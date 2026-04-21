#!/usr/bin/env python3
"""
Shared alliance memory-scan logic for CLI and GUI (Windows only).
"""

from __future__ import annotations

import ctypes
import re
import struct
import time
from ctypes import wintypes
from pathlib import Path
import threading
from typing import Any, Callable

import psutil


def find_process(name_pattern: str) -> psutil.Process | None:
    needle = name_pattern.lower()
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info.get("name") or ""
            if needle in name.lower():
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def open_game_handle(pid: int) -> tuple[Any, Any] | None:
    kernel32 = ctypes.windll.kernel32
    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400
    h = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not h:
        return None
    return h, kernel32


def close_handle(kernel32: Any, h_process: Any) -> None:
    if h_process:
        kernel32.CloseHandle(h_process)


def quick_scan(h_process: Any, kernel32: Any) -> dict[str, dict[str, Any]]:
    class MEMORY_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_void_p),
            ("AllocationBase", ctypes.c_void_p),
            ("AllocationProtect", wintypes.DWORD),
            ("RegionSize", ctypes.c_size_t),
            ("State", wintypes.DWORD),
            ("Protect", wintypes.DWORD),
            ("Type", wintypes.DWORD),
        ]

    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    max_address = 0x7FFFFFFF0000

    MEM_COMMIT = 0x1000
    PAGE_READWRITE = 0x04

    found_data: dict[str, dict[str, Any]] = {}

    pattern = rb'([A-Z][A-Za-z0-9]{1,6})\s+([0-9a-f]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{3,40}?)\d?[\x00-\x08\x0b-\x1f]?'

    while address < max_address:
        if kernel32.VirtualQueryEx(
            h_process, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)
        ) == 0:
            address += 0x10000
            continue

        if mbi.State == MEM_COMMIT and mbi.Protect == PAGE_READWRITE:
            scan_size = min(mbi.RegionSize, 2 * 1024 * 1024)
            buffer = (ctypes.c_char * scan_size)()
            bytes_read = ctypes.c_size_t()

            if kernel32.ReadProcessMemory(
                h_process,
                ctypes.c_void_p(address),
                buffer,
                scan_size,
                ctypes.byref(bytes_read),
            ):
                data = bytes(buffer[: bytes_read.value])
                matches = re.findall(pattern, data)

                for abbr, alliance_id, full_name in matches:
                    try:
                        abbr_str = abbr.decode("utf-8", errors="ignore").strip()
                        alliance_id_str = alliance_id.decode("utf-8")
                        full_name_str = full_name.decode("utf-8", errors="ignore").strip()
                        full_name_str = "".join(
                            c for c in full_name_str if c.isprintable() or c.isspace()
                        )
                        full_name_str = " ".join(full_name_str.split())

                        if 3 < len(full_name_str) < 50 and len(abbr_str) <= 10:
                            abbr_idx = data.find(abbr)
                            rank = None
                            power = None

                            if abbr_idx != -1:
                                check_start = max(0, abbr_idx - 100)
                                check_end = min(len(data), abbr_idx + 200)
                                check_region = data[check_start:check_end]

                                for r in range(1, 51):
                                    if struct.pack("<I", r) in check_region:
                                        rank = r
                                        break

                                for i in range(0, len(check_region) - 8, 4):
                                    val = struct.unpack("<Q", check_region[i : i + 8])[0]
                                    if 1_000_000_000 <= val <= 10_000_000_000:
                                        power = val
                                        break

                            found_data[alliance_id_str] = {
                                "abbr": abbr_str,
                                "name": full_name_str,
                                "id": alliance_id_str,
                                "rank": rank,
                                "power": power,
                            }
                    except (UnicodeDecodeError, struct.error, IndexError):
                        continue

        address += mbi.RegionSize

    return found_data


def merge_alliances(
    all_alliances: dict[str, dict[str, Any]], new_data: dict[str, dict[str, Any]]
) -> None:
    for aid, info in new_data.items():
        if aid not in all_alliances:
            all_alliances[aid] = info
        else:
            if info["rank"] and not all_alliances[aid]["rank"]:
                all_alliances[aid]["rank"] = info["rank"]
            if info["power"] and not all_alliances[aid]["power"]:
                all_alliances[aid]["power"] = info["power"]


def write_alliance_csv(output_file: Path, all_alliances: dict[str, dict[str, Any]]) -> None:
    alliances_list = list(all_alliances.values())
    alliances_with_rank = [a for a in alliances_list if a["rank"]]
    alliances_without_rank = [a for a in alliances_list if not a["rank"]]
    alliances_with_rank.sort(key=lambda x: x["rank"])

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Rank,Short Name,Full Name,Power,Alliance ID\n")
        for a in alliances_with_rank:
            rank = a["rank"] if a["rank"] else ""
            power = a["power"] if a["power"] else ""
            f.write(f'{rank},"{a["abbr"]}","{a["name"]}",{power},"{a["id"]}"\n')
        if alliances_without_rank:
            f.write("\n# Without rank data:\n")
            for a in alliances_without_rank:
                power = a["power"] if a["power"] else ""
                f.write(f',"{a["abbr"]}","{a["name"]}",{power},"{a["id"]}"\n')


def default_csv_path() -> Path:
    return Path("live_alliance_data.csv")


def run_monitor_loop(
    proc: psutil.Process,
    h_process: Any,
    kernel32: Any,
    all_alliances: dict[str, dict[str, Any]],
    scan_interval_sec: float,
    should_stop: Callable[[], bool],
    on_scan_complete: Callable[[int, int], None] | None = None,
    alliances_lock: threading.Lock | None = None,
) -> None:
    scan_count = 0
    while not should_stop():
        try:
            if not proc.is_running():
                break
        except psutil.NoSuchProcess:
            break

        scan_count += 1
        new_data = quick_scan(h_process, kernel32)
        if alliances_lock:
            with alliances_lock:
                merge_alliances(all_alliances, new_data)
                total = len(all_alliances)
        else:
            merge_alliances(all_alliances, new_data)
            total = len(all_alliances)
        if on_scan_complete:
            on_scan_complete(scan_count, total)
        time.sleep(scan_interval_sec)
