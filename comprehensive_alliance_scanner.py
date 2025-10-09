#!/usr/bin/env python3
"""
Comprehensive alliance data extractor from game memory
Extracts: Rank, Short Name, Full Name, Alliance ID, Power
"""

import psutil
import ctypes
from ctypes import wintypes
import struct
import re
from pathlib import Path

output_file = Path("alliances_extracted_from_memory.csv")

def find_process(name_pattern):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name_pattern.lower() in proc.info['name'].lower():
                return proc
        except:
            pass
    return None

def scan_memory(proc):
    """Scan game memory for alliance data"""
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
        return []

    print(f"[+] Scanning memory: {proc.info['name']} (PID: {proc.pid})")
    print(f"[*] Looking for alliance data structures...\n")

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
    PAGE_READONLY = 0x02
    PAGE_READWRITE = 0x04

    alliance_data = {}
    regions_scanned = 0

    while address < max_address:
        if kernel32.VirtualQueryEx(h_process, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
            address += 0x10000
            continue

        if mbi.State == MEM_COMMIT and mbi.Protect in [PAGE_READONLY, PAGE_READWRITE]:
            scan_size = min(mbi.RegionSize, 5 * 1024 * 1024)
            buffer = (ctypes.c_char * scan_size)()
            bytes_read = ctypes.c_size_t()

            if kernel32.ReadProcessMemory(h_process, ctypes.c_void_p(address), buffer, scan_size, ctypes.byref(bytes_read)):
                data = bytes(buffer[:bytes_read.value])

                # Pattern: ABBR HASH START_DELIM FULLNAME END_DELIM
                # Example: UvvU 37ecf329739c4b61bf9da597829fa993 2veni vidi vici8
                # Start delimiter (2) and end delimiter (8) are not part of the name
                pattern1 = rb'.{0,3}([A-Z][A-Za-z0-9]{1,6})\s+([0-9a-f]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{3,40}?)\d?[\x00-\x08\x0b-\x1f]?'
                matches = re.findall(pattern1, data)

                for abbr, alliance_id, full_name in matches:
                    try:
                        abbr_str = abbr.decode('utf-8', errors='ignore').strip()
                        alliance_id_str = alliance_id.decode('utf-8')
                        full_name_str = full_name.decode('utf-8', errors='ignore').strip()

                        # Clean up names
                        full_name_str = ''.join(c for c in full_name_str if c.isprintable() or c.isspace())
                        full_name_str = ' '.join(full_name_str.split())  # Normalize whitespace

                        if len(full_name_str) > 3 and len(full_name_str) < 50:
                            if alliance_id_str not in alliance_data:
                                alliance_data[alliance_id_str] = {
                                    'abbr': abbr_str,
                                    'name': full_name_str,
                                    'id': alliance_id_str,
                                    'rank': None,
                                    'power': None
                                }
                    except:
                        pass

                # Look for rank numbers near alliance abbreviations
                # Pattern: rank(1-50) as int32 near alliance names
                for alliance_id, info in list(alliance_data.items()):
                    abbr_bytes = info['abbr'].encode('utf-8')
                    offset = 0
                    while True:
                        idx = data.find(abbr_bytes, offset)
                        if idx == -1:
                            break

                        # Check for rank number nearby (within 100 bytes)
                        check_start = max(0, idx - 100)
                        check_end = min(len(data), idx + 50)
                        check_region = data[check_start:check_end]

                        for rank in range(1, 51):
                            rank_bytes = struct.pack('<I', rank)
                            if rank_bytes in check_region:
                                if info['rank'] is None or rank < info['rank']:
                                    info['rank'] = rank

                        # Look for power number nearby (within 200 bytes)
                        power_start = max(0, idx - 100)
                        power_end = min(len(data), idx + 200)
                        power_region = data[power_start:power_end]

                        for i in range(0, len(power_region) - 8, 4):
                            try:
                                val = struct.unpack('<Q', power_region[i:i+8])[0]
                                if 1_000_000_000 <= val <= 10_000_000_000:  # Billion to 10 billion range
                                    if info['power'] is None or abs(val - 6_400_000_000) < abs(info['power'] - 6_400_000_000):
                                        info['power'] = val
                            except:
                                pass

                        offset = idx + 1

            regions_scanned += 1
            if regions_scanned % 200 == 0:
                print(f"  Scanned {regions_scanned} regions, found {len(alliance_data)} unique alliances...")

        address += mbi.RegionSize

    kernel32.CloseHandle(h_process)
    return list(alliance_data.values())

print("Comprehensive Alliance Data Extractor")
print("=" * 60)
print("\n[*] Make sure the alliance rankings are visible in game!")
print("[*] Scanning game memory...\n")

game_proc = find_process("LastWar")
if not game_proc:
    print("[!] Game not running")
    exit(1)

try:
    alliances = scan_memory(game_proc)

    print(f"\n[+] Extraction complete!")
    print(f"[+] Found {len(alliances)} unique alliances\n")

    # Sort by rank
    alliances_with_rank = [a for a in alliances if a['rank'] is not None]
    alliances_without_rank = [a for a in alliances if a['rank'] is None]

    alliances_with_rank.sort(key=lambda x: x['rank'])

    # Display results
    print(f"{'Rank':<6} {'Abbr':<8} {'Full Name':<30} {'Power':<15} {'Alliance ID'}")
    print("=" * 100)

    for alliance in alliances_with_rank[:50]:  # Top 50
        rank = alliance['rank'] if alliance['rank'] else '?'
        abbr = alliance['abbr'][:7]
        name = alliance['name'][:29]
        power = f"{alliance['power']:,}" if alliance['power'] else 'Unknown'
        aid = alliance['id'][:16] + '...'

        print(f"{rank:<6} {abbr:<8} {name:<30} {power:<15} {aid}")

    # Save to CSV
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Rank,Short Name,Full Name,Power,Alliance ID\n")

        for alliance in alliances_with_rank:
            rank = alliance['rank'] if alliance['rank'] else ''
            abbr = alliance['abbr']
            name = alliance['name']
            power = alliance['power'] if alliance['power'] else ''
            aid = alliance['id']

            f.write(f'{rank},"{abbr}","{name}",{power},"{aid}"\n')

        # Also include alliances without rank
        if alliances_without_rank:
            f.write("\n# Alliances found without rank:\n")
            for alliance in alliances_without_rank[:20]:  # Limit to 20
                abbr = alliance['abbr']
                name = alliance['name']
                power = alliance['power'] if alliance['power'] else ''
                aid = alliance['id']
                f.write(f',"{abbr}","{name}",{power},"{aid}"\n')

    print(f"\n[+] Data saved to: {output_file}")

    if alliances_without_rank:
        print(f"[*] Note: Found {len(alliances_without_rank)} additional alliances without rank data")

except PermissionError:
    print("[!] Access denied. Run as Administrator")
except Exception as e:
    print(f"[!] Error: {e}")
    import traceback
    traceback.print_exc()
