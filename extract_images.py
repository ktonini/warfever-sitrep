#!/usr/bin/env python3
"""
The Last War Image Extractor

This script extracts embedded image files from The Last War game's Unity asset bundles.
It uses UnityPy to parse Unity asset files and extract texture data.

Note: This tool can only extract unencrypted Unity assets. The main game assets
in StreamingAssets/AssetBundles appear to use custom encryption and cannot be
extracted with this tool.

Version: 1.0.0
Author: k33bz
Created with assistance from: Claude Code (CLI version)
  Model: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
  Platform: Anthropic Claude Code CLI
  Date: 2025-10-08
License: MIT
"""

import UnityPy
import os
import sys
from pathlib import Path
import re
from PIL import Image

# ============================================================================
# Configuration
# ============================================================================

# Set the Unity version for proper asset parsing
# The Last War uses Unity 2019.4.40f1
UnityPy.config.FALLBACK_UNITY_VERSION = "2019.4.40f1"

# ============================================================================
# Auto-detect Latest Game Version
# ============================================================================

def find_latest_game_version():
    """
    Automatically finds the latest version of The Last War installed.

    Scans the game installation directory for all app-* folders and returns
    the path to the newest version based on version number sorting.

    Returns:
        Path: Path to the LastWar_Data directory of the newest version, or None if not found
    """
    # Get the base game installation directory
    game_base_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'TheLastWar'

    if not game_base_path.exists():
        return None

    # Find all directories matching the pattern "app-*"
    app_dirs = [d for d in game_base_path.iterdir() if d.is_dir() and d.name.startswith('app-')]

    if not app_dirs:
        return None

    # Sort directories by version number (extract version from "app-1.0.198" format)
    def extract_version(path):
        """Extract version tuple from app directory name for sorting."""
        match = re.search(r'app-(\d+)\.(\d+)\.(\d+)', path.name)
        if match:
            return tuple(map(int, match.groups()))
        return (0, 0, 0)

    # Sort by version number (newest first)
    app_dirs.sort(key=extract_version, reverse=True)

    # Return the path to LastWar_Data in the newest version
    latest_version = app_dirs[0] / 'LastWar_Data'

    return latest_version if latest_version.exists() else None

# Default path to the game data directory
# Automatically detects the newest installed version
default_game_path = find_latest_game_version()

# ============================================================================
# Command Line Argument Processing
# ============================================================================

# Check if a custom path was provided as a command line argument
# Usage: python extract_images.py [path_to_LastWar_Data]
if len(sys.argv) > 1:
    game_data_path = sys.argv[1]
elif default_game_path:
    # Use the auto-detected path
    game_data_path = str(default_game_path)
    print(f"Auto-detected game version: {default_game_path.parent.name}")
else:
    # Could not auto-detect, set to None for error handling below
    game_data_path = None

# Define the output directory where extracted images will be saved
output_dir = "extracted_images"

# ============================================================================
# Validation and Setup
# ============================================================================

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Validate that the game data path exists before proceeding
if not game_data_path or not os.path.exists(game_data_path):
    if not game_data_path:
        print(f"Error: Could not auto-detect The Last War installation")
        print(f"Please ensure the game is installed at: %LOCALAPPDATA%\\TheLastWar\\")
    else:
        print(f"Error: Game data path not found: {game_data_path}")
    print(f"\nUsage: python extract_images.py [path_to_LastWar_Data]")
    print(f"Example: python extract_images.py \"C:\\Users\\YourName\\AppData\\Local\\TheLastWar\\app-1.0.198\\LastWar_Data\"")
    sys.exit(1)

# ============================================================================
# Asset Loading
# ============================================================================

print(f"Loading Unity assets from {game_data_path}...")
print("Scanning for images...\n")

# Load all Unity assets from the game data directory
env = UnityPy.load(game_data_path)

# Counters
textures_found = 0
textures_extracted = 0

# ============================================================================
# Image Extraction Loop
# ============================================================================

# Iterate through all objects in the Unity environment
for obj in env.objects:
    # Check if the current object is a Texture2D asset
    if obj.type.name == "Texture2D":
        textures_found += 1

        # Read the texture object data
        data = obj.read()

        # Extract the texture name
        texture_name = data.m_Name if hasattr(data, 'm_Name') else f"Texture_{obj.path_id}"

        # Skip Unity's default UI elements and unnamed textures
        if not texture_name or "unity" in texture_name.lower() or texture_name.startswith("Texture_"):
            continue

        print(f"Found: {texture_name}")

        try:
            # Convert texture to PIL Image
            image = data.image

            if image:
                # Sanitize filename
                safe_name = "".join(c for c in texture_name if c.isalnum() or c in (' ', '-', '_')).strip()
                output_path = os.path.join(output_dir, f"{safe_name}.png")

                # Save the image
                image.save(output_path)

                print(f"  Extracted to: {output_path}")
                print(f"  Size: {image.width}x{image.height}")
                textures_extracted += 1

        except Exception as e:
            print(f"  Error extracting texture: {e}")

# ============================================================================
# Completion Summary
# ============================================================================

print(f"\n{'='*60}")
print(f"Extraction complete!")
print(f"Found {textures_found} textures")
print(f"Successfully extracted {textures_extracted} textures")
print(f"Output directory: {output_dir}")
print(f"\nNote: The main game assets in StreamingAssets/AssetBundles")
print(f"appear to use custom encryption and could not be extracted.")
