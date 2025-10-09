# The Last War Asset & Data Extractor

Complete toolkit for extracting game assets and real-time data from The Last War.

## 🎯 Extraction Methods

### ✅ **NEW: Real-Time Memory Extraction - WORKS!**
**Live data extraction from game memory** - Extract alliance data as you play!
- ✅ **Alliance names** - Both short and full names
- ✅ **Alliance IDs** - Unique identifiers (32-char hashes)
- ✅ **Power values** - Real-time power numbers
- ✅ **Rank data** - Current rankings (1-50)
- ✅ **No screenshots needed** - Direct memory access
- ✅ **CSV export** - Ready-to-use data format

**👉 See [MEMORY_EXTRACTION.md](MEMORY_EXTRACTION.md) for setup & usage**

After extensive testing of static extraction and BepInEx runtime, **we've successfully developed working memory extraction** plus manual screenshot capture for visual assets.

### ✅ Method 1: Automated Mouse/OCR Scraper (NEW!) - 90% Success
**Automated extraction using mouse control + OCR**
- ✅ **Alliance logos** - Auto-scrolls and captures all logos
- ✅ **Alliance names** - OCR extracts names using game fonts
- ✅ **Ranking data** - Scrapes leaderboards automatically
- ✅ **Batch processing** - 50-500+ entries in minutes
- ✅ **JSON output** - Structured data with metadata
- ⚠️ **Requires Tesseract OCR** - One-time install

**👉 See [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) for setup & usage**

### ✅ Method 2: Manual Screenshots - 100% Success
Extract assets by capturing screenshots while playing.
- ✅ **100% success rate** - Works for all visible assets
- ✅ **All resource items** - Gold, gems, materials, chests
- ✅ **Character portraits** - Hero menu screenshots
- ✅ **Building icons** - Base view captures
- ✅ **No technical requirements** - Uses built-in Windows tools
- ✅ **No anti-cheat issues** - Just screen capture

**👉 See [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md) for complete instructions**

### ⚠️ Method 3: Static Extraction (Python) - 3% Success
Extract from game files without running the game.
- ✅ Easy setup (just Python)
- ❌ **Only 3 game items** (encrypted assets inaccessible)
- ❌ **No alliance logos**
- ❌ **No resource items** (99% encrypted)

### ❌ Method 4: Runtime Extraction (BepInEx) - 0% Success
Extract from game memory while running.
- ❌ **Blocked by anti-cheat** - AntiCheatExpert detects mods
- ❌ **No IL2CPP metadata** - Required files encrypted/missing
- ❌ **BepInEx won't initialize** - Unhollower/Il2CppInterop failures
- ❌ **Debuggers blocked** - RenderDoc, Cheat Engine blocked

**Status**: Not functional due to professional-grade anti-modding protection.

---

## Quick Start (Memory Extraction)

### 1. Install Python Dependency

```bash
pip install psutil
```

### 2. Launch Game & Open Rankings

1. Start The Last War
2. Navigate to Alliance Menu → Rankings
3. Keep window visible

### 3. Run Live Monitor

```bash
python live_alliance_monitor.py
```

### 4. Scroll Through Rankings

- Slowly scroll through the alliance list
- Scanner captures data in real-time
- Watch console for alliance count

### 5. Save Data

- Press `Ctrl+C` to stop scanning
- Data automatically saves to `live_alliance_data.csv`

### Output Example

```csv
Rank,Short Name,Full Name,Power,Alliance ID
1,"UvvU","veni vidi vici",6435764372,"37ecf329739c4b61bf9da597829fa993"
2,"ORCE","Omega Force",6387057595,"40bdeadf9a184d7da54c7dc4a07feeac"
```

**Full guide**: [MEMORY_EXTRACTION.md](MEMORY_EXTRACTION.md)

---

## Quick Start (Automated Scraper)

### 1. Install Dependencies

