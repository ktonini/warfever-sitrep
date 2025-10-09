#!/usr/bin/env python3
"""
Clean up text remnants and find duplicate shield designs
"""

from PIL import Image
from pathlib import Path
import imagehash

logos_dir = Path("alliance-logos")
cleaned_dir = Path("alliance-logos-cleaned")
cleaned_dir.mkdir(exist_ok=True)

print("Step 1: Cleaning text remnants from right edge...\n")

# Process each logo
for logo_file in sorted(logos_dir.glob("*.png")):
    img = Image.open(logo_file).convert('RGBA')
    pixels = img.load()

    # Clean up lighter text remnants on right edge (rightmost 30 pixels)
    edge_width = 30
    start_x = max(0, img.width - edge_width)

    for y in range(img.height):
        for x in range(start_x, img.width):
            r, g, b, a = pixels[x, y]

            if a > 0:  # Only check non-transparent pixels
                avg = (r + g + b) / 3

                # Remove lighter gray text (avg 70-150)
                variance = max(abs(r - avg), abs(g - avg), abs(b - avg))
                if 70 <= avg <= 150 and variance < 40:
                    pixels[x, y] = (0, 0, 0, 0)

    # Save cleaned version
    cleaned_file = cleaned_dir / logo_file.name
    img.save(cleaned_file)

print(f"Cleaned {len(list(logos_dir.glob('*.png')))} logos\n")

print("Step 2: Finding duplicate shield designs...\n")

# Calculate perceptual hashes for each logo
hashes = {}
for logo_file in sorted(cleaned_dir.glob("*.png")):
    img = Image.open(logo_file)
    # Use average hash for perceptual similarity
    img_hash = imagehash.average_hash(img, hash_size=16)

    if img_hash not in hashes:
        hashes[img_hash] = []
    hashes[img_hash].append(logo_file.name)

# Find duplicates
print(f"{'Hash':<20} {'Count':<8} {'Files'}")
print("=" * 80)

unique_count = 0
duplicate_groups = []

for img_hash, files in sorted(hashes.items(), key=lambda x: len(x[1]), reverse=True):
    if len(files) > 1:
        print(f"{str(img_hash):<20} {len(files):<8} {', '.join(files)}")
        duplicate_groups.append(files)
    else:
        unique_count += 1

print(f"\nSummary:")
print(f"  Unique logos: {unique_count}")
print(f"  Duplicate groups: {len(duplicate_groups)}")
print(f"  Total logos: {len(list(cleaned_dir.glob('*.png')))}")

# Create deduplicated set
if duplicate_groups:
    deduped_dir = Path("alliance-logos-unique")
    deduped_dir.mkdir(exist_ok=True)

    print(f"\nStep 3: Creating deduplicated set...\n")

    # Copy all unique logos
    copied = set()
    for img_hash, files in hashes.items():
        # Keep the first file from each group
        source = cleaned_dir / files[0]
        dest = deduped_dir / files[0]

        if source.exists():
            img = Image.open(source)
            img.save(dest)
            copied.add(files[0])

            if len(files) > 1:
                print(f"Kept: {files[0]} (duplicates: {', '.join(files[1:])})")

    print(f"\nCreated {len(copied)} unique logos in {deduped_dir}/")
