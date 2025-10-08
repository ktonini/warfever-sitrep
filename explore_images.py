#!/usr/bin/env python3
"""
The Last War Image Explorer

This script explores Unity asset bundles to find and list images,
helping to identify alliance logos, resource items, and other game assets.
"""

import UnityPy
import os
import sys
from pathlib import Path
import re

# Set the Unity version for proper asset parsing
UnityPy.config.FALLBACK_UNITY_VERSION = "2019.4.40f1"

def find_latest_game_version():
    """Find the latest version of The Last War installed."""
    game_base_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'TheLastWar'

    if not game_base_path.exists():
        return None

    app_dirs = [d for d in game_base_path.iterdir() if d.is_dir() and d.name.startswith('app-')]

    if not app_dirs:
        return None

    def extract_version(path):
        match = re.search(r'app-(\d+)\.(\d+)\.(\d+)', path.name)
        if match:
            return tuple(map(int, match.groups()))
        return (0, 0, 0)

    app_dirs.sort(key=extract_version, reverse=True)
    latest_version = app_dirs[0] / 'LastWar_Data'

    return latest_version if latest_version.exists() else None

# Get game path
default_game_path = find_latest_game_version()

if len(sys.argv) > 1:
    game_data_path = sys.argv[1]
elif default_game_path:
    game_data_path = str(default_game_path)
    print(f"Auto-detected game version: {default_game_path.parent.name}")
else:
    game_data_path = None

if not game_data_path or not os.path.exists(game_data_path):
    print(f"Error: Could not find The Last War installation")
    sys.exit(1)

print(f"Loading Unity assets from {game_data_path}...")
print("This may take a while...\n")

env = UnityPy.load(game_data_path)

# Dictionaries to categorize found images
textures = {}
sprites = {}

print("Scanning for images...")

# Iterate through all objects
for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        name = data.m_Name if hasattr(data, 'm_Name') else f"Texture_{obj.path_id}"
        textures[name] = {
            'path_id': obj.path_id,
            'container': obj.container if hasattr(obj, 'container') else None,
            'width': data.m_Width if hasattr(data, 'm_Width') else 0,
            'height': data.m_Height if hasattr(data, 'm_Height') else 0,
        }

    elif obj.type.name == "Sprite":
        data = obj.read()
        name = data.m_Name if hasattr(data, 'm_Name') else f"Sprite_{obj.path_id}"
        sprites[name] = {
            'path_id': obj.path_id,
            'container': obj.container if hasattr(obj, 'container') else None,
        }

print(f"\nFound {len(textures)} textures and {len(sprites)} sprites")

# Filter for likely alliance/resource images
alliance_keywords = ['alliance', 'guild', 'clan', 'logo', 'emblem', 'badge', 'icon']
resource_keywords = ['gold', 'gem', 'diamond', 'chest', 'resource', 'item', 'coin', 'crystal']

print("\n" + "="*80)
print("POTENTIAL ALLIANCE LOGOS:")
print("="*80)

alliance_images = []
for name in textures.keys():
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in alliance_keywords):
        alliance_images.append(name)
        print(f"  {name}")
        if textures[name]['container']:
            print(f"    Container: {textures[name]['container']}")
        print(f"    Size: {textures[name]['width']}x{textures[name]['height']}")

if not alliance_images:
    print("  (None found with common keywords)")

print("\n" + "="*80)
print("POTENTIAL RESOURCE ITEMS:")
print("="*80)

resource_images = []
for name in textures.keys():
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in resource_keywords):
        resource_images.append(name)
        print(f"  {name}")
        if textures[name]['container']:
            print(f"    Container: {textures[name]['container']}")
        print(f"    Size: {textures[name]['width']}x{textures[name]['height']}")

if not resource_images:
    print("  (None found with common keywords)")

# Save complete list to file for analysis
output_file = "image_catalog.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("THE LAST WAR - IMAGE CATALOG\n")
    f.write("="*80 + "\n\n")

    f.write("TEXTURES:\n")
    f.write("-"*80 + "\n")
    for name, info in sorted(textures.items()):
        f.write(f"{name}\n")
        if info['container']:
            f.write(f"  Container: {info['container']}\n")
        f.write(f"  Size: {info['width']}x{info['height']}\n")
        f.write(f"  Path ID: {info['path_id']}\n\n")

    f.write("\n" + "="*80 + "\n")
    f.write("SPRITES:\n")
    f.write("-"*80 + "\n")
    for name, info in sorted(sprites.items()):
        f.write(f"{name}\n")
        if info['container']:
            f.write(f"  Container: {info['container']}\n")
        f.write(f"  Path ID: {info['path_id']}\n\n")

print(f"\n{'='*80}")
print(f"Complete catalog saved to: {output_file}")
print(f"Total: {len(textures)} textures, {len(sprites)} sprites")
