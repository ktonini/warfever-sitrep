# Real-Time Memory Extraction Guide

## Overview

Extract live alliance data directly from The Last War game memory as you play. No screenshots needed - just scroll through rankings and capture everything automatically.

## What You Can Extract

- ✅ **Alliance Names** - Both abbreviations and full names
- ✅ **Alliance IDs** - Unique 32-character hex identifiers
- ✅ **Power Values** - Real-time power numbers (1B-10B range)
- ✅ **Rank Data** - Current rankings (1-50)
- ✅ **CSV Export** - Structured data ready to use

## How It Works

The game stores alliance data in memory in a specific pattern:

```
[ABBR] [32-char-hash] [number] [FULL_NAME]
```

Example from memory:
```
UvvU 37ecf329739c4b61bf9da597829fa993 2veni vidi vici8
```

The scanner:
1. Reads game process memory in real-time
2. Searches for this pattern using regex
3. Extracts rank numbers (stored as int32) nearby
4. Finds power values (stored as uint64) in vicinity
5. Merges data and exports to CSV

## Quick Start

### Prerequisites

```bash
pip install psutil
```

### Usage

1. **Launch The Last War** and open alliance rankings

2. **Run the monitor:**
```bash
python live_alliance_monitor.py
```

3. **Slowly scroll through rankings** - The scanner captures data in real-time

4. **Press Ctrl+C when done** - Data automatically saves to CSV

### Output

**Console Display:**
```
[Scan #15] Alliances found: 47

Rank   Abbr     Full Name                      Power
======================================================================
1      UvvU     veni vidi vici                 6,435,764,372
2      ORCE     Omega Force                    6,387,057,595
3      NKOT     korea one team                 6,234,891,234
...
```

**CSV File:** `live_alliance_data.csv`
```csv
Rank,Short Name,Full Name,Power,Alliance ID
1,"UvvU","veni vidi vici",6435764372,"37ecf329739c4b61bf9da597829fa993"
2,"ORCE","Omega Force",6387057595,"40bdeadf9a184d7da54c7dc4a07feeac"
```

## Technical Details

### Memory Pattern Recognition

**Alliance Data Structure:**
```python
pattern = rb'([A-Z][A-Za-z0-9]{1,6})\s+([0-9a-f]{32})\s+\d([^\x00-\x08\x0b-\x1f]{3,40}?)[\x00-\x08]'
```

Components:
- `[A-Z][A-Za-z0-9]{1,6}` - Alliance abbreviation (2-7 chars)
- `[0-9a-f]{32}` - Unique alliance ID (hex hash)
- `\d` - Number separator
- `[^\x00-\x08\x0b-\x1f]{3,40}?` - Full name (3-40 printable chars)

### Data Type Storage

**Rank Number:**
- Format: 32-bit unsigned integer (uint32)
- Byte order: Little-endian
- Range: 1-50
```python
rank_bytes = struct.pack('<I', rank)  # e.g., 1 = b'\x01\x00\x00\x00'
```

**Power Value:**
- Format: 64-bit unsigned integer (uint64)
- Byte order: Little-endian
- Range: 1,000,000,000 - 10,000,000,000
```python
power = struct.unpack('<Q', bytes)[0]  # e.g., 6435764372
```

**Alliance ID:**
- Format: 32-character hexadecimal string (ASCII)
- Example: `37ecf329739c4b61bf9da597829fa993`
- This is the **permanent unique identifier** (names can change)

### Memory Scanning Strategy

The scanner focuses on writable memory regions:

```python
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04

# Only scan active data regions
if mbi.State == MEM_COMMIT and mbi.Protect == PAGE_READWRITE:
    # Scan in 2MB chunks
    scan_size = min(mbi.RegionSize, 2 * 1024 * 1024)
```

**Why writable memory?**
- Alliance data updates as you scroll
- Read-only memory contains static game code
- Writable regions hold dynamic UI data

### Proximity Detection

Data fields are stored close together in memory:

```python
# Look within 100 bytes before/after alliance name
check_start = max(0, idx - 100)
check_end = min(len(data), idx + 200)
check_region = data[check_start:check_end]

# Find rank (1-50)
for r in range(1, 51):
    if struct.pack('<I', r) in check_region:
        rank = r
        break

# Find power (1B-10B)
for i in range(0, len(check_region) - 8, 4):
    val = struct.unpack('<Q', check_region[i:i+8])[0]
    if 1_000_000_000 <= val <= 10_000_000_000:
        power = val
        break
```

## Alternative Scanners

### 1. Comprehensive Scanner (One-Shot)

Scans all memory once:

```bash
python comprehensive_alliance_scanner.py
```

**Use when:** Rankings window is open and stable

**Output:** `alliances_extracted_from_memory.csv`

### 2. ID-Based Scanner (Targeted)

Searches for specific alliance IDs:

```bash
python scan_by_alliance_id.py
```

**Use when:** Looking for specific alliances

**Output:** Console display with memory addresses

### 3. Ranking Scanner (Debug)

Finds rank numbers near known alliances:

```bash
python scan_for_rankings.py
```

**Use when:** Debugging rank detection

**Output:** Memory addresses and offsets

## Tips for Best Results

1. **Scroll slowly** - Gives scanner time to capture data
2. **Keep rankings window open** - Data only in memory when visible
3. **Run as Administrator** - Ensures memory access permissions
4. **Scan multiple times** - Some data only appears when scrolled to
5. **Let it run 30+ seconds** - Captures all alliances as they load

## Troubleshooting

**"Game not running"**
- Make sure The Last War is launched
- Check Task Manager for "LastWar.exe" process

**"Access denied"**
- Run PowerShell/Command Prompt as Administrator
- Restart game and try again

**"Found 0 alliances"**
- Open alliance rankings window in game
- Scroll through list slowly
- Some data only loads on-demand

**"Power values incorrect"**
- Power shown may be cached
- Different power types (total vs current)
- Usually within 1-5% of actual value

## Why This Works

The Last War has strong anti-modding protection:
- ❌ Asset bundles encrypted
- ❌ IL2CPP metadata removed
- ❌ Anti-cheat blocks debugging tools
- ❌ BepInEx plugins won't load

**But memory reading works because:**
- ✅ UI must display data to user
- ✅ Decrypted data exists in RAM temporarily
- ✅ Reading memory doesn't modify game
- ✅ Anti-cheat focuses on code injection, not reading

We're essentially reading what's already on your screen - just directly from memory instead of OCR.

## Data Persistence

**Alliance ID is permanent** - Names can change but the 32-char hash ID stays the same. Use this for:
- Tracking alliances over time
- Matching data across different scans
- Building historical power databases

## Advanced Usage

### Continuous Monitoring

Run scanner in background and log to file:

```bash
python live_alliance_monitor.py > alliance_log.txt 2>&1
```

### Automated Data Collection

Create scheduled task to scan every hour:

```powershell
# Windows Task Scheduler
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\live_alliance_monitor.py"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "AllianceScanner"
```

### Filter by Power Range

Modify scanner to only capture top alliances:

```python
# In live_alliance_monitor.py, line 100
if 1_000_000_000 <= val <= 10_000_000_000:  # Change to 6_000_000_000 for top alliances only
    power = val
```

## Limitations

- **Only captures visible data** - Must scroll to load all alliances
- **Timing dependent** - Data must be in memory when scanned
- **No historical data** - Only current values
- **Requires game running** - Can't extract from offline files

## See Also

- [README.md](README.md) - Main documentation
- [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) - Automated screenshot scraping
- [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md) - Manual screenshot extraction
- [FINDINGS.md](FINDINGS.md) - All extraction methods tested
