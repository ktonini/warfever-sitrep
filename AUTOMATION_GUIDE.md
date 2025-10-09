# Automated Asset Extraction Guide

## Overview

Automated scripts to capture alliance logos and ranking data using mouse/keyboard automation and OCR.

### What's Automated
- ✅ **Alliance Logo Extraction** - Automatically scrolls and captures logos
- ✅ **Alliance Name OCR** - Reads alliance names using Tesseract
- ✅ **Ranking Data Capture** - Scrapes leaderboard data
- ✅ **Power Level Extraction** - OCR for power/ranking numbers
- ✅ **Batch Processing** - Capture 50-500+ entries automatically

## Prerequisites

### 1. Install Python Packages
```bash
pip install pyautogui pillow pytesseract
```

### 2. Install Tesseract OCR (Required for text extraction)

**Windows:**
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Run `tesseract-ocr-w64-setup-5.3.x.exe`
3. Install to default location: `C:\Program Files\Tesseract-OCR`
4. The script will auto-detect it

**Verify installation:**
```bash
tesseract --version
```

### 3. Launch The Last War
Make sure the game is running in windowed or borderless mode (not fullscreen).

## Method 1: Alliance Logo Scraper

### Quick Start

```bash
python alliance_scraper.py
```

### How It Works

1. **Automatic Game Detection**
   - Finds The Last War window
   - Brings it to foreground

2. **Interactive Calibration** (First run only)
   - You'll have 5 seconds to hover mouse over each UI element:
     - Alliance menu button
     - First alliance in list
     - Alliance logo area
     - Alliance name text
     - Ranking/power text
     - Scroll area
   - Positions saved to `calibration.json` for reuse

3. **Automated Scraping**
   - Clicks alliance menu
   - Captures each alliance entry:
     - Logo (100x100 PNG)
     - Name (OCR extracted)
     - Rank/Power (OCR extracted)
     - Full screenshot
   - Scrolls automatically
   - Saves all data to JSON

### Output Structure

```
extracted-alliances/
├── logos/
│   ├── alliance_001_20251008_223000.png
│   ├── alliance_002_20251008_223001.png
│   └── ...
├── screenshots/
│   ├── alliance_001_20251008_223000.png
│   └── ...
├── data/
│   └── alliance_data_20251008_223000.json
└── calibration.json
```

### Example JSON Output

```json
[
  {
    "index": 0,
    "timestamp": "2025-10-08T22:30:15",
    "logo_file": "extracted-alliances/logos/alliance_001_20251008_223000.png",
    "name": "Dragon Alliance",
    "rank_power": "Rank: 1 | Power: 125.5M",
    "screenshot": "extracted-alliances/screenshots/alliance_001_20251008_223000.png"
  },
  ...
]
```

### Configuration

**Number of alliances to scrape:**
- Default: 50
- You'll be prompted on startup
- Or edit in code: `scraper.run(num_alliances=100)`

**Scroll speed:**
- Adjust `pyautogui.PAUSE` in code (default: 0.5 seconds)
- Slower = more reliable, faster = quicker scraping

## Method 2: Ranking Data Scraper

### Quick Start

```bash
python ranking_scraper.py
```

### How It Works

1. **Manual Setup**
   - Navigate to any ranking/leaderboard screen
   - Ensure rankings are visible
   - Press ENTER to start

2. **Automated Capture**
   - Captures visible ranking rows (~6 at a time)
   - OCR extracts: rank number, player name, power, etc.
   - Scrolls down automatically
   - Repeats until target number reached

3. **Output**
   - Screenshots of each ranking row
   - JSON with OCR data
   - Timestamp for each entry

### Output Structure

```
extracted-rankings/
├── rank_001_20251008_223500.png
├── rank_002_20251008_223501.png
├── ...
└── rankings_20251008_223500.json
```

### Example JSON Output

```json
[
  {
    "rank": 1,
    "screenshot": "extracted-rankings/rank_001_20251008_223500.png",
    "ocr_text": "1 PlayerName 156.2M",
    "timestamp": "2025-10-08T22:35:12"
  },
  ...
]
```

## Tips for Best Results

### 1. Game Window Position
- **Windowed mode recommended** (not fullscreen)
- Position window to center or left side of screen
- Keep window size consistent between runs

### 2. Calibration Accuracy
- Take your time during calibration
- Hover precisely over elements
- Recalibrate if OCR results are poor:
  ```bash
  rm extracted-alliances/calibration.json
  python alliance_scraper.py
  ```

### 3. OCR Accuracy
The script already extracted The Last War's fonts! For best OCR:
- Ensure text is not overlapped by UI
- Use highest game graphics settings
- Avoid capturing during animations
- Clean screenshots = better OCR

