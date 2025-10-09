# Extraction Methods Comparison

Quick reference guide for choosing the right extraction method.

## 📊 Method Comparison

| Method | Success Rate | Time | Output | Difficulty |
|--------|--------------|------|--------|------------|
| **Memory Extraction** ⭐ | 100% | <1 min | CSV data | Easy |
| **Manual Screenshots** | 100% | 1.5-3 hrs | PNG images | Easy |
| **Automated Scraper** | 90% | 5-15 min | PNG + JSON | Medium |
| **Static Extraction** | 3% | 1 min | Limited PNG | Easy |
| **BepInEx Runtime** | 0% | N/A | N/A | Hard |

## 🎯 Choose Your Method

### For Alliance Data (Names, IDs, Power, Ranks)
**→ Use Memory Extraction** ([MEMORY_EXTRACTION.md](MEMORY_EXTRACTION.md))

**What you get:**
- Alliance abbreviations
- Full alliance names
- Unique alliance IDs (32-char hashes)
- Power values
- Current rankings
- CSV export

**Time:** Under 1 minute
**Difficulty:** Easy (just run script and scroll)

```bash
pip install psutil
python live_alliance_monitor.py
# Scroll through rankings in game
# Press Ctrl+C when done
```

---

### For Alliance Logos (Visual Assets)
**→ Use Manual Screenshots** ([SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md))

**What you get:**
- High-quality alliance logos
- Resource item icons (gold, gems, chests)
- Character portraits
- Building textures
- UI elements

**Time:** 1.5-3 hours
**Difficulty:** Easy (point and click)

**OR Use Automated Scraper** ([AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md))

**What you get:**
- Alliance logos auto-captured
- OCR-extracted text
- JSON metadata
- Faster but requires Tesseract OCR

**Time:** 5-15 minutes
**Difficulty:** Medium (setup + calibration)

---

## 📋 Detailed Breakdown

### ✅ Memory Extraction (BEST for data)

**Pros:**
- ✅ Fastest method (under 1 minute)
- ✅ No OCR errors
- ✅ Structured CSV output
- ✅ Unique alliance IDs
- ✅ Real-time data as you scroll
- ✅ No screenshots needed

**Cons:**
- ❌ Text data only (no images)
- ❌ Requires game running
- ❌ Only captures visible alliances

**Best for:**
- Database building
- Tracking alliance power over time
- Alliance research
- Data analysis

**Guide:** [MEMORY_EXTRACTION.md](MEMORY_EXTRACTION.md)

---

### ✅ Manual Screenshots (BEST for visual assets)

**Pros:**
- ✅ 100% success rate
- ✅ All visible assets
- ✅ No technical setup
- ✅ High quality PNGs
- ✅ Built-in Windows tools

**Cons:**
- ❌ Time consuming (1.5-3 hours)
- ❌ Manual process
- ❌ Requires organization afterward

**Best for:**
- Wiki/database images
- Game guides
- Asset collections
- When you need visuals

**Guide:** [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md)

---

### ✅ Automated Scraper (BEST for speed + logos)

**Pros:**
- ✅ Fast (5-15 minutes)
- ✅ Auto-scrolls and captures
- ✅ OCR extracts text
- ✅ JSON metadata output
- ✅ Batch processing

**Cons:**
- ❌ Requires Tesseract OCR install
- ❌ Initial calibration needed
- ❌ 90% success (some OCR errors)
- ❌ Mouse control automation

**Best for:**
- Quick alliance logo extraction
- When you need both images + text
- Repeated scans
- Leaderboard tracking

**Guide:** [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)

---

### ⚠️ Static Extraction (Limited)

**Pros:**
- ✅ Fast (1 minute)
- ✅ No game needed
- ✅ Easy Python script

**Cons:**
- ❌ Only 3% success
- ❌ 99 textures (96 Unity defaults)
- ❌ 3 game items only
- ❌ No alliance logos
- ❌ No resource items

**Best for:**
- Learning Unity extraction
- Checking for basic UI elements
- Not recommended for actual use

**Script:** `extract_images.py`

---

### ❌ BepInEx Runtime (Doesn't Work)

**Status:** Failed
- IL2CPP metadata missing
- Anti-cheat blocks initialization
- Unhollower won't load
- Il2CppInterop fails

**Not recommended**

**Details:** [RUNTIME_EXTRACTION.md](RUNTIME_EXTRACTION.md)

---

## 🚀 Quick Start Recommendations

### I want alliance data (CSV)
```bash
pip install psutil
python live_alliance_monitor.py
```
**Time:** <1 min | **Guide:** [MEMORY_EXTRACTION.md](MEMORY_EXTRACTION.md)

### I want alliance logos (PNG)
1. Press `Win+Shift+S` in game
2. Capture each logo
3. Save to folder
4. Run `organize_screenshots.ps1`

**Time:** 1.5-3 hrs | **Guide:** [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md)

### I want both (automated)
```bash
pip install pyautogui pillow pytesseract
# Install Tesseract OCR from github.com/UB-Mannheim/tesseract/wiki
python alliance_scraper.py
```
**Time:** 5-15 min | **Guide:** [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)

---

## 💡 Pro Tips

1. **Use memory extraction for tracking** - The unique alliance ID (32-char hash) never changes, even when alliance renames. Perfect for building historical databases.

2. **Combine methods** - Use memory extraction for data, manual screenshots for logos. Best of both worlds.

3. **OCR vs Memory** - Memory extraction has 100% accuracy for text. OCR has ~90% accuracy but also captures logos.

4. **One-time vs Repeated** - Memory extraction is best for repeated scans (just scroll and press Ctrl+C). Screenshots are one-time investments.

5. **Quality vs Speed** - Screenshots give highest quality. Automation gives speed. Memory gives perfect data.

---

## 📖 See Also

- [README.md](README.md) - Main documentation
- [MEMORY_EXTRACTION.md](MEMORY_EXTRACTION.md) - Real-time data extraction ⭐
- [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md) - Manual visual assets
- [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) - Automated scraping
- [CLAUDE.md](CLAUDE.md) - Development process
- [FINDINGS.md](FINDINGS.md) - What works and what doesn't
