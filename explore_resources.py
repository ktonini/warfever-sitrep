#!/usr/bin/env python3
"""
The Last War Resources Explorer

Explores Unity Resources directory for embedded assets.
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

# Target the Resources directory
resources_path = game_data_path / 'Resources'

if not resources_path.exists():
    print(f"Error: Resources directory not found")
    sys.exit(1)

print(f"Scanning Resources in: {resources_path}")
print()

# Dictionary to store all found assets
all_textures = {}
all_sprites = {}
all_objects = {}

# Get all files in Resources
resource_files = list(resources_path.glob('*'))

for resource_file in resource_files:
    if resource_file.is_file():
        print(f"  Loading {resource_file.name}...")

        try:
            env = UnityPy.load(str(resource_file))

            texture_count = 0
            sprite_count = 0
            other_count = 0

            for obj in env.objects:
                obj_type = obj.type.name

                if obj_type == "Texture2D":
                    data = obj.read()
                    name = data.m_Name if hasattr(data, 'm_Name') else f"Texture_{obj.path_id}"

                    all_textures[f"{resource_file.name}/{name}"] = {
                        'file': resource_file.name,
                        'path_id': obj.path_id,
                        'container': obj.container if hasattr(obj, 'container') else None,
                        'width': data.m_Width if hasattr(data, 'm_Width') else 0,
                        'height': data.m_Height if hasattr(data, 'm_Height') else 0,
                        'format': str(data.m_TextureFormat) if hasattr(data, 'm_TextureFormat') else "Unknown",
                    }
                    texture_count += 1

                elif obj_type == "Sprite":
                    data = obj.read()
                    name = data.m_Name if hasattr(data, 'm_Name') else f"Sprite_{obj.path_id}"

                    all_sprites[f"{resource_file.name}/{name}"] = {
                        'file': resource_file.name,
                        'path_id': obj.path_id,
                        'container': obj.container if hasattr(obj, 'container') else None,
                    }
                    sprite_count += 1

                else:
                    # Track other object types for analysis
                    if obj_type not in all_objects:
                        all_objects[obj_type] = 0
                    all_objects[obj_type] += 1
                    other_count += 1

            print(f"    Textures: {texture_count}, Sprites: {sprite_count}, Other: {other_count}")

        except Exception as e:
            print(f"    Error loading {resource_file.name}: {e}")

print(f"\nTotal: {len(all_textures)} textures, {len(all_sprites)} sprites")
print(f"\nOther object types found:")
for obj_type, count in sorted(all_objects.items()):
    print(f"  {obj_type}: {count}")

# Keywords for filtering
alliance_keywords = ['alliance', 'guild', 'clan', 'logo', 'emblem', 'badge', 'totem', 'flag']
resource_keywords = ['item', 'resource', 'gold', 'gem', 'diamond', 'chest', 'coin', 'crystal', 'brick', 'ore', 'food', 'oil', 'steel', 'titanium']

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
        print(f"    Size: {info['width']}x{info['height']}")
        print(f"    Format: {info['format']}")
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
        print(f"    Size: {info['width']}x{info['height']}")
        print(f"    Format: {info['format']}")
else:
    print("  (None found with common keywords)")

# Save complete catalog
output_file = "resources_catalog.txt"
print(f"\n{'='*80}")
print(f"Saving complete catalog to: {output_file}")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("THE LAST WAR - RESOURCES CATALOG\n")
    f.write("="*80 + "\n\n")

    f.write("OBJECT TYPES:\n")
    f.write("-"*80 + "\n")
    for obj_type, count in sorted(all_objects.items()):
        f.write(f"{obj_type}: {count}\n")

    f.write("\n" + "="*80 + "\n")
    f.write("TEXTURES:\n")
    f.write("-"*80 + "\n\n")
    for name, info in sorted(all_textures.items()):
        f.write(f"{name}\n")
        f.write(f"  File: {info['file']}\n")
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
        f.write(f"  File: {info['file']}\n")
        if info['container']:
            f.write(f"  Container: {info['container']}\n")
        f.write(f"  Path ID: {info['path_id']}\n\n")

print(f"Complete! Found {len(alliance_matches)} potential alliance images")
print(f"         and {len(resource_matches)} potential resource/item images")
