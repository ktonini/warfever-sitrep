#!/usr/bin/env python3
"""
Scan game memory for alliance ranking text data
"""

import psutil
import ctypes
from ctypes import wintypes
import re
from pathlib import Path

output_file = Path("alliance_data_from_memory.txt")

# Known alliance short names from our CSV
KNOWN_ALLIANCES = [
    "UvvU", "ORCE", "NKOT", "STR8", "LE4L", "EPIC", "TASF", "LoL", "HYPH", "MMM",
    "N8N8", "PAKR", "Null", "PARUZ", "MJ40", "DRKK", "aLoB", "CCM", "MMM2", "1Brk",
    "LnfS", "arfa", "EMCY", "AVLS", "Bnd", "NRDS", "NzLs", "NzLs2", "NzLs3", "LATN",
    "LxG4", "Lzgs", "NRDS2", "Frc", "Swrd", "Frk", "Own", "LAWS", "JR19", "MzF",
    "smd", "gd", "Tw", "STRS", "MTF", "BLKH", "JR19_2", "AWRI", "Jug", "AMRI"
]

def find_process(name_pattern):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name_pattern.lower() in proc.info['name'].lower():
                return proc
        except:
            pass
    return None

def scan_memory_for_strings(proc):
    """Scan process memory for alliance-related strings"""
    kernel32 = ctypes.windll.kernel32

    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400

    h_process = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
        False,
        proc.pid
    )

    if not h_process:
        print(f"[!] Failed to open process")
        return []

    print(f"[+] Scanning memory: {proc.info['name']} (PID: {proc.pid})")
    print(f"[*] Looking for alliance names and data...\n")

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

    found_strings = []
    regions_scanned = 0

    while address < max_address:
        if kernel32.VirtualQueryEx(h_process, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
            address += 0x10000
            continue

        # Scan readable/writable memory where strings are likely stored
        if mbi.State == MEM_COMMIT and mbi.Protect in [PAGE_READONLY, PAGE_READWRITE]:
            scan_size = min(mbi.RegionSize, 5 * 1024 * 1024)
            buffer = (ctypes.c_char * scan_size)()
            bytes_read = ctypes.c_size_t()

            if kernel32.ReadProcessMemory(h_process, ctypes.c_void_p(address), buffer, scan_size, ctypes.byref(bytes_read)):
                data = bytes(buffer[:bytes_read.value])

                try:
                    # Try to decode as UTF-8
                    text = data.decode('utf-8', errors='ignore')

                    # Look for known alliance names
                    for alliance_name in KNOWN_ALLIANCES:
                        if alliance_name in text:
                            # Find context around the alliance name
                            idx = text.find(alliance_name)
                            context_start = max(0, idx - 100)
                            context_end = min(len(text), idx + 200)
                            context = text[context_start:context_end]

                            # Clean up the context
                            context = context.replace('\x00', ' ').strip()

                            found_strings.append({
                                'address': hex(address + context_start),
                                'alliance': alliance_name,
                                'context': context
                            })

                    # Also look for power numbers (format: 1,234,567,890)
                    power_pattern = re.findall(r'[\d,]{9,}', text)
                    if power_pattern:
                        for power in power_pattern:
                            # Check if there's an alliance name nearby
                            power_idx = text.find(power)
                            nearby_text = text[max(0, power_idx-200):min(len(text), power_idx+50)]

                            for alliance_name in KNOWN_ALLIANCES:
                                if alliance_name in nearby_text:
                                    found_strings.append({
                                        'address': hex(address + power_idx),
                                        'type': 'power',
                                        'alliance': alliance_name,
                                        'power': power,
                                        'context': nearby_text.replace('\x00', ' ').strip()
                                    })
                                    break

                except:
                    pass

            regions_scanned += 1
            if regions_scanned % 100 == 0:
                print(f"  Scanned {regions_scanned} regions, found {len(found_strings)} matches...")

        address += mbi.RegionSize

    kernel32.CloseHandle(h_process)
    return found_strings

print("Alliance Data Memory Scanner")
print("=" * 60)
print("\n[*] Scanning game memory for alliance data...")

game_proc = find_process("LastWar")
if not game_proc:
    print("[!] Game not running!")
    exit(1)

try:
    results = scan_memory_for_strings(game_proc)

    print(f"\n[+] Found {len(results)} alliance-related strings in memory\n")

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Alliance Data Found in Memory\n")
        f.write("=" * 60 + "\n\n")

        for item in results:
            f.write(f"Address: {item['address']}\n")
            if 'alliance' in item:
                f.write(f"Alliance: {item['alliance']}\n")
            if 'power' in item:
                f.write(f"Power: {item['power']}\n")
            f.write(f"Context: {item['context'][:200]}\n")
            f.write("-" * 60 + "\n\n")

    print(f"[+] Results saved to: {output_file}")

    # Show some samples
    print("\nSample findings:")
    for item in results[:10]:
        alliance = item.get('alliance', 'Unknown')
        power = item.get('power', '')
        print(f"  {alliance} {power}")

except PermissionError:
    print("[!] Access denied. Run as Administrator.")
except Exception as e:
    print(f"[!] Error: {e}")
    import traceback
    traceback.print_exc()
