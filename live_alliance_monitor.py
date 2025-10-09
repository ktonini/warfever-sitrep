#!/usr/bin/env python3
"""
Live Alliance Data Monitor
Watches memory in real-time as you scroll through alliance rankings
Press Ctrl+C to stop and save data
"""

import psutil
import ctypes
from ctypes import wintypes
import struct
import re
import time
from pathlib import Path
from collections import defaultdict

output_file = Path("live_alliance_data.csv")

def find_process(name_pattern):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name_pattern.lower() in proc.info['name'].lower():
                return proc
        except:
            pass
    return None

def quick_scan(h_process, kernel32):
    """Quick scan of readable memory for alliance data"""

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

    found_data = {}

    while address < max_address:
        if kernel32.VirtualQueryEx(h_process, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
            address += 0x10000
            continue

        # Only scan writable memory for latest data
        if mbi.State == MEM_COMMIT and mbi.Protect == PAGE_READWRITE:
            scan_size = min(mbi.RegionSize, 2 * 1024 * 1024)  # 2MB chunks
            buffer = (ctypes.c_char * scan_size)()
            bytes_read = ctypes.c_size_t()

            if kernel32.ReadProcessMemory(h_process, ctypes.c_void_p(address), buffer, scan_size, ctypes.byref(bytes_read)):
                data = bytes(buffer[:bytes_read.value])

                # Pattern: ABBR HASH START_DELIM FULLNAME END_DELIM
                # Example: UvvU 37ecf329...fa993 2veni vidi vici8
                # Start delimiter (2) and end delimiter (8) are not part of the name
                pattern = rb'([A-Z][A-Za-z0-9]{1,6})\s+([0-9a-f]{32})\s+\d([^\d\x00-\x08\x0b-\x1f]{3,40}?)\d?[\x00-\x08\x0b-\x1f]?'
                matches = re.findall(pattern, data)

                for abbr, alliance_id, full_name in matches:
                    try:
                        abbr_str = abbr.decode('utf-8', errors='ignore').strip()
                        alliance_id_str = alliance_id.decode('utf-8')
                        full_name_str = full_name.decode('utf-8', errors='ignore').strip()

                        # Clean up
                        full_name_str = ''.join(c for c in full_name_str if c.isprintable() or c.isspace())
                        full_name_str = ' '.join(full_name_str.split())

                        if 3 < len(full_name_str) < 50 and len(abbr_str) <= 10:
                            # Look for rank nearby
                            abbr_idx = data.find(abbr)
                            rank = None
                            power = None

                            if abbr_idx != -1:
                                check_start = max(0, abbr_idx - 100)
                                check_end = min(len(data), abbr_idx + 200)
                                check_region = data[check_start:check_end]

                                # Find rank (1-50)
                                for r in range(1, 51):
                                    if struct.pack('<I', r) in check_region:
                                        rank = r
                                        break

                                # Find power
                                for i in range(0, len(check_region) - 8, 4):
                                    try:
                                        val = struct.unpack('<Q', check_region[i:i+8])[0]
                                        if 1_000_000_000 <= val <= 10_000_000_000:
                                            power = val
                                            break
                                    except:
                                        pass

                            found_data[alliance_id_str] = {
                                'abbr': abbr_str,
                                'name': full_name_str,
                                'id': alliance_id_str,
                                'rank': rank,
                                'power': power
                            }
                    except:
                        pass

        address += mbi.RegionSize

    return found_data

print("Live Alliance Monitor")
print("=" * 60)
print("\n[*] Instructions:")
print("    1. Make sure alliance rankings window is open in game")
print("    2. Slowly scroll through the rankings")
print("    3. This will continuously scan and capture data")
print("    4. Press Ctrl+C when done to save\n")

game_proc = find_process("LastWar")
if not game_proc:
    print("[!] Game not running")
    exit(1)

print(f"[+] Found game: {game_proc.info['name']} (PID: {game_proc.pid})")

kernel32 = ctypes.windll.kernel32
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

h_process = kernel32.OpenProcess(
    PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
    False,
    game_proc.pid
)

if not h_process:
    print("[!] Failed to open process")
    exit(1)

print("[+] Memory access granted")
print("\n[*] Monitoring... (Ctrl+C to stop)\n")

all_alliances = {}
scan_count = 0

try:
    while True:
        scan_count += 1
        print(f"\r[Scan #{scan_count}] Alliances found: {len(all_alliances)}", end='', flush=True)

        # Quick scan
        new_data = quick_scan(h_process, kernel32)

        # Merge with existing data
        for aid, info in new_data.items():
            if aid not in all_alliances:
                all_alliances[aid] = info
            else:
                # Update if we found better data
                if info['rank'] and not all_alliances[aid]['rank']:
                    all_alliances[aid]['rank'] = info['rank']
                if info['power'] and not all_alliances[aid]['power']:
                    all_alliances[aid]['power'] = info['power']

        # Wait a bit before next scan
        time.sleep(2)

except KeyboardInterrupt:
    print("\n\n[*] Stopping monitor...")

finally:
    kernel32.CloseHandle(h_process)

    print(f"\n[+] Captured {len(all_alliances)} unique alliances!")

    if all_alliances:
        # Sort by rank
        alliances_list = list(all_alliances.values())
        alliances_with_rank = [a for a in alliances_list if a['rank']]
        alliances_without_rank = [a for a in alliances_list if not a['rank']]

        alliances_with_rank.sort(key=lambda x: x['rank'])

        # Display
        print(f"\n{'Rank':<6} {'Abbr':<8} {'Full Name':<30} {'Power'}")
        print("=" * 70)

        for a in alliances_with_rank[:20]:  # Show first 20
            rank = a['rank'] if a['rank'] else '?'
            power = f"{a['power']:,}" if a['power'] else 'Unknown'
            print(f"{rank:<6} {a['abbr']:<8} {a['name']:<30} {power}")

        if len(alliances_with_rank) > 20:
            print(f"... and {len(alliances_with_rank) - 20} more")

        # Save to CSV
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Rank,Short Name,Full Name,Power,Alliance ID\n")

            for a in alliances_with_rank:
                rank = a['rank'] if a['rank'] else ''
                power = a['power'] if a['power'] else ''
                f.write(f'{rank},"{a["abbr"]}","{a["name"]}",{power},"{a["id"]}"\n')

            if alliances_without_rank:
                f.write("\n# Without rank data:\n")
                for a in alliances_without_rank:
                    power = a['power'] if a['power'] else ''
                    f.write(f',"{a["abbr"]}","{a["name"]}",{power},"{a["id"]}"\n')

        print(f"\n[+] Data saved to: {output_file}")
    else:
        print("\n[!] No alliance data captured")
