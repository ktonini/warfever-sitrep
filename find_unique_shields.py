#!/usr/bin/env python3
"""
Find truly unique shield designs using visual comparison
"""

from PIL import Image
from pathlib import Path
import imagehash

cleaned_dir = Path("alliance-logos-cleaned")
unique_dir = Path("alliance-logos-unique")
unique_dir.mkdir(exist_ok=True)

print("Analyzing shield designs for duplicates...\n")

# Calculate perceptual hashes with higher precision
hashes = {}
for logo_file in sorted(cleaned_dir.glob("*.png")):
    img = Image.open(logo_file)

    # Use difference hash which is better for similar images
    # Lower hash_size = more tolerance for minor differences
    img_hash = imagehash.dhash(img, hash_size=8)

    if img_hash not in hashes:
        hashes[img_hash] = []
    hashes[img_hash].append(logo_file.name)

# Group similar hashes (allow small variations)
# Merge groups with very similar hashes
merged_groups = {}
hash_list = list(hashes.keys())

for i, hash1 in enumerate(hash_list):
    merged_key = hash1

    # Find if this hash is similar to any existing merged group
    for existing_key in list(merged_groups.keys()):
        # If hashes differ by less than 5 bits, consider them the same design
        if hash1 - existing_key < 5:
            merged_key = existing_key
            break

    if merged_key not in merged_groups:
        merged_groups[merged_key] = []

    merged_groups[merged_key].extend(hashes[hash1])

# Sort by group size
sorted_groups = sorted(merged_groups.items(), key=lambda x: len(x[1]), reverse=True)

print(f"{'Group':<8} {'Count':<8} {'Representative':<20} {'Others'}")
print("=" * 100)

for idx, (img_hash, files) in enumerate(sorted_groups, 1):
    representative = files[0]
    others = files[1:] if len(files) > 1 else []

    if others:
        print(f"{idx:<8} {len(files):<8} {representative:<20} {', '.join(others[:5])}")
        if len(others) > 5:
            print(f"{' '*37}... and {len(others)-5} more")
    else:
        print(f"{idx:<8} {len(files):<8} {representative:<20}")

    # Copy representative to unique folder
    src = cleaned_dir / representative
    dst = unique_dir / f"design_{idx:02d}_{representative}"
    if src.exists():
        img = Image.open(src)
        img.save(dst)

print(f"\n{'='*100}")
print(f"Total unique shield designs: {len(sorted_groups)}")
print(f"Total logos analyzed: {sum(len(files) for files in merged_groups.values())}")
print(f"\nUnique designs saved to: {unique_dir}/")
