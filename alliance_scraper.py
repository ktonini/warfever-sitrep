#!/usr/bin/env python3
"""
Automated Alliance Logo & Data Scraper for The Last War

Uses mouse automation to navigate alliance list and capture:
- Alliance logos
- Alliance names (OCR)
- Ranking data (OCR)
- Power levels
"""

import pyautogui
import time
import os
from pathlib import Path
from PIL import Image, ImageGrab
import json
from datetime import datetime

# Try to import OCR libraries
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    print("[!] pytesseract not installed. OCR features disabled.")
    print("[*] Install with: pip install pytesseract")
    print("[*] Also install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
    OCR_AVAILABLE = False

class AllianceScraper:
    def __init__(self, output_dir="extracted-alliances"):
        """Initialize the alliance scraper"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "logos").mkdir(exist_ok=True)
        (self.output_dir / "screenshots").mkdir(exist_ok=True)
        (self.output_dir / "data").mkdir(exist_ok=True)

        # Failsafe - move mouse to corner to abort
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5  # 500ms pause between actions

        self.alliance_data = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def setup_tesseract(self):
        """Configure Tesseract OCR path (Windows)"""
        if OCR_AVAILABLE:
            # Common Tesseract installation paths
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\k33bz\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
            ]

            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"[+] Tesseract found at: {path}")
                    return True

            print("[!] Tesseract not found. OCR disabled.")
            return False
        return False

    def find_game_window(self):
        """Locate The Last War game window"""
        print("[*] Looking for The Last War window...")

        # Try to find window by title
        windows = pyautogui.getAllWindows()
        for window in windows:
            if "LastWar" in window.title or "The Last War" in window.title:
                print(f"[+] Found game window: {window.title}")
                window.activate()  # Bring to front
                time.sleep(1)
                return window

        print("[!] Game window not found. Make sure The Last War is running.")
        print("[*] Available windows:")
        for w in windows[:10]:  # Show first 10
            print(f"    - {w.title}")
        return None

    def calibrate(self):
        """Interactive calibration to find UI element positions"""
        print("\n=== CALIBRATION MODE ===")
        print("[*] You have 5 seconds to hover your mouse over each element...")
        print("[*] Press Ctrl+C to skip calibration and use manual coordinates\n")

        positions = {}

        try:
            # Alliance menu button
            print("[1] Hover over ALLIANCE MENU button")
            time.sleep(5)
            positions['alliance_button'] = pyautogui.position()
            print(f"    → Recorded: {positions['alliance_button']}")

            # Alliance list area (first item)
            print("\n[2] Hover over FIRST ALLIANCE in the list")
            time.sleep(5)
            positions['first_alliance'] = pyautogui.position()
            print(f"    → Recorded: {positions['first_alliance']}")

            # Logo location (approximate)
            print("\n[3] Hover over ALLIANCE LOGO (left side)")
            time.sleep(5)
            positions['logo_area'] = pyautogui.position()
            print(f"    → Recorded: {positions['logo_area']}")

            # Alliance name text
            print("\n[4] Hover over ALLIANCE NAME text")
            time.sleep(5)
            positions['name_area'] = pyautogui.position()
            print(f"    → Recorded: {positions['name_area']}")

            # Ranking/power area
            print("\n[5] Hover over RANKING/POWER text")
            time.sleep(5)
            positions['rank_area'] = pyautogui.position()
            print(f"    → Recorded: {positions['rank_area']}")

            # Scroll area
            print("\n[6] Hover in SCROLL AREA (middle of list)")
            time.sleep(5)
            positions['scroll_area'] = pyautogui.position()
            print(f"    → Recorded: {positions['scroll_area']}")

            # Save calibration
            calib_file = self.output_dir / "calibration.json"
            with open(calib_file, 'w') as f:
                json.dump({k: list(v) for k, v in positions.items()}, f, indent=2)
            print(f"\n[+] Calibration saved to: {calib_file}")

            return positions

        except KeyboardInterrupt:
            print("\n[!] Calibration skipped. Using manual coordinates...")
            return None

    def load_calibration(self):
        """Load saved calibration data"""
        calib_file = self.output_dir / "calibration.json"
        if calib_file.exists():
            with open(calib_file, 'r') as f:
                data = json.load(f)
                return {k: tuple(v) for k, v in data.items()}
        return None

    def capture_region(self, x, y, width, height, filename=None):
        """Capture a specific screen region"""
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))

        if filename:
            screenshot.save(filename)
            return filename
        return screenshot

    def extract_text_ocr(self, image):
        """Extract text from image using OCR"""
        if not OCR_AVAILABLE:
            return ""

        try:
            # Convert PIL image to text
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"[!] OCR error: {e}")
            return ""

    def scrape_alliance_entry(self, positions, index):
        """Scrape a single alliance entry"""
        print(f"\n[*] Scraping alliance #{index + 1}...")

        alliance_info = {
            'index': index,
            'timestamp': datetime.now().isoformat()
        }

        # Capture logo (100x100 region around logo_area)
        logo_x, logo_y = positions['logo_area']
        logo_file = self.output_dir / "logos" / f"alliance_{index:03d}_{self.session_id}.png"
        self.capture_region(logo_x - 50, logo_y - 50, 100, 100, logo_file)
        alliance_info['logo_file'] = str(logo_file)
        print(f"    → Logo saved: {logo_file.name}")

        # Capture name area and OCR
        name_x, name_y = positions['name_area']
        name_img = self.capture_region(name_x - 10, name_y - 15, 300, 30)
        alliance_name = self.extract_text_ocr(name_img)
        alliance_info['name'] = alliance_name
        print(f"    → Name: {alliance_name}")

        # Capture rank/power area and OCR
        rank_x, rank_y = positions['rank_area']
        rank_img = self.capture_region(rank_x - 10, rank_y - 15, 200, 30)
        rank_text = self.extract_text_ocr(rank_img)
        alliance_info['rank_power'] = rank_text
        print(f"    → Rank/Power: {rank_text}")

        # Full screenshot of entry
        entry_file = self.output_dir / "screenshots" / f"alliance_{index:03d}_{self.session_id}.png"
        first_x, first_y = positions['first_alliance']
        self.capture_region(first_x - 100, first_y - 50, 800, 100, entry_file)
        alliance_info['screenshot'] = str(entry_file)

        self.alliance_data.append(alliance_info)
        return alliance_info

    def scroll_down(self, positions, amount=3):
        """Scroll down in the alliance list"""
        scroll_x, scroll_y = positions['scroll_area']
        pyautogui.click(scroll_x, scroll_y)  # Focus on list
        time.sleep(0.2)
        pyautogui.scroll(-amount)  # Negative = scroll down
        time.sleep(0.5)  # Wait for animation

    def run(self, num_alliances=50):
        """Main scraping loop"""
        print("=" * 60)
        print("THE LAST WAR - ALLIANCE SCRAPER")
        print("=" * 60)
        print()
        print("[!] FAILSAFE: Move mouse to corner to abort!")
        print()

        # Setup
        if OCR_AVAILABLE:
            self.setup_tesseract()

        # Find game window
        window = self.find_game_window()
        if not window:
            print("[!] Please start The Last War and try again.")
            return

        # Load or create calibration
        positions = self.load_calibration()
        if not positions:
            positions = self.calibrate()
            if not positions:
                print("[!] Calibration required. Exiting.")
                return

        # Navigate to alliance menu
        print("\n[*] Navigating to alliance menu...")
        pyautogui.click(positions['alliance_button'])
        time.sleep(2)

        # Start scraping
        print(f"\n[*] Starting scrape of {num_alliances} alliances...")
        print("[*] Progress:")

        for i in range(num_alliances):
            try:
                # Scrape current entry
                self.scrape_alliance_entry(positions, i)

                # Scroll to next entry (every 3rd entry to account for list items)
                if (i + 1) % 3 == 0:
                    self.scroll_down(positions)

                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"\n[+] Progress: {i + 1}/{num_alliances} alliances scraped")

            except pyautogui.FailSafeException:
                print("\n[!] Failsafe triggered! Stopping...")
                break
            except Exception as e:
                print(f"\n[!] Error on alliance {i + 1}: {e}")
                continue

        # Save data
        data_file = self.output_dir / "data" / f"alliance_data_{self.session_id}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.alliance_data, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Scraping complete!")
        print(f"[+] Scraped {len(self.alliance_data)} alliances")
        print(f"[+] Data saved to: {data_file}")
        print(f"[+] Logos saved to: {self.output_dir / 'logos'}")
        print(f"[+] Screenshots saved to: {self.output_dir / 'screenshots'}")

def main():
    """Entry point"""
    print("[*] Installing required packages...")
    os.system("pip install pyautogui pillow pytesseract --quiet")

    scraper = AllianceScraper()

    print("\nHow many alliances to scrape?")
    try:
        num = int(input("Enter number (default 50): ") or "50")
    except ValueError:
        num = 50

    scraper.run(num_alliances=num)

if __name__ == "__main__":
    main()