### 4. Failsafe Protection
**Emergency stop:**
- Move mouse to any screen corner → Script stops immediately
- Or press `Ctrl+C` in terminal

### 5. Speed vs Accuracy
**Faster scraping:**
```python
pyautogui.PAUSE = 0.2  # Faster but may miss elements
```

**More reliable:**
```python
pyautogui.PAUSE = 1.0  # Slower but more accurate
```

## Advanced Usage

### Custom Calibration

Edit `calibration.json` manually with exact pixel coordinates:

```json
{
  "alliance_button": [1200, 100],
  "first_alliance": [640, 300],
  "logo_area": [200, 350],
  "name_area": [400, 350],
  "rank_area": [700, 350],
  "scroll_area": [640, 500]
}
```

### Batch Processing

Scrape multiple alliance pages:

```python
from alliance_scraper import AllianceScraper

scraper = AllianceScraper()
scraper.run(num_alliances=200)  # Top 200 alliances
```

### OCR Post-Processing

Extract structured data from OCR text:

```python
import json
import re

with open('extracted-alliances/data/alliance_data_*.json') as f:
    data = json.load(f)

for alliance in data:
    # Parse rank and power
    text = alliance['rank_power']
    rank_match = re.search(r'Rank:\s*(\d+)', text)
    power_match = re.search(r'Power:\s*([\d.]+[KMB]?)', text)

    if rank_match:
        alliance['rank'] = int(rank_match.group(1))
    if power_match:
        alliance['power'] = power_match.group(1)

# Save cleaned data
with open('cleaned_alliance_data.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## Troubleshooting

### OCR Not Working

**Issue**: Empty or garbage text from OCR

**Solutions:**
1. Verify Tesseract installed:
   ```bash
   tesseract --version
   ```

2. Check Tesseract path in script:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

3. Test OCR manually:
   ```bash
   tesseract test_image.png output
   ```

### Script Clicks Wrong Location

**Issue**: Mouse clicks wrong UI elements

**Solutions:**
1. Recalibrate: Delete `calibration.json` and run again
2. Verify game window is active and unobscured
3. Check screen resolution matches calibration
4. Adjust coordinates manually in `calibration.json`

### Game Window Not Found

**Issue**: `Game window not found`

**Solutions:**
1. Ensure The Last War is running
2. Check window title contains "LastWar" or "The Last War"
3. Manually activate game window before running script
4. Try fullscreen → windowed mode

### Script Too Fast/Slow

**Adjust timing:**
```python
# In the script:
pyautogui.PAUSE = 0.5  # Global pause (0.1-2.0 seconds)
time.sleep(1)          # Specific delays (increase as needed)
```

### Scroll Not Working

**Issue**: List doesn't scroll or scrolls too far

**Solutions:**
1. Calibrate scroll area more precisely
2. Adjust scroll amount:
   ```python
   pyautogui.scroll(-3)  # Try -1 to -5
   ```
3. Click list area first to focus it

## Performance

### Estimated Timing

| Task | Count | Time | Rate |
|------|-------|------|------|
| Alliance scraping | 50 | 5 min | 10/min |
| Alliance scraping | 200 | 20 min | 10/min |
| Ranking scraping | 50 | 3 min | 16/min |
| Ranking scraping | 100 | 6 min | 16/min |

### Optimization

**Parallel capture** (advanced):
```python
# Capture multiple regions simultaneously
from concurrent.futures import ThreadPoolExecutor

def capture_all_regions():
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(capture_region, x, y, w, h)
            for x, y, w, h in regions
        ]
        return [f.result() for f in futures]
```

## Integration with Font Extraction

The Last War fonts have been extracted to:
- `Perfect DOS VGA 437.ttf`
- `LiberationSans.ttf`

**Train Tesseract with game fonts** for better OCR:

1. Create `.traineddata` file from game fonts
2. Place in Tesseract tessdata folder
3. Use custom language:
   ```python
   pytesseract.image_to_string(img, lang='lastwar')
   ```

Tutorial: https://tesseract-ocr.github.io/tessdoc/Training-Tesseract.html

## Safety Notes

1. **Anti-Cheat**: Mouse automation is undetectable (operates at OS level)
2. **No game modifications**: Scripts only read screen and control mouse
3. **Failsafe enabled**: Corner abort always available
4. **Rate limiting**: Built-in delays prevent spam

## Next Steps

After scraping:

1. **Clean OCR data** - Fix common misreads
2. **Deduplicate** - Remove duplicate entries
3. **Analyze** - Find patterns in alliance power/rankings
4. **Visualize** - Create charts from ranking data
5. **Export** - Convert to CSV/Excel for analysis

---

**Note**: These scripts provide semi-automated extraction. Some manual setup (calibration) is required on first run, but subsequent runs are fully automated.
