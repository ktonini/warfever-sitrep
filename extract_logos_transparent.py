#!/usr/bin/env python3
"""
Extract alliance logos with transparent background and text removal
"""

from PIL import Image
from pathlib import Path
import numpy as np

screenshot_path = Path("alliance_screenshot.png")
output_dir = Path("alliance-logos")
output_dir.mkdir(exist_ok=True)

img = Image.open(screenshot_path)
img_rgba = img.convert('RGBA')
pixels = img.load()
width, height = img.size

SEARCH_X_START = 100
SEARCH_X_END = 220  # Expand search to find full extent

short_names = [
    "UvvU", "ORCE", "NKOT", "STR8", "LE4L", "EPIC", "TASF", "LoL", "HYPH", "MMM",
    "N8N8", "PAKR", "Null", "PARUZ", "MJ40", "DRKK", "aLoB", "CCM", "MMM2", "1Brk",
    "LnfS", "arfa", "EMCY", "AVLS", "Bnd", "NRDS", "NzLs", "NzLs2", "NzLs3", "LATN",
    "LxG4", "Lzgs", "NRDS2", "Frc", "Swrd", "Frk", "Own", "LAWS", "JR19", "MzF",
    "smd", "gd", "Tw", "STRS", "MTF", "BLKH", "JR19_2", "AWRI", "Jug", "AMRI"
]

def should_be_transparent(pixel):
    """Check if pixel should be made transparent (background or text)"""
    r, g, b = pixel[:3]
    avg = (r + g + b) / 3

    # Background (light blue/purple)
    is_bg = (200 <= r <= 207 and 207 <= g <= 214 and 225 <= b <= 232)

    # Very dark pixels (text/rank numbers) - only the darkest
    is_text = avg < 70

    return is_bg or is_text

def is_shield_pixel(pixel):
    """Check if pixel is part of shield"""
    return not should_be_transparent(pixel)

# Step 1: Find all content blocks
print("Finding all shield content blocks...")
shield_blocks = []
current_start = None

for y in range(height):
    has_content = any(
        is_shield_pixel(pixels[x, y])
        for x in range(SEARCH_X_START, min(SEARCH_X_END, width))
        if y < height
    )

    if has_content:
        if current_start is None:
            current_start = y
    else:
        if current_start is not None:
            shield_blocks.append((current_start, y - 1))
            current_start = None

if current_start is not None:
    shield_blocks.append((current_start, height - 1))

# Filter for shield blocks (height between 60-90 pixels)
shield_blocks = [(start, end) for start, end in shield_blocks
                 if 60 <= end - start + 1 <= 90]

print(f"Found {len(shield_blocks)} shield blocks\n")
print("Extracting logos with transparency (skipping first 2)...\n")
print(f"{'Rank':<6} {'Y Range':<15} {'X Range':<15} {'Width':<8} {'Height'}")
print("=" * 70)

# Skip first 2 shields, extract starting from shield 3
for i, (start_y, end_y) in enumerate(shield_blocks[2:50]):
    rank = i + 3
    short_name_idx = rank - 1

    if short_name_idx >= len(short_names):
        break

    short_name = short_names[short_name_idx]

    # Find horizontal bounds (ignoring transparent pixels)
    left_edge = width
    right_edge = 0

    for y in range(start_y, end_y + 1, 2):
        for x in range(SEARCH_X_START, min(SEARCH_X_END, width)):
            if y < height and is_shield_pixel(pixels[x, y]):
                left_edge = min(left_edge, x)
                right_edge = max(right_edge, x)

    if left_edge >= width or right_edge <= 0:
        print(f"{rank:<6} {start_y}-{end_y:<10} - Could not find horizontal bounds")
        continue

    # Add small padding
    left = max(SEARCH_X_START, left_edge - 2)
    right = min(SEARCH_X_END - 1, right_edge + 2)
    top = start_y
    bottom = end_y

    logo_width = right - left + 1
    logo_height = bottom - top + 1

    print(f"{rank:<6} {start_y}-{end_y:<10} {left}-{right:<10} {logo_width:<8} {logo_height}")

    # Crop the region
    logo = img_rgba.crop((left, top, right + 1, bottom + 1))
    logo_data = logo.load()

    # Make background and text transparent, but only in edge zones
    # Define shield center zone (roughly X=130-185 in screenshot coords)
    shield_center_start = max(0, 130 - left)
    shield_center_end = min(logo.width, 185 - left)

    for py in range(logo.height):
        for px in range(logo.width):
            # Always remove background everywhere
            r, g, b = logo_data[px, py][:3]
            is_bg = (200 <= r <= 207 and 207 <= g <= 214 and 225 <= b <= 232)

            if is_bg:
                logo_data[px, py] = (0, 0, 0, 0)
            # Only remove dark text in edge zones (not in shield center)
            elif px < shield_center_start or px > shield_center_end:
                avg = (r + g + b) / 3
                if avg < 70:
                    logo_data[px, py] = (0, 0, 0, 0)

    # Save as PNG with transparency
    logo_file = output_dir / f"{rank:02d}_{short_name}.png"
    logo.save(logo_file)

print(f"\n[+] All logos saved to: {output_dir}/")
