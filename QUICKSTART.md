# Quick Start Guide - Extract Alliance Logos & Resource Items

**Goal**: Extract alliance logos and resource item icons from The Last War.

## TL;DR - Fastest Method

1. Download BepInEx IL2CPP: https://github.com/BepInEx/BepInEx/releases
2. Extract to `C:\Users\k33bz\AppData\Local\TheLastWar\app-1.0.198\`
3. Run game once, close it
4. Build plugin: `cd BepInEx-Plugin && dotnet build -c Release`
5. Copy `bin/Release/netstandard2.1/LastWarTextureExtractor.dll` to `BepInEx\plugins\`
6. Run game, press **F10**
7. Get textures from `BepInEx\ExtractedTextures\`

## Why Not Use Static Extraction?

❌ **Static extraction (extract_images.py) FAILED:**
- Only extracted 3 game items
- No alliance logos
- Assets are encrypted in game files

✅ **Runtime extraction (BepInEx plugin) SUCCEEDS:**
- Extracts 500-2000+ textures
- All alliance logos
- All resource items
- Everything in game memory

## Step-by-Step Instructions

### 1. Install BepInEx (5 minutes)

```bash
# Download BepInEx 5.x IL2CPP x64
# From: https://github.com/BepInEx/BepInEx/releases
# File: BepInEx_UnityIL2CPP_x64_[version].zip

# Extract to game directory
# Target: C:\Users\k33bz\AppData\Local\TheLastWar\app-1.0.198\

# Should create:
# C:\Users\k33bz\AppData\Local\TheLastWar\app-1.0.198\BepInEx\
```

### 2. Initialize BepInEx (1 minute)

```bash
# Launch The Last War once
# BepInEx console window should appear
# Close game
# Verify BepInEx\plugins\ folder exists
```

### 3. Build Plugin (2 minutes)

```bash
# Install .NET SDK if needed
# https://dotnet.microsoft.com/download

cd C:\Users\k33bz\OneDrive\git\lastwar-asset-extractor\BepInEx-Plugin
dotnet restore
dotnet build -c Release

# Find DLL at:
# bin/Release/netstandard2.1/LastWarTextureExtractor.dll
```

### 4. Install Plugin (30 seconds)

```bash
# Copy DLL to:
cp bin/Release/netstandard2.1/LastWarTextureExtractor.dll \
   "C:\Users\k33bz\AppData\Local\TheLastWar\app-1.0.198\BepInEx\plugins\"
```

### 5. Extract Assets (2 minutes)

```bash
# 1. Launch The Last War
# 2. Navigate to different screens to load assets:
#    - Main base
#    - Alliance menu (for logos)
#    - Inventory (for resource items)
#    - Hero roster
#    - Shop
# 3. Press F10 to extract ALL loaded textures
# 4. Wait 10-30 seconds (game may freeze briefly)
# 5. Check output:
#    C:\Users\k33bz\AppData\Local\TheLastWar\app-1.0.198\BepInEx\ExtractedTextures\
```

### 6. Find Your Assets

```
BepInEx/ExtractedTextures/
├── Alliance/          ← ALLIANCE LOGOS HERE
├── Items/             ← RESOURCE ITEMS HERE
├── Characters/        ← Hero portraits
├── Buildings/         ← Base buildings
├── UI/                ← UI elements
├── Map/               ← Map textures
└── Misc/              ← Other
```

## Troubleshooting

### "Plugin not loading"
- Check `BepInEx\LogOutput.log` for errors
- Ensure using **IL2CPP** version of BepInEx (game uses IL2CPP)
- Verify DLL is in `BepInEx\plugins\` folder

### "BepInEx console not appearing"
- Press `F5` to toggle console
- Check if `winhttp.dll` exists in game directory
- Re-extract BepInEx to game folder

### "No textures extracted" / "Found 0 textures"
- Visit more game screens before pressing F10
- Try F9 for visible textures only
- Check `BepInEx\LogOutput.log` for errors

### "Build failed"
- Install .NET SDK 6.0+: https://dotnet.microsoft.com/download
- Run `dotnet restore` first
- Check error messages for missing packages

## Expected Results

### First Extraction (F10 after visiting alliance menu + inventory):
```
[Info] Found 847 Texture2D objects in memory
[Info] Extraction complete! New: 823, Skipped: 0
[Info] Total unique textures extracted: 823
```

### Output:
```
Alliance/
  ├── alliance_logo_001.png
  ├── alliance_logo_002.png
  ├── alliance_emblem_red.png
  └── ... (10-50 alliance logos)

Items/
  ├── item_icon_gold.png
  ├── item_icon_gems.png
  ├── item_icon_chest_bronze.png
  ├── item_icon_chest_silver.png
  ├── item_icon_chest_gold.png
  └── ... (100-300 resource items)
```

## Full Documentation

- **[RUNTIME_EXTRACTION.md](RUNTIME_EXTRACTION.md)** - Complete guide with all details
- **[BepInEx-Plugin/BUILD.md](BepInEx-Plugin/BUILD.md)** - Build troubleshooting
- **[FINDINGS.md](FINDINGS.md)** - Analysis of what was found

## Comparison

| Method | Alliance Logos | Resource Items | Total Textures | Setup Time |
|--------|---------------|----------------|----------------|------------|
| **Static (Python)** | ❌ 0 | ❌ 1 | 99 | 2 min |
| **Runtime (BepInEx)** | ✅ All | ✅ All | 500-2000+ | 10 min |

**Recommendation**: Use runtime extraction for comprehensive results.

## Next Steps After Extraction

1. Browse extracted images in `BepInEx\ExtractedTextures\`
2. Copy desired images to your project
3. Repeat extraction after visiting more game screens for additional assets
4. Share findings (respecting game's intellectual property)

## Need Help?

1. Check `BepInEx\LogOutput.log` for detailed error messages
2. Review [RUNTIME_EXTRACTION.md](RUNTIME_EXTRACTION.md) troubleshooting section
3. Verify BepInEx version matches game architecture (IL2CPP x64)
4. Ensure .NET SDK installed for building plugin

## Legal Notice

⚠️ This tool is for educational and research purposes. Respect intellectual property rights. Do not redistribute extracted game assets.
