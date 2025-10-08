# CLAUDE.md

## Project Overview
This project attempts to extract image assets (alliance logos, resource items, etc.) from The Last War game using Unity asset extraction tools.

## Development Process

### Initial Analysis
- Searched for image files in the game directory structure
- Located game data in `app-1.0.198\LastWar_Data` directory
- Identified multiple potential asset locations:
  - Main Unity asset files (globalgamemanagers.assets, resources.assets, sharedassets0.assets)
  - StreamingAssets/AssetBundles directory
  - Resources directory

### Technology Selection
- Chose **UnityPy** for programmatic Unity asset extraction
- UnityPy is a Python library that can parse Unity asset files and extract embedded resources
- Built upon the successful font extraction project

### Asset Discovery Process

#### Phase 1: Main Asset Files
- Scanned the main Unity asset files in `LastWar_Data`
- Found 110 textures and 21 sprites
- Identified limited game-specific content:
  - `item_icon_goldbrick` (154x154)
  - `icon_od_LXchongzhihuodongjiangbei` (154x154)
  - Various UI elements

#### Phase 2: StreamingAssets Investigation
- Discovered `StreamingAssets/AssetBundles` directory containing:
  - `BundleFragment0.bytes` (13MB)
  - `BundleOffsetTable.bytes` (20KB)
  - Asset bundle files: `gameres`, `packageres`, `download`, `datatable`, `dllres`, `lua`
  - Raw bundle files: `gameres_raw_1587206357.raw`, `gameres_raw_3763444104.raw`

#### Phase 3: Bundle Analysis Results
- Attempted to load asset bundles with UnityPy
- **Discovery**: Asset bundles appear to be encrypted or use a custom format
- Standard UnityPy loading techniques returned 0 textures/sprites from all bundle files
- Conclusion: Main game assets (alliance logos, resource items) are protected

#### Phase 4: Resources Directory
- Examined Unity Resources folder
- Found only Unity's default UI resources:
  - 41 default textures (buttons, scrollbars, UI elements)
  - 1 sprite
  - No game-specific content

### Key Findings

#### Successfully Accessible Assets
1. **Limited UI textures** in main asset files
2. **Unity default resources** (not game-specific)
3. **Basic game UI elements** (search icons, etc.)

#### Inaccessible Assets (Encrypted/Protected)
1. **Alliance logos** - Not found in accessible assets
2. **Resource item icons** - Only `item_icon_goldbrick` found
3. **Main game textures** - Stored in encrypted bundles

### Technical Challenges

#### Challenge 1: Custom Bundle Encryption
- **Issue**: Asset bundles in StreamingAssets use custom encryption/compression
- **Evidence**:
  - Large bundle files (13MB BundleFragment0.bytes) but UnityPy extracts 0 assets
  - `.bytes` extension suggests obfuscation
  - Offset table indicates custom loading mechanism
- **Limitation**: Cannot decrypt without reverse engineering the game's bundle loader

#### Challenge 2: Limited Asset Access
- **Issue**: Most game assets are not stored in standard Unity asset files
- **Finding**: Game likely downloads and decrypts assets at runtime
- **Impact**: Static extraction tools can only access Unity's built-in resources

### Results

#### Extracted Assets
- Successfully created extraction tool for accessible Unity assets
- Limited to:
  - Unity default UI resources
  - A few game UI elements
  - No alliance logos or comprehensive resource item icons

#### Tools Created
1. **explore_images.py** - Scans main Unity asset files
2. **explore_assetbundles.py** - Attempts to load asset bundles
3. **explore_raw_bundles.py** - Analyzes .raw and .bytes files
4. **explore_resources.py** - Examines Resources directory
5. **extract_images.py** - Extracts accessible textures to PNG format

## Technical Details

### Asset File Structure
```
LastWar_Data/
├── globalgamemanagers.assets
├── resources.assets
├── sharedassets0.assets
├── Resources/
│   ├── unity default resources
│   └── unity_builtin_extra
└── StreamingAssets/
    └── AssetBundles/
        ├── BundleFragment0.bytes (encrypted)
        ├── BundleOffsetTable.bytes
        ├── gameres (encrypted)
        ├── packageres (encrypted)
        ├── gameres_raw_*.raw (encrypted)
        └── ...
```

### Unity Version
- The Last War uses **Unity 2019.4.40f1**
- Version detected from `globalgamemanagers` file
- Set via `UnityPy.config.FALLBACK_UNITY_VERSION`

### Image Format Detection
Images are extracted and converted to PNG using PIL (Pillow):
- UnityPy provides texture data in various Unity formats
- `.image` property converts to PIL Image object
- Saved as PNG for maximum compatibility

## Limitations

### What Cannot Be Extracted
1. **Alliance Logos** - Stored in encrypted bundles
2. **Most Resource Items** - Protected in custom bundle format
3. **Character Art** - Not accessible via standard extraction
4. **In-Game Graphics** - Encrypted in BundleFragment files

### Why Extraction Failed
The Last War implements several protection mechanisms:
- Custom bundle encryption/obfuscation
- `.bytes` file extensions to hide Unity bundles
- Runtime decryption (assets decoded when game runs)
- Fragmented bundle system with offset tables

### Alternative Approaches (Not Implemented)
1. **Runtime Memory Extraction** - Capture textures from game memory while running
2. **Network Traffic Analysis** - Intercept asset downloads
3. **Reverse Engineering** - Decode the custom bundle format
4. **Screen Capture** - Extract visuals from running game

## Dependencies
- Python 3.13
- UnityPy 1.23.0
- Pillow (PIL fork) for image export
- Additional: lz4, brotli, texture2ddecoder, etcpak, astc-encoder-py

## Usage
See README.md for usage instructions.

## Conclusion
While this project successfully demonstrates Unity asset extraction techniques, The Last War's use of custom encryption prevents extraction of alliance logos and most resource items. The tools created can extract basic UI elements but not the main game assets.
