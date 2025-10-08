# The Last War Asset Extractor

Tools for extracting image assets from The Last War game, including **static file extraction** and **runtime memory extraction**.

## 🎯 Two Extraction Methods

### Method 1: Static Extraction (Python) - Limited ⚠️
Extract from game files without running the game.
- ✅ Easy setup (just Python)
- ❌ **Only 3 game items** (encrypted assets inaccessible)
- ❌ **No alliance logos**

### Method 2: Runtime Extraction (BepInEx Plugin) - Comprehensive ⭐
Extract from game memory while running.
- ✅ **All alliance logos**
- ✅ **All resource items**
- ✅ **500-2000+ textures**
- ⚠️ Requires BepInEx installation

**👉 For alliance logos and resource items, use Method 2 (Runtime Extraction)**

See [RUNTIME_EXTRACTION.md](RUNTIME_EXTRACTION.md) for the runtime method.

---

## Method 1: Static Extraction (Limited)

### ⚠️ Limitations

**This method has limited functionality** due to The Last War's asset protection:

#### ✅ What CAN Be Extracted
- Unity default UI resources
- 3 basic game items: `item_icon_goldbrick`, trophy icon, gift button

#### ❌ What CANNOT Be Extracted
- **Alliance logos** - Stored in encrypted bundles
- **Most resource items** - Only 1 out of 100+ found
- **Character artwork** - Not accessible
- **Most in-game graphics** - Custom encrypted format

The game uses custom encryption for its main asset bundles.

## Why This Limitation Exists

The Last War implements asset protection:
- Custom bundle encryption in `StreamingAssets/AssetBundles`
- Runtime decryption (assets only accessible when game runs)
- Obfuscated `.bytes` files instead of standard Unity bundles
- Fragmented asset system with custom offset tables

## Installation

### Prerequisites
- Python 3.8 or higher
- The Last War installed on Windows

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/lastwar-asset-extractor.git
cd lastwar-asset-extractor
```

2. Install dependencies:
```bash
pip install UnityPy Pillow
```

## Usage

### Basic Usage (Auto-detect Game Path)

The extractor will automatically find your Last War installation:

```bash
python extract_images.py
```

### Manual Path (If Auto-detect Fails)

```bash
python extract_images.py "C:\Users\YourName\AppData\Local\TheLastWar\app-1.0.198\LastWar_Data"
```

### Output

Extracted images are saved to the `extracted_images` folder as PNG files.

## Exploration Tools

This repository includes several exploration scripts used during development:

- **`explore_images.py`** - Scans main Unity asset files for textures
- **`explore_assetbundles.py`** - Attempts to analyze asset bundles
- **`explore_raw_bundles.py`** - Examines .raw and .bytes files
- **`explore_resources.py`** - Explores Resources directory

These tools generate catalog files showing what assets are present (even if they can't be extracted).

## Technical Details

### Unity Version
The Last War uses Unity 2019.4.40f1

### Asset Structure
```
LastWar_Data/
├── globalgamemanagers.assets      # Basic Unity data
├── resources.assets                # Limited game resources
├── sharedassets0.assets            # Shared assets
├── Resources/                      # Unity default resources
└── StreamingAssets/
    └── AssetBundles/               # Encrypted game assets ❌
        ├── BundleFragment0.bytes   # Main assets (encrypted)
        ├── gameres                 # Game resources (encrypted)
        └── ...
```

### How It Works

1. **Auto-detection**: Scans `%LOCALAPPDATA%\TheLastWar` for the latest version
2. **Asset Loading**: Uses UnityPy to parse Unity asset files
3. **Texture Extraction**: Converts Unity textures to PIL images
4. **Export**: Saves as PNG files

### Supported Asset Types
- Texture2D (converted to PNG)
- Unity's default UI resources
- Accessible game textures (very limited)

## Method 2: Runtime Extraction ⭐

**For extracting alliance logos and resource items, use the BepInEx plugin method!**

See **[RUNTIME_EXTRACTION.md](RUNTIME_EXTRACTION.md)** for complete instructions.

### Quick Overview

1. Install BepInEx (Unity mod framework)
2. Build and install the plugin
3. Run The Last War
4. Press **F10** to extract all loaded textures
5. Find 500-2000+ textures organized by category

**Success rate**: ~95% (vs ~3% for static extraction)

### What You'll Get
- ✅ All alliance logos
- ✅ All resource item icons
- ✅ Character portraits
- ✅ Building textures
- ✅ UI elements
- ✅ Everything loaded in memory!

## Development

This tool was developed to explore Unity asset extraction techniques. While it successfully demonstrates the basics, The Last War's encryption prevents access to most interesting assets.

### Dependencies
- **UnityPy** (1.23.0+) - Unity asset parsing
- **Pillow** - Image processing and export
- **Python 3.8+** - Runtime environment

## Known Issues

1. **Encrypted Bundles**: Cannot extract from StreamingAssets/AssetBundles
2. **Limited Output**: Only extracts Unity defaults and basic UI elements
3. **No Alliance Logos**: Protected assets not accessible

## Credits

- **UnityPy**: Unity asset extraction library
- **Claude Code**: Development assistance (Claude Sonnet 4.5)

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational purposes. Respect the game developer's intellectual property rights. Extracting game assets may violate the Terms of Service.

## Related Projects

- [lastwar-font-extractor](https://github.com/yourusername/lastwar-font-extractor) - Successfully extracts fonts from The Last War

## See Also

For full development details and technical challenges, see [CLAUDE.md](CLAUDE.md).
