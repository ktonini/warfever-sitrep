#!/usr/bin/env python3
"""
Shared alliance memory-scan logic for CLI and GUI (Windows only).
"""

from __future__ import annotations

import ctypes
import os
import re
import struct
import time
from ctypes import wintypes
from pathlib import Path
import threading
from typing import Any, Callable

import psutil

from lw_debug_log import flush_monitor_log, get_logger

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
    """Committed pages that may hold UI strings (heap, mapped file, IL2CPP .rdata)."""
    base = _base_page_protect(protect)
    allowed = {
        0x02,  # PAGE_READONLY
        0x04,  # PAGE_READWRITE
        0x08,  # PAGE_WRITECOPY
    }
    # Unity/IL2CPP literals often live in PAGE_EXECUTE_READ; skip to speed scans: LW_SCAN_SKIP_EXECREAD=1
    if os.environ.get("LW_SCAN_SKIP_EXECREAD", "").strip() not in ("1", "true", "yes"):
        allowed.add(0x20)  # PAGE_EXECUTE_READ
    if os.environ.get("LW_SCAN_RWX", "").strip() in ("1", "true", "yes"):
        allowed.update(
            {
                0x40,  # PAGE_EXECUTE_READWRITE
                0x80,  # PAGE_EXECUTE_WRITECOPY
            }
        )
    return base in allowed


def _rpm_read_chunk(
    kernel32: Any, h_process: Any, read_addr: int, read_len: int
) -> tuple[bytes, bool]:
    """
    Read up to read_len bytes. Returns (data, used_paged_fallback).

    On failure, ReadProcessMemory can still set NumberOfBytesRead (e.g. ERROR_PARTIAL_COPY
    299) — we must use those bytes, then read the remainder in smaller steps.
    """
    if read_len <= 0:
        return b"", False
    buf = (ctypes.c_char * read_len)()
    br = ctypes.c_size_t(0)
    ok = bool(
        kernel32.ReadProcessMemory(
            h_process,
            ctypes.c_void_p(read_addr),
            buf,
            read_len,
            ctypes.byref(br),
        )
    )
    got0 = int(br.value)
    if ok and got0 == read_len:
        return bytes(memoryview(buf)[:read_len]), False

    out = bytearray()
    if got0 > 0:
        out.extend(memoryview(buf)[:got0])

    # First call did not return the full buffer; finish with page-sized reads.
    used_fallback = not (ok and got0 == read_len)
    page = 4096
    pos = got0
    while pos < read_len:
        chunk = min(page, read_len - pos)
        b2 = (ctypes.c_char * chunk)()
        br2 = ctypes.c_size_t(0)
        kernel32.ReadProcessMemory(
            h_process,
            ctypes.c_void_p(read_addr + pos),
            b2,
            chunk,
            ctypes.byref(br2),
        )
        got = int(br2.value)
        if got > 0:
            out.extend(memoryview(b2)[:got])
            pos += got
        else:
            pos += chunk

    return bytes(out), used_fallback


