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

from lw_debug_log import get_logger

_log = get_logger()


def find_process(name_pattern: str) -> psutil.Process | None:
    """Pick the main game process if several names match (e.g. launcher vs client)."""
    needle = name_pattern.lower()
    candidates: list[psutil.Process] = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info.get("name") or ""
            if needle in name.lower():
                candidates.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if not candidates:
        _log.info("find_process(%r): no matching processes", name_pattern)
        return None
    for p in candidates:
        try:
            _log.debug(
                "find_process candidate pid=%s name=%r exe=%r",
                p.pid,
                p.name(),
                p.exe(),
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            _log.debug("find_process candidate pid=%s (exe unavailable: %s)", p.pid, e)
    if len(candidates) == 1:
        chosen = candidates[0]
        _log.info(
            "find_process: using pid=%s name=%r",
            chosen.pid,
            chosen.name(),
        )
        return chosen

    def score(proc: psutil.Process) -> int:
        try:
            exe = (proc.exe() or "").lower()
            rss = int(proc.memory_info().rss)
            if "launcher" in exe or "updater" in exe:
                rss -= 10**12
            if exe.endswith("lastwar.exe") and "launcher" not in exe:
                rss += 10**12
            return rss
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            return 0

    chosen = max(candidates, key=score)
    try:
        exe = chosen.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        exe = "?"
    _log.info(
        "find_process: chose pid=%s name=%r exe=%r (from %d candidates)",
        chosen.pid,
        chosen.name(),
        exe,
        len(candidates),
    )
    return chosen


def open_game_handle(pid: int) -> tuple[Any, Any] | None:
    kernel32 = ctypes.windll.kernel32
    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400
    h = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not h:
        err = kernel32.GetLastError()
        _log.error("OpenProcess failed pid=%s GetLastError=%s", pid, err)
        return None
    _log.info("OpenProcess ok pid=%s handle=%s", pid, h)
    return h, kernel32


def close_handle(kernel32: Any, h_process: Any) -> None:
    if h_process:
        kernel32.CloseHandle(h_process)


def _base_page_protect(protect: int) -> int:
    """Lower byte of protection (ignore PAGE_GUARD / PAGE_NOCACHE / etc.)."""
    return int(protect) & 0xFF


def _is_readable_committed_region(protect: int) -> bool:
    """Committed pages that may hold UI strings (match comprehensive scanner, + writecopy)."""
    base = _base_page_protect(protect)
    return base in (
        0x02,  # PAGE_READONLY
        0x04,  # PAGE_READWRITE
        0x08,  # PAGE_WRITECOPY
    )


def quick_scan(
    h_process: Any,
    kernel32: Any,
    should_stop: Callable[[], bool] | None = None,
) -> dict[str, dict[str, Any]]:
    t0 = time.perf_counter()

    def _abort_requested() -> bool:
        return should_stop is not None and should_stop()

    aborted = False
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

    found_data: dict[str, dict[str, Any]] = {}

    # In-memory rows often look like: GMUvvU 37ecf329... 2veni vidi vici8
    # (0–3 prefix bytes before tag; name may end with control or trailing '8').
    ALLIANCE_PATTERNS = (
        rb".{0,3}([A-Z][A-Za-z0-9]{1,6})\s+([0-9a-f]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{3,40}?)\d?[\x00-\x08\x0b-\x1f]?",
        rb".{0,3}([A-Z][A-Za-z0-9]{1,6})\s+([0-9a-f]{32})\s+\d([^8\x00]{3,50}?)8",
        rb"([A-Z][A-Za-z0-9]{1,6})\s+([0-9a-f]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{3,40}?)\d?[\x00-\x08\x0b-\x1f]?",
    )

    chunk_max = 2 * 1024 * 1024
    chunk_overlap = 16384

    vq_ok = 0
    vq_fail = 0
    readable_regions = 0
    chunks_read = 0
    rpm_ok = 0
    rpm_fail = 0
    raw_pattern_hits = 0

    def scan_buffer(data: bytes) -> None:
        nonlocal raw_pattern_hits
        for pat in ALLIANCE_PATTERNS:
            matches = re.findall(pat, data)
            raw_pattern_hits += len(matches)
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

    while address < max_address:
        if _abort_requested():
            aborted = True
            break

        if kernel32.VirtualQueryEx(
            h_process, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)
        ) == 0:
            vq_fail += 1
            address += 0x10000
            continue

        vq_ok += 1
        region_base = int(ctypes.cast(mbi.BaseAddress, ctypes.c_void_p).value or 0)
        region_size = int(mbi.RegionSize)

        if mbi.State == MEM_COMMIT and _is_readable_committed_region(mbi.Protect):
            readable_regions += 1
            offset = 0
            while offset < region_size:
                if _abort_requested():
                    aborted = True
                    break
                read_len = min(chunk_max, region_size - offset)
                buffer = (ctypes.c_char * read_len)()
                bytes_read = ctypes.c_size_t()
                read_addr = region_base + offset
                chunks_read += 1

                if kernel32.ReadProcessMemory(
                    h_process,
                    ctypes.c_void_p(read_addr),
                    buffer,
                    read_len,
                    ctypes.byref(bytes_read),
                ):
                    rpm_ok += 1
                    data = bytes(buffer[: bytes_read.value])
                    scan_buffer(data)
                else:
                    rpm_fail += 1
                    if rpm_fail <= 8:
                        err = kernel32.GetLastError()
                        _log.debug(
                            "ReadProcessMemory fail addr=0x%x len=%s err=%s",
                            read_addr,
                            read_len,
                            err,
                        )

                if read_len < chunk_max:
                    offset += read_len
                else:
                    offset += chunk_max - chunk_overlap

            if aborted:
                break

        next_address = region_base + region_size
        if next_address <= address:
            next_address = address + 0x1000
        address = next_address

    elapsed = time.perf_counter() - t0
    accepted = len(found_data)
    _log.info(
        "quick_scan %sin %.2fs: VirtualQuery ok=%s fail=%s readable_regions=%s "
        "chunks=%s rpm_ok=%s rpm_fail=%s raw_regex_hits=%s accepted_alliances=%s",
        "aborted " if aborted else "done ",
        elapsed,
        vq_ok,
        vq_fail,
        readable_regions,
        chunks_read,
        rpm_ok,
        rpm_fail,
        raw_pattern_hits,
        accepted,
    )
    if accepted == 0 and raw_pattern_hits == 0:
        _log.warning(
            "No regex matches for alliance pattern — rankings data may be encoded differently "
            "or this may not be the game process."
        )
    elif accepted == 0 and raw_pattern_hits > 0:
        _log.warning(
            "Had %s raw regex hits but 0 accepted rows (filters may be too strict).",
            raw_pattern_hits,
        )

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
                _log.warning("Process pid=%s no longer running; stopping monitor loop.", proc.pid)
                break
        except psutil.NoSuchProcess:
            _log.warning("Process disappeared; stopping monitor loop.")
            break

        scan_count += 1
        _log.debug("monitor loop scan #%s starting", scan_count)
        new_data = quick_scan(h_process, kernel32, should_stop)
        if alliances_lock:
            with alliances_lock:
                merge_alliances(all_alliances, new_data)
                total = len(all_alliances)
        else:
            merge_alliances(all_alliances, new_data)
            total = len(all_alliances)
        if on_scan_complete:
            on_scan_complete(scan_count, total)
        if should_stop():
            break
        time.sleep(scan_interval_sec)
