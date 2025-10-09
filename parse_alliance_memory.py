#!/usr/bin/env python3
"""
Parse alliance data from memory dump
"""

import re
from pathlib import Path

input_file = Path("alliance_data_from_memory.txt")
output_file = Path("alliances_from_memory.csv")

# Read the memory dump
with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Pattern: (PREFIX)SHORT_NAME HASH (NUMBER)FULL_NAME8
# Example: GMUvvU 37ecf329739c4b61bf9da597829fa993 2veni vidi vici8@
pattern = r'.{0,3}([A-Z][A-Za-z0-9]{1,5})\s+([0-9a-f]{32})\s+\d([^8\x00]+?)8'

matches = re.findall(pattern, content)

alliances = {}
for short_name, hash_val, full_name in matches:
    full_name = full_name.strip()
    # Filter out garbage
    if len(full_name) > 3 and len(full_name) < 50:
        # Clean up the name
        full_name = ''.join(c for c in full_name if c.isprintable())
        if short_name not in alliances or len(full_name) > len(alliances[short_name]):
            alliances[short_name] = full_name

print(f"Found {len(alliances)} unique alliances:\n")

# Sort and display
sorted_alliances = sorted(alliances.items())

for short, full in sorted_alliances:
    print(f"  {short:<10} -> {full}")

# Save to CSV
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("Short Name,Full Name\n")
    for short, full in sorted_alliances:
        f.write(f'"{short}","{full}"\n')

print(f"\n[+] Saved to: {output_file}")
