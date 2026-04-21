#!/usr/bin/env python3
"""
Desktop UI for the live alliance memory monitor (Windows).
Run: python lw_monitor_gui.py
Build: see scripts/build_windows_gui.ps1
"""

from __future__ import annotations

import os
import sys


def _clear_stale_tcl_tk_env() -> None:
    """Drop TCL_LIBRARY/TK_LIBRARY that point at dead paths (common after PyInstaller runs)."""
    for key in ("TCL_LIBRARY", "TK_LIBRARY"):
        path = os.environ.get(key)
        if not path:
            continue
        normalized = path.replace("/", os.sep)
        if "_MEI" in normalized or not os.path.isdir(normalized):
            del os.environ[key]


_clear_stale_tcl_tk_env()

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

if sys.platform != "win32":
    print("This tool requires Windows (ReadProcessMemory).")
    sys.exit(1)

from lw_alliance_monitor_core import (
    close_handle,
    default_csv_path,
    find_process,
    merge_alliances,
    open_game_handle,
    quick_scan,
    run_monitor_loop,
    write_alliance_csv,
)


def application_base_dir() -> Path:
    if getattr(sys, "frozen", False) and sys.executable:
        return Path(sys.executable).resolve().parent
    return Path.cwd()


class AllianceMonitorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Last War — Alliance Memory Monitor")
        self.minsize(880, 520)
        self.geometry("960x600")

        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._alliances: dict[str, dict[str, Any]] = {}
        self._alliances_lock = threading.Lock()
        self._h_process: Any = None
        self._kernel32: Any = None
        self._proc = None
        self._output_path = application_base_dir() / default_csv_path().name
        self._shutting_down = False
        self._finalize_after_id: str | None = None
        self._finalize_lock = threading.Lock()
        self._finalize_done = False

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Output CSV:").pack(side=tk.LEFT)
        self._path_var = tk.StringVar(value=str(self._output_path))
        path_entry = ttk.Entry(top, textvariable=self._path_var, width=72)
        path_entry.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

        ttk.Button(top, text="Browse…", command=self._browse_output).pack(side=tk.LEFT)

        ctrl = ttk.Frame(self, padding=(8, 0, 8, 8))
        ctrl.pack(fill=tk.X)

        self._start_btn = ttk.Button(ctrl, text="Start monitoring", command=self._on_start)
        self._start_btn.pack(side=tk.LEFT)

        self._stop_btn = ttk.Button(
            ctrl, text="Stop & save CSV", command=self._on_stop, state=tk.DISABLED
        )
        self._stop_btn.pack(side=tk.LEFT, padx=(8, 0))

        self._scan_once_btn = ttk.Button(ctrl, text="Scan once", command=self._on_scan_once)
        self._scan_once_btn.pack(side=tk.LEFT, padx=(16, 0))

        self._status_var = tk.StringVar(value="Idle. Launch the game, open alliance rankings, then Start.")
        ttk.Label(ctrl, textvariable=self._status_var).pack(side=tk.LEFT, padx=(24, 0))

        table_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("rank", "abbr", "name", "power", "aid")
        self._tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode=tk.BROWSE,
        )
        self._tree.heading("rank", text="Rank")
        self._tree.heading("abbr", text="Short")
        self._tree.heading("name", text="Full name")
        self._tree.heading("power", text="Power")
        self._tree.heading("aid", text="Alliance ID")

        self._tree.column("rank", width=50, anchor=tk.CENTER)
        self._tree.column("abbr", width=90, anchor=tk.W)
        self._tree.column("name", width=220, anchor=tk.W)
        self._tree.column("power", width=120, anchor=tk.E)
        self._tree.column("aid", width=280, anchor=tk.W)

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_y.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self._poll_ui()

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save CSV as",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
            initialfile=Path(self._path_var.get()).name,
        )
        if path:
            self._path_var.set(path)

    def _set_running_ui(self, running: bool) -> None:
        self._start_btn.configure(state=tk.DISABLED if running else tk.NORMAL)
        self._stop_btn.configure(state=tk.NORMAL if running else tk.DISABLED)
        self._scan_once_btn.configure(state=tk.DISABLED if running else tk.NORMAL)

    def _on_start(self) -> None:
        self._output_path = Path(self._path_var.get()).expanduser()
        game_proc = find_process("LastWar")
        if not game_proc:
            messagebox.showerror(
                "Game not found",
                "Could not find a process whose name contains “LastWar”.\n"
                "Start the game and open the alliance rankings window.",
            )
            return

        opened = open_game_handle(game_proc.pid)
        if not opened:
            messagebox.showerror(
                "Access denied",
                "Could not open the game process for reading.\n"
                "Try running this app as Administrator.",
            )
            return

        self._h_process, self._kernel32 = opened
        self._proc = game_proc
        self._stop_event.clear()
        with self._finalize_lock:
            self._finalize_done = False

        with self._alliances_lock:
            self._alliances.clear()

        self._set_running_ui(True)
        self._status_var.set(
            f"Monitoring {game_proc.name()} (PID {game_proc.pid}). "
            "First full memory pass can take several minutes; then the scan # will increase. "
            "Keep the rankings list open and scroll slowly."
        )

        def worker() -> None:
            try:
                assert self._proc is not None and self._h_process is not None and self._kernel32

                def should_stop() -> bool:
                    return self._stop_event.is_set()

                def on_scan(scan_n: int, count: int) -> None:
                    self.after(0, lambda: self._status_var.set(
                        f"Scan #{scan_n} — {count} unique alliances (stop when done)"
                    ))

                run_monitor_loop(
                    self._proc,
                    self._h_process,
                    self._kernel32,
                    self._alliances,
                    scan_interval_sec=2.0,
                    should_stop=should_stop,
                    on_scan_complete=on_scan,
                    alliances_lock=self._alliances_lock,
                )
            finally:
                if self._kernel32 and self._h_process:
                    close_handle(self._kernel32, self._h_process)
                self._h_process = None
                self._kernel32 = None
                self._finalize_after_id = self.after(0, self._finalize_worker)

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _finalize_worker(self) -> None:
        with self._finalize_lock:
            if self._finalize_done:
                return
            self._finalize_done = True
        self._finalize_after_id = None
        self._worker = None
        self._set_running_ui(False)
        self._refresh_table()
        confirm = self._stop_event.is_set() and not self._shutting_down
        self._save_csv(show_confirm=confirm)

    def _on_stop(self) -> None:
        self._stop_event.set()
        self._status_var.set("Stopping…")

    def _on_scan_once(self) -> None:
        self._output_path = Path(self._path_var.get()).expanduser()
        game_proc = find_process("LastWar")
        if not game_proc:
            messagebox.showerror("Game not found", "Start the game first.")
            return
        opened = open_game_handle(game_proc.pid)
        if not opened:
            messagebox.showerror("Access denied", "Could not open the process. Try Run as administrator.")
            return
        h, k32 = opened
        self._status_var.set("Scanning memory once…")
        self.update_idletasks()
        try:
            new_data = quick_scan(h, k32)
            with self._alliances_lock:
                merge_alliances(self._alliances, new_data)
        finally:
            close_handle(k32, h)
        self._refresh_table()
        self._status_var.set(f"Single scan done — {len(self._alliances)} unique alliances in table.")

    def _save_csv(self, show_confirm: bool) -> None:
        self._output_path = Path(self._path_var.get()).expanduser()
        with self._alliances_lock:
            snapshot = dict(self._alliances)
        if not snapshot:
            if show_confirm:
                messagebox.showinfo("No data", "No alliances captured yet.")
            self._status_var.set("Idle.")
            return
        try:
            write_alliance_csv(self._output_path, snapshot)
        except OSError as e:
            messagebox.showerror("Save failed", str(e))
            return
        self._status_var.set(f"Saved {len(snapshot)} rows to {self._output_path}")
        if show_confirm and not self._shutting_down:
            messagebox.showinfo("Saved", f"Wrote CSV:\n{self._output_path}")

    def _refresh_table(self) -> None:
        with self._alliances_lock:
            rows = list(self._alliances.values())
        ranked = [r for r in rows if r.get("rank")]
        unranked = [r for r in rows if not r.get("rank")]
        ranked.sort(key=lambda x: x["rank"])

        self._tree.delete(*self._tree.get_children())
        for a in ranked:
            power = f"{a['power']:,}" if a.get("power") else ""
            self._tree.insert(
                "",
                tk.END,
                values=(a.get("rank", ""), a.get("abbr", ""), a.get("name", ""), power, a.get("id", "")),
            )
        for a in unranked:
            power = f"{a['power']:,}" if a.get("power") else ""
            self._tree.insert(
                "",
                tk.END,
                values=("", a.get("abbr", ""), a.get("name", ""), power, a.get("id", "")),
            )

    def _poll_ui(self) -> None:
        if self._worker and self._worker.is_alive():
            self._refresh_table()
        self.after(800, self._poll_ui)

    def destroy(self) -> None:
        self._shutting_down = True
        self._stop_event.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=12.0)
        if self._finalize_after_id is not None:
            try:
                self.after_cancel(self._finalize_after_id)
            except tk.TclError:
                pass
            self._finalize_after_id = None
        self._finalize_worker()
        super().destroy()


def main() -> None:
    try:
        app = AllianceMonitorApp()
    except tk.TclError as e:
        err = str(e).lower()
        if "init.tcl" in err:
            print(
                "Tkinter could not load Tcl/Tk.\n\n"
                "If TCL_LIBRARY or TK_LIBRARY is set (often after running a PyInstaller .exe), "
                "clear them for this shell, then retry:\n"
                "  set TCL_LIBRARY=\n"
                "  set TK_LIBRARY=\n\n"
                "If it still fails, use the full installer from https://www.python.org/downloads/ "
                "(Windows Store / embed builds sometimes omit Tk).\n",
                file=sys.stderr,
            )
            sys.exit(1)
        raise
    app.mainloop()


if __name__ == "__main__":
    main()