```bash
pip install pyautogui pillow pytesseract
```

### 2. Install Tesseract OCR

**Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

Install to: `C:\Program Files\Tesseract-OCR`

### 3. Run Alliance Scraper

```bash
python alliance_scraper.py
```

**First Run**: Interactive calibration (hover over UI elements)

**Subsequent Runs**: Fully automated

### Output
- Alliance logos (PNG)
- Alliance names (OCR)
- Ranking data (JSON)
- 50-500+ entries in minutes

**Full guide**: [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)

---

## Quick Start (Manual Screenshots)

### 1. Setup Screenshot Tool

**Option A: Windows Snipping Tool (Built-in)**
- Press `Win+Shift+S` to capture
- Select region and save as PNG

**Option B: ShareX (Recommended)**
- Download from https://getsharex.com/
- Configure hotkey and auto-save folder
- Much faster for batch captures

### 2. Extract Assets

1. Launch The Last War
2. Navigate to asset location:
   - **Alliance logos**: Alliance Menu → List
   - **Resources**: Inventory → Items/Materials
   - **Chests**: Inventory → Chests
   - **Heroes**: Heroes Menu
   - **Buildings**: Base View (zoom in)

3. Take screenshots using `Win+Shift+S`

4. Organize using provided PowerShell script:
   ```powershell
   .\organize_screenshots.ps1
   ```

### Expected Results
- **210-420+ unique assets** in 1.5-3 hours
- Organized into categories automatically
- High-quality PNG images ready to use

**See full guide**: [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md)

---

## Why Automated Extraction Fails

The Last War implements **professional-grade anti-modding protection**:

| Protection Layer | Impact |
|-----------------|--------|
| **Asset Bundle Encryption** | All bundles in StreamingAssets encrypted |
| **IL2CPP Metadata Encryption** | No global-metadata.dat file |
| **Runtime Decryption** | Assets decrypted on-the-fly in memory |
| **AntiCheatExpert** | Blocks RenderDoc, Cheat Engine, debuggers |
| **No Metadata Signature** | IL2CPP signature (AF 1B B1 FA) not in memory |
| **BepInEx Incompatibility** | Both Unhollower and Il2CppInterop fail |

### What We Tested

✅ **Static Extraction (UnityPy)**
- Result: 99 textures (96 Unity defaults, 3 game items)
- Success: 3%

❌ **BepInEx 6.0-pre.1 (Unhollower)**
- Error: `Could not load Il2Cppmscorlib, Version=3.7.1.6`
- Result: Won't initialize

❌ **BepInEx 6.0-pre.2 (Il2CppInterop)**
- Error: `DirectoryNotFoundException: global-metadata.dat`
- Result: Won't initialize

❌ **Memory Dumping**
- Searched entire game memory for IL2CPP metadata signature
- Result: Not found (encrypted in memory)

❌ **Graphics Debugging (RenderDoc)**
- Error: "Using hacking tools and would close the game"
- Result: Blocked by AntiCheatExpert

❌ **Il2CppDumper**
- Error: "Metadata file not found or encrypted"
- Result: Cannot extract metadata from GameAssembly.dll

### Conclusion
After 10+ hours of testing every known Unity asset extraction method, **manual screenshots are the only reliable approach**.

---

## Static Extraction (Limited)

If you want to try static extraction (3% success rate):

### Installation

```bash
pip install UnityPy Pillow
```

### Usage

```bash
python extract_images.py
```

Auto-detects game path from `%LOCALAPPDATA%\TheLastWar`

### What You'll Get
- 99 textures total:
  - 96 Unity default UI resources
  - 3 game items: `item_icon_goldbrick`, trophy, gift button

### What You Won't Get
- ❌ Alliance logos (encrypted)
- ❌ Resource items (99% encrypted)
- ❌ Character artwork (encrypted)
- ❌ Building textures (encrypted)

---

## Repository Structure

