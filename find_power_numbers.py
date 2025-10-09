#!/usr/bin/env python3
"""
Find power numbers near alliance names in memory
"""

import struct
from pathlib import Path

input_file = Path("alliance_data_from_memory.txt")

# Read raw memory data
with open(input_file, 'rb') as f:
    data = f.read()

# Known values to search for
known_alliances = {
    b'UvvU': 6435764372,
    b'ORCE': 6387057595,  # From your CSV
}

print("Searching for alliance power numbers in memory...\n")

for alliance_bytes, expected_power in known_alliances.items():
    print(f"Looking for {alliance_bytes.decode()} (power: {expected_power:,})")

    # Find all occurrences of the alliance name
    offset = 0
    found_count = 0

    while True:
        idx = data.find(alliance_bytes, offset)
        if idx == -1:
            break

        found_count += 1

        # Look for the power number as different integer types near this location
        # Check 200 bytes before and after
        search_start = max(0, idx - 200)
        search_end = min(len(data), idx + 200)
        search_region = data[search_start:search_end]

        # Try to find the power number as uint32, uint64, little/big endian
        power_formats = [
            ('uint32_le', 4, 'little', False),
            ('uint32_be', 4, 'big', False),
            ('uint64_le', 8, 'little', False),
            ('uint64_be', 8, 'big', False),
            ('int32_le', 4, 'little', True),
            ('int64_le', 8, 'little', True),
        ]

        for fmt_name, size, endian, signed in power_formats:
            # Try every offset in the search region
            for i in range(len(search_region) - size):
                try:
                    if signed:
                        value = int.from_bytes(search_region[i:i+size], endian, signed=True)
                    else:
                        value = int.from_bytes(search_region[i:i+size], endian, signed=False)

                    # Check if it's close to our expected value (within 10%)
                    if abs(value - expected_power) < expected_power * 0.1:
                        actual_offset = search_start + i
                        distance_from_name = actual_offset - idx

                        print(f"  FOUND at offset {actual_offset:08x} (distance: {distance_from_name:+4d} bytes)")
                        print(f"    Format: {fmt_name}, Value: {value:,}")

                        # Show context
                        ctx_start = max(0, actual_offset - 20)
                        ctx_end = min(len(data), actual_offset + 20)
                        context = data[ctx_start:ctx_end]
                        print(f"    Context: {context[:40]}")
                        print()

                except:
                    pass

        offset = idx + 1

    print(f"  Total occurrences of '{alliance_bytes.decode()}': {found_count}\n")

print("\nNow searching for raw binary patterns...")

# Also search for the exact hex bytes
for alliance_name, power in known_alliances.items():
    print(f"\n{alliance_name.decode()} power as different formats:")

    # Little endian uint32
    le32 = power.to_bytes(4, 'little', signed=False) if power < 2**32 else None
    if le32 and le32 in data:
        idx = data.find(le32)
        print(f"  Found as LE uint32 at offset: 0x{idx:08x}")

    # Little endian uint64
    le64 = power.to_bytes(8, 'little', signed=False)
    if le64 in data:
        idx = data.find(le64)
        print(f"  Found as LE uint64 at offset: 0x{idx:08x}")

    # Big endian uint32
    be32 = power.to_bytes(4, 'big', signed=False) if power < 2**32 else None
    if be32 and be32 in data:
        idx = data.find(be32)
        print(f"  Found as BE uint32 at offset: 0x{idx:08x}")

    # Big endian uint64
    be64 = power.to_bytes(8, 'big', signed=False)
    if be64 in data:
        idx = data.find(be64)
        print(f"  Found as BE uint64 at offset: 0x{idx:08x}")