def quick_scan(
    h_process: Any,
    kernel32: Any,
    should_stop: Callable[[], bool] | None = None,
) -> dict[str, dict[str, Any]]:
    t0 = time.perf_counter()
    last_progress_log = t0

    def _abort_requested() -> bool:
        return should_stop is not None and should_stop()

    aborted = False
    _log.info(
        "quick_scan started (full address walk; often several minutes — "
        "progress every ~15s; set LW_SCAN_SKIP_EXECREAD=1 for faster scans)"
    )
    flush_monitor_log()

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
        rb".{0,3}([A-Z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{2,62}?)\d?[\x00-\x08\x0b-\x1f]?",
        rb".{0,3}([A-Z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^8\x00]{2,62}?)8",
        rb"([A-Z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{2,62}?)\d?[\x00-\x08\x0b-\x1f]?",
        rb".{0,3}([A-Za-z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{2,62}?)\d?[\x00-\x08\x0b-\x1f]?",
    )

    # Unity / IL2CPP often stores UI strings as UTF-16LE; same logical layout as ASCII patterns.
    ALLIANCE_PATTERNS_U = (
        r".{0,3}([A-Z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{2,62}?)\d?[\x00-\x08\x0b-\x1f]?",
        r".{0,3}([A-Z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^8\x00]{2,62}?)8",
        r"([A-Z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{2,62}?)\d?[\x00-\x08\x0b-\x1f]?",
        r".{0,3}([A-Za-z][A-Za-z0-9]{1,10})\s+([0-9a-fA-F]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{2,62}?)\d?[\x00-\x08\x0b-\x1f]?",
    )

    def _likely_utf16le_text_blob(blob: bytes) -> bool:
        """Cheap check for UTF-16LE Latin runs (Unity/C# string heaps)."""
        if len(blob) < 64:
            return False
        n = min(len(blob) & ~1, 768)
        hits = 0
        for i in range(0, n, 2):
            lo, hi = blob[i], blob[i + 1]
            if hi == 0 and 32 <= lo <= 126:
                hits += 1
        return hits >= 8

    chunk_max = 2 * 1024 * 1024
    chunk_overlap = 16384

    vq_ok = 0
    vq_fail = 0
    readable_regions = 0
    chunks_read = 0
    rpm_ok = 0
    rpm_fail = 0
    rpm_chunks_empty = 0
    rpm_paged_recoveries = 0
    bytes_scanned = 0
    raw_byte_hits = 0
    utf16_raw_hits = 0

    # Optional: set LW_DEBUG_FIND=YourTag to count chunks containing that UTF-8 / UTF-16-LE needle
    debug_find = os.environ.get("LW_DEBUG_FIND", "").strip()[:48]
    debug_find_chunks = 0
    debug_find_utf16_chunks = 0
    debug_find_b = debug_find.encode("utf-8", errors="ignore") if debug_find else b""
    debug_find_u16 = debug_find.encode("utf-16-le", errors="ignore") if debug_find else b""

    def _store_row(
        blob: bytes,
        anchor: bytes,
        abbr_str: str,
        alliance_id_str: str,
        full_name_str: str,
    ) -> None:
        if not (2 < len(full_name_str) < 64 and len(abbr_str) <= 12):
            return
        alliance_id_str = alliance_id_str.lower()
        if len(alliance_id_str) != 32 or not re.fullmatch(r"[0-9a-f]+", alliance_id_str):
            return
        abbr_idx = blob.find(anchor)
        rank = None
        power = None
        if abbr_idx != -1:
            check_start = max(0, abbr_idx - 100)
            check_end = min(len(blob), abbr_idx + 200)
            check_region = blob[check_start:check_end]
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

    def scan_buffer(data: bytes) -> None:
        nonlocal raw_byte_hits
        for pat in ALLIANCE_PATTERNS:
            matches = re.findall(pat, data)
            raw_byte_hits += len(matches)
            for abbr, alliance_id, full_name in matches:
                try:
                    abbr_str = abbr.decode("utf-8", errors="ignore").strip()
                    alliance_id_str = alliance_id.decode("utf-8")
                    full_name_str = full_name.decode("utf-8", errors="ignore").strip()
                    full_name_str = "".join(
                        c for c in full_name_str if c.isprintable() or c.isspace()
                    )
                    full_name_str = " ".join(full_name_str.split())
                    _store_row(data, abbr, abbr_str, alliance_id_str, full_name_str)
                except (UnicodeDecodeError, struct.error, IndexError, TypeError):
                    continue

    def scan_buffer_utf16(data: bytes) -> None:
        nonlocal utf16_raw_hits
        if len(data) < 64:
            return
        u = data.decode("utf-16-le", errors="ignore")
        if len(u) < 40:
            return
        for pat in ALLIANCE_PATTERNS_U:
            matches = re.findall(pat, u)
            if not matches:
                continue
            utf16_raw_hits += len(matches)
            for abbr_str, alliance_id_str, full_name_str in matches:
                try:
                    full_name_str = "".join(
                        c for c in full_name_str if c.isprintable() or c.isspace()
                    )
                    full_name_str = " ".join(full_name_str.split())
                    abbr_str = abbr_str.strip()
                    alliance_id_str = alliance_id_str.strip()
                    anchor = abbr_str.encode("utf-16-le")
                    _store_row(data, anchor, abbr_str, alliance_id_str, full_name_str)
                except (UnicodeDecodeError, struct.error, IndexError, TypeError):
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
        now = time.perf_counter()
        if now - last_progress_log >= 15.0:
            last_progress_log = now
            scanned_so_far = bytes_scanned / (1024 * 1024)
            _log.info(
                "quick_scan progress: %.0fs elapsed vq=%s readable_regions=%s chunks=%s "
                "MiB_scanned=%.1f ascii_hits=%s utf16_hits=%s accepted=%s",
                now - t0,
                vq_ok,
                readable_regions,
                chunks_read,
                scanned_so_far,
                raw_byte_hits,
                utf16_raw_hits,
                len(found_data),
            )
            flush_monitor_log()

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
                read_addr = region_base + offset
                chunks_read += 1

                data, used_paged = _rpm_read_chunk(kernel32, h_process, read_addr, read_len)
                if data:
                    rpm_ok += 1
                    bytes_scanned += len(data)
                    if used_paged:
                        rpm_paged_recoveries += 1
                    if debug_find and debug_find_b in data:
                        debug_find_chunks += 1
                    if debug_find and debug_find_u16 in data:
                        debug_find_utf16_chunks += 1
                    scan_buffer(data)
                    if _likely_utf16le_text_blob(data):
                        scan_buffer_utf16(data)
                else:
                    rpm_fail += 1
                    rpm_chunks_empty += 1

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
    pattern_hits = raw_byte_hits + utf16_raw_hits
    scanned_mib = bytes_scanned / (1024 * 1024)
    _log.info(
        "quick_scan %sin %.2fs: VirtualQuery ok=%s fail=%s readable_regions=%s "
        "chunks=%s bytes_scanned_mib=%.1f rpm_ok=%s rpm_fail=%s rpm_empty_chunks=%s "
        "rpm_paged_recover=%s raw_ascii_hits=%s utf16_hits=%s accepted_alliances=%s",
        "aborted " if aborted else "done ",
        elapsed,
        vq_ok,
        vq_fail,
        readable_regions,
        chunks_read,
        scanned_mib,
        rpm_ok,
        rpm_fail,
        rpm_chunks_empty,
        rpm_paged_recoveries,
        raw_byte_hits,
        utf16_raw_hits,
        accepted,
    )
    flush_monitor_log()
    if debug_find:
        _log.info(
            "LW_DEBUG_FIND=%r: chunks_with_utf8_needle=%s chunks_with_utf16le_needle=%s "
            "(set tag while rankings list is on screen; 0 means string not in scanned memory)",
            debug_find,
            debug_find_chunks,
            debug_find_utf16_chunks,
        )
        flush_monitor_log()
    if accepted == 0 and pattern_hits == 0:
        _log.warning(
            "No regex matches (ASCII or UTF-16). Causes may include rankings closed, new wire "
            "format, or GPU-only text. Scanned ~%.1f MiB this pass. "
            "Tuning: LW_SCAN_SKIP_EXECREAD=1 skips PAGE_EXECUTE_READ (faster). "
            "LW_SCAN_RWX=1 also scans RWX (much slower). "
            "Debug: set env LW_DEBUG_FIND=YourAllianceTag while the tag is visible on screen.",
            scanned_mib,
        )
    elif accepted == 0 and pattern_hits > 0:
        _log.warning(
            "Had %s pattern hits (ascii=%s utf16=%s) but 0 accepted rows (filters may be too strict).",
            pattern_hits,
            raw_byte_hits,
            utf16_raw_hits,
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