```
lastwar-asset-extractor/
├── MEMORY_EXTRACTION.md         # Live memory extraction guide ⭐ NEW!
├── live_alliance_monitor.py     # Real-time memory scanner ⭐ NEW!
├── comprehensive_alliance_scanner.py  # One-shot memory scanner ⭐ NEW!
├── scan_by_alliance_id.py       # ID-based scanner ⭐ NEW!
├── scan_for_rankings.py         # Ranking debug scanner ⭐ NEW!
├── AUTOMATION_GUIDE.md          # Automated scraper guide
├── alliance_scraper.py          # Auto alliance logo scraper
├── ranking_scraper.py           # Auto ranking data scraper
├── SCREENSHOT_GUIDE.md          # Manual extraction guide
├── organize_screenshots.ps1     # Auto-organize script
├── extract_images.py            # Static extractor (limited)
├── README.md                    # This file
├── CLAUDE.md                    # Development log
├── FINDINGS.md                  # Extraction results analysis
├── RUNTIME_EXTRACTION.md        # BepInEx attempt (failed)
├── live_alliance_data.csv       # Memory extraction output ⭐
├── extracted-alliances/         # Automated scraper output
│   ├── logos/                   # Alliance logos (PNG)
│   ├── screenshots/             # Full screenshots
│   ├── data/                    # JSON data with OCR
│   └── calibration.json         # UI positions
├── extracted-rankings/          # Ranking scraper output
├── extracted-screenshots/       # Manual screenshots
└── organized-assets/            # Organized output
    ├── alliance-logos/
    ├── resources/
    ├── chests/
    ├── buildings/
    ├── heroes/
    └── ui/
```

## Development Notes

### Technical Details
- **Unity Version**: 2019.4.40f1
- **IL2CPP**: Custom implementation without standard metadata
- **Asset Bundles**: Custom encryption (not standard Unity)
- **Anti-Cheat**: AntiCheatExpert active protection

### Asset Files Analyzed
- `globalgamemanagers.assets` - Basic Unity data
- `resources.assets` - Limited resources
- `sharedassets0.assets` - Shared assets
- `StreamingAssets/AssetBundles/*` - All encrypted ❌
- `GameAssembly.dll` - IL2CPP binary (no metadata)

### Tools Tested
- UnityPy - Static extraction
- BepInEx 6.0-pre.1 - Unhollower (failed)
- BepInEx 6.0-pre.2 - Il2CppInterop (failed)
- Il2CppDumper - Metadata extraction (failed)
- RenderDoc - Graphics debugging (blocked)
- Memory scanners - Metadata search (not found)
- Il2CppMemoryDumper - Memory dump (Android only)

### Memory Analysis Results
- Scanned entire LastWar.exe process memory
- Searched for IL2CPP metadata signature (`AF 1B B1 FA`)
- Result: Signature not present (encrypted on-the-fly)

## Credits

- **UnityPy**: Unity asset extraction library
- **ShareX**: Screenshot automation tool
- **Claude Code**: Development assistance

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational purposes. Respect the game developer's intellectual property rights. Extracting game assets may violate the Terms of Service.

## Related Projects

- [lastwar-font-extractor](../lastwar-font-extractor) - Successfully extracts fonts from The Last War

## See Also

- [EXTRACTION_METHODS.md](EXTRACTION_METHODS.md) - 📊 **Compare all methods & choose the right one**
- [MEMORY_EXTRACTION.md](MEMORY_EXTRACTION.md) - ⭐ **Real-time data extraction (WORKS!)**
- [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md) - Manual visual asset extraction
- [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) - Automated screenshot scraping
- [CLAUDE.md](CLAUDE.md) - Full development log
- [FINDINGS.md](FINDINGS.md) - Extraction results analysis
- [RUNTIME_EXTRACTION.md](RUNTIME_EXTRACTION.md) - BepInEx attempt documentation
