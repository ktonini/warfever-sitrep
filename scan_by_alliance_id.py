#!/usr/bin/env python3
"""
Scan for alliance data using their unique ID hash
"""

import psutil
import ctypes
from ctypes import wintypes
import struct
import binascii

def find_process(name_pattern):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name_pattern.lower() in proc.info['name'].lower():
                return proc
        except:
            pass
    return None

# Known alliances with their IDs from memory dump
KNOWN_ALLIANCES = {
    '37ecf329739c4b61bf9da597829fa993': {'abbr': 'UvvU', 'name': 'veni vidi vici', 'power': 6435764372},
    '40bdeadf9a184d7da54c7dc4a07feeac': {'abbr': 'ORCE', 'name': 'Omega Force', 'power': 6387057595},
    '918453bfc5e94524b3cce4c29806844b': {'abbr': 'NKOT', 'name': 'korea one team', 'power': None},
}

def scan_for_alliance_ids(proc):
    """Scan for alliance IDs and associated data"""
    kernel32 = ctypes.windll.kernel32

    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400

    h_process = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
        False,
        proc.pid
    )

    if not h_process:
        print("[!] Failed to open process")
        return {}

    print(f"[+] Scanning for alliance IDs...\n")

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

    results = {}
    regions_scanned = 0

    for alliance_id_hex, info in KNOWN_ALLIANCES.items():
        # Convert hex ID to binary
        alliance_id_bytes = binascii.unhexlify(alliance_id_hex)

        print(f"Searching for: {info['abbr']} (ID: {alliance_id_hex[:16]}...)")

        address = 0
        found_count = 0

        while address < max_address and found_count < 5:  # Limit to first 5 occurrences
            if kernel32.VirtualQueryEx(h_process, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
                address += 0x10000
                continue

            if mbi.State == MEM_COMMIT and mbi.Protect == PAGE_READWRITE:
                scan_size = min(mbi.RegionSize, 5 * 1024 * 1024)
                buffer = (ctypes.c_char * scan_size)()
                bytes_read = ctypes.c_size_t()

                if kernel32.ReadProcessMemory(h_process, ctypes.c_void_p(address), buffer, scan_size, ctypes.byref(bytes_read)):
                    data = bytes(buffer[:bytes_read.value])

                    # Search for this alliance ID
                    idx = data.find(alliance_id_bytes)
                    if idx != -1:
                        found_count += 1
                        mem_addr = address + idx

                        print(f"  Found at: 0x{mem_addr:016x}")

                        # Look around this ID for power numbers and other data
                        context_start = max(0, idx - 200)
                        context_end = min(len(data), idx + 200)
                        context = data[context_start:context_end]

                        # Look for power numbers nearby
                        power_found = []
                        for i in range(0, len(context) - 8, 4):
                            try:
                                # Try uint64
                                val = struct.unpack('<Q', context[i:i+8])[0]
                                if 5_000_000_000 <= val <= 10_000_000_000:
                                    offset_from_id = (context_start + i) - idx
                                    power_found.append((offset_from_id, val))
                            except:
                                pass

                        if power_found:
                            print(f"    Power numbers found nearby:")
                            for offset, power in power_found[:3]:  # Show first 3
                                print(f"      Offset {offset:+4d}: {power:,}")

                        # Look for the abbreviation
                        abbr_bytes = info['abbr'].encode('utf-8')
                        abbr_idx = context.find(abbr_bytes)
                        if abbr_idx != -1:
                            abbr_offset = (context_start + abbr_idx) - idx
                            print(f"    Abbreviation '{info['abbr']}' at offset {abbr_offset:+4d}")

                        # Look for rank number (1-50)
                        for rank in range(1, 51):
                            rank_bytes = struct.pack('<I', rank)
                            rank_idx = context.find(rank_bytes)
                            if rank_idx != -1:
                                rank_offset = (context_start + rank_idx) - idx
                                print(f"    Rank {rank} at offset {rank_offset:+4d}")
                                break

                        print()

                        if alliance_id_hex not in results:
                            results[alliance_id_hex] = []
                        results[alliance_id_hex].append({
                            'address': mem_addr,
                            'power_numbers': power_found
                        })

            regions_scanned += 1
            if regions_scanned % 200 == 0:
                print(f"    (Scanned {regions_scanned} regions...)")

            address += mbi.RegionSize

        print(f"  Total found: {found_count}\n")

    kernel32.CloseHandle(h_process)
    return results

print("Alliance ID-Based Scanner")
print("=" * 60)

game_proc = find_process("LastWar")
if not game_proc:
    print("[!] Game not running")
    exit(1)

try:
    results = scan_for_alliance_ids(game_proc)

    print(f"\n[+] Scan complete!")
    print(f"[+] Found {sum(len(v) for v in results.values())} total occurrences")

except PermissionError:
    print("[!] Access denied. Run as Administrator")
except Exception as e:
    print(f"[!] Error: {e}")
    import traceback
    traceback.print_exc()
