#!/usr/bin/env python3
"""
Scan for alliance rankings data - look for rank numbers 1-50 near alliance names
"""

import psutil
import ctypes
from ctypes import wintypes
import struct

def find_process(name_pattern):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name_pattern.lower() in proc.info['name'].lower():
                return proc
        except:
            pass
    return None

def scan_for_rankings(proc):
    """Scan for alliance ranking data structures"""
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

    print(f"[+] Scanning for ranking data structures...")
    print(f"[*] Looking for patterns: rank(1-50) + alliance_name + power\n")

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

    found_structures = []
    regions_scanned = 0

    # Known first alliance
    uvvu_bytes = b'UvvU'

    while address < max_address:
        if kernel32.VirtualQueryEx(h_process, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
            address += 0x10000
            continue

        if mbi.State == MEM_COMMIT and mbi.Protect == PAGE_READWRITE:
            scan_size = min(mbi.RegionSize, 5 * 1024 * 1024)
            buffer = (ctypes.c_char * scan_size)()
            bytes_read = ctypes.c_size_t()

            if kernel32.ReadProcessMemory(h_process, ctypes.c_void_p(address), buffer, scan_size, ctypes.byref(bytes_read)):
                data = bytes(buffer[:bytes_read.value])

                # Look for UvvU
                offset = 0
                while True:
                    idx = data.find(uvvu_bytes, offset)
                    if idx == -1:
                        break

                    # Check if there's a rank=1 nearby (as int32, int16, or byte)
                    check_start = max(0, idx - 100)
                    check_end = min(len(data), idx + 100)
                    check_region = data[check_start:check_end]

                    # Look for the number 1 in various formats near UvvU
                    for i in range(len(check_region) - 8):
                        # Check for rank = 1 (as different int types)
                        if check_region[i:i+4] == b'\x01\x00\x00\x00':  # int32 = 1
                            # Found rank 1! Now look for large numbers (power) nearby
                            power_start = max(0, idx - 50)
                            power_end = min(len(data), idx + 200)
                            power_region = data[power_start:power_end]

                            for j in range(0, len(power_region) - 8, 4):
                                try:
                                    # Try reading as uint32
                                    val = struct.unpack('<I', power_region[j:j+4])[0]
                                    if 5_000_000_000 <= val <= 10_000_000_000:
                                        mem_addr = address + power_start + j
                                        distance_from_uvvu = (power_start + j) - idx

                                        print(f"[MATCH] UvvU at 0x{address+idx:016x}")
                                        print(f"        Rank=1 found")
                                        print(f"        Power={val:,} at offset {distance_from_uvvu:+d} from UvvU")
                                        print(f"        Memory address: 0x{mem_addr:016x}\n")

                                        found_structures.append({
                                            'address': mem_addr,
                                            'alliance': 'UvvU',
                                            'rank': 1,
                                            'power': val
                                        })

                                    # Try uint64
                                    val64 = struct.unpack('<Q', power_region[j:j+8])[0]
                                    if 5_000_000_000 <= val64 <= 10_000_000_000:
                                        mem_addr = address + power_start + j
                                        distance_from_uvvu = (power_start + j) - idx

                                        print(f"[MATCH] UvvU at 0x{address+idx:016x}")
                                        print(f"        Rank=1 found")
                                        print(f"        Power={val64:,} (uint64) at offset {distance_from_uvvu:+d}")
                                        print(f"        Memory address: 0x{mem_addr:016x}\n")

                                        found_structures.append({
                                            'address': mem_addr,
                                            'alliance': 'UvvU',
                                            'rank': 1,
                                            'power': val64
                                        })
                                except:
                                    pass

                    offset = idx + 1

            regions_scanned += 1
            if regions_scanned % 100 == 0:
                print(f"  Scanned {regions_scanned} regions...")

        address += mbi.RegionSize

    kernel32.CloseHandle(h_process)
    return found_structures

print("Alliance Ranking Data Scanner")
print("=" * 60)

game_proc = find_process("LastWar")
if not game_proc:
    print("[!] Game not running")
    exit(1)

try:
    results = scan_for_rankings(game_proc)
    print(f"\n[+] Found {len(results)} potential ranking structures")

except PermissionError:
    print("[!] Access denied. Run as Administrator")
except Exception as e:
    print(f"[!] Error: {e}")
    import traceback
    traceback.print_exc()
