#!/usr/bin/env python3
"""
The Last War Asset Bundle Explorer

This script explores Unity asset bundles in StreamingAssets to find images,
particularly alliance logos and resource item icons.
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
    game_data_path = Path(sys.argv[1])
elif default_game_path:
    game_data_path = default_game_path
    print(f"Auto-detected game version: {default_game_path.parent.name}")
else:
    game_data_path = None

if not game_data_path or not game_data_path.exists():
    print(f"Error: Could not find The Last War installation")
    sys.exit(1)

# Target the AssetBundles directory
assetbundles_path = game_data_path / 'StreamingAssets' / 'AssetBundles'

if not assetbundles_path.exists():
    print(f"Error: AssetBundles directory not found at {assetbundles_path}")
    sys.exit(1)

print(f"Scanning asset bundles in: {assetbundles_path}")
print("This may take several minutes...\n")

# Dictionary to store all found textures
all_textures = {}
all_sprites = {}

# Scan each asset bundle file
bundle_files = ['gameres', 'packageres', 'download', 'datatable', 'dllres', 'lua']

for bundle_name in bundle_files:
    bundle_path = assetbundles_path / bundle_name

    if not bundle_path.exists():
        print(f"  Skipping {bundle_name} (not found)")
        continue

    print(f"  Loading {bundle_name}...")

    try:
        env = UnityPy.load(str(bundle_path))

        texture_count = 0
        sprite_count = 0

        for obj in env.objects:
            if obj.type.name == "Texture2D":
                data = obj.read()
                name = data.m_Name if hasattr(data, 'm_Name') else f"Texture_{obj.path_id}"

                all_textures[f"{bundle_name}/{name}"] = {
                    'bundle': bundle_name,
                    'path_id': obj.path_id,
                    'container': obj.container if hasattr(obj, 'container') else None,
                    'width': data.m_Width if hasattr(data, 'm_Width') else 0,
                    'height': data.m_Height if hasattr(data, 'm_Height') else 0,
                    'format': str(data.m_TextureFormat) if hasattr(data, 'm_TextureFormat') else "Unknown",
                }
                texture_count += 1

            elif obj.type.name == "Sprite":
                data = obj.read()
                name = data.m_Name if hasattr(data, 'm_Name') else f"Sprite_{obj.path_id}"

                all_sprites[f"{bundle_name}/{name}"] = {
                    'bundle': bundle_name,
                    'path_id': obj.path_id,
                    'container': obj.container if hasattr(obj, 'container') else None,
                }
                sprite_count += 1

        print(f"    Found {texture_count} textures, {sprite_count} sprites")

    except Exception as e:
        print(f"    Error loading {bundle_name}: {e}")

print(f"\nTotal: {len(all_textures)} textures, {len(all_sprites)} sprites")

# Keywords for filtering
alliance_keywords = ['alliance', 'guild', 'clan', 'logo', 'emblem', 'badge', 'totem', 'flag']
resource_keywords = ['item', 'resource', 'gold', 'gem', 'diamond', 'chest', 'coin', 'crystal', 'brick', 'ore', 'food', 'oil', 'steel', 'titanium']
ui_keywords = ['icon', 'button', 'ui', 'interface']

# Filter and display results
print("\n" + "="*80)
print("POTENTIAL ALLIANCE LOGOS:")
print("="*80)

alliance_matches = []
for name, info in all_textures.items():
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in alliance_keywords):
        alliance_matches.append((name, info))

if alliance_matches:
    for name, info in sorted(alliance_matches):
        print(f"\n  {name}")
        print(f"    Bundle: {info['bundle']}")
        print(f"    Size: {info['width']}x{info['height']}")
        print(f"    Format: {info['format']}")
        if info['container']:
            print(f"    Container: {info['container']}")
else:
    print("  (None found with common keywords)")

print("\n" + "="*80)
print("POTENTIAL RESOURCE/ITEM ICONS:")
print("="*80)

resource_matches = []
for name, info in all_textures.items():
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in resource_keywords):
        resource_matches.append((name, info))

if resource_matches:
    for name, info in sorted(resource_matches):
        print(f"\n  {name}")
        print(f"    Bundle: {info['bundle']}")
        print(f"    Size: {info['width']}x{info['height']}")
        print(f"    Format: {info['format']}")
        if info['container']:
            print(f"    Container: {info['container']}")
else:
    print("  (None found with common keywords)")

# Save complete catalog
output_file = "assetbundle_catalog.txt"
print(f"\n{'='*80}")
print(f"Saving complete catalog to: {output_file}")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("THE LAST WAR - ASSET BUNDLE IMAGE CATALOG\n")
    f.write("="*80 + "\n\n")

    f.write("TEXTURES:\n")
    f.write("-"*80 + "\n\n")
    for name, info in sorted(all_textures.items()):
        f.write(f"{name}\n")
        f.write(f"  Bundle: {info['bundle']}\n")
        f.write(f"  Size: {info['width']}x{info['height']}\n")
        f.write(f"  Format: {info['format']}\n")
        if info['container']:
            f.write(f"  Container: {info['container']}\n")
        f.write(f"  Path ID: {info['path_id']}\n\n")

    f.write("\n" + "="*80 + "\n")
    f.write("SPRITES:\n")
    f.write("-"*80 + "\n\n")
    for name, info in sorted(all_sprites.items()):
        f.write(f"{name}\n")
        f.write(f"  Bundle: {info['bundle']}\n")
        if info['container']:
            f.write(f"  Container: {info['container']}\n")
        f.write(f"  Path ID: {info['path_id']}\n\n")

print(f"Complete! Found {len(alliance_matches)} potential alliance images")
print(f"         and {len(resource_matches)} potential resource/item images")
