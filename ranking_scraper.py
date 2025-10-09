#!/usr/bin/env python3
"""
Automated Ranking Data Scraper for The Last War

Captures leaderboard data including:
- Player rankings
- Alliance rankings
- Power levels
- Player names (OCR)
"""

import pyautogui
import time
from pathlib import Path
from PIL import ImageGrab
import json
from datetime import datetime

# OCR support
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class RankingScraper:
    def __init__(self, output_dir="extracted-rankings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Enable failsafe
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3

        self.ranking_data = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def capture_ranking_row(self, y_position, row_number):
        """Capture a single ranking row"""
        # Assume ranking rows are ~800px wide, 80px tall
        # Centered on screen
        screen_width, screen_height = pyautogui.size()
        x_center = screen_width // 2

        # Capture row
        row_img = ImageGrab.grab(bbox=(
            x_center - 400,  # 400px left of center
            y_position - 40,  # 40px above click point
            x_center + 400,  # 400px right of center
            y_position + 40   # 40px below click point
        ))

        # Save screenshot
        img_file = self.output_dir / f"rank_{row_number:03d}_{self.session_id}.png"
        row_img.save(img_file)

        # OCR if available
        text_data = ""
        if OCR_AVAILABLE:
            try:
                text_data = pytesseract.image_to_string(row_img).strip()
            except:
                pass

        return {
            'rank': row_number,
            'screenshot': str(img_file),
            'ocr_text': text_data,
            'timestamp': datetime.now().isoformat()
        }

    def scrape_visible_rankings(self, start_rank=1):
        """Scrape all visible ranking rows on screen"""
        print(f"\n[*] Scraping visible rankings (starting from #{start_rank})...")

        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()

        # Assume rankings start at 30% down screen, each row is ~80px
        start_y = int(screen_height * 0.3)
        row_height = 80

        visible_rows = []
        for i in range(6):  # Typically 5-6 rows visible
            y_pos = start_y + (i * row_height)
            row_data = self.capture_ranking_row(y_pos, start_rank + i)
            visible_rows.append(row_data)
            print(f"    → Rank #{start_rank + i}: {row_data['ocr_text'][:50]}...")

        return visible_rows

    def scroll_rankings(self, amount=3):
        """Scroll down in rankings list"""
        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 2
        center_y = screen_height // 2

        pyautogui.click(center_x, center_y)
        time.sleep(0.2)
        pyautogui.scroll(-amount)
        time.sleep(0.8)  # Wait for animation

    def run(self, num_rankings=50, scroll_every=5):
        """Main ranking scraper"""
        print("=" * 60)
        print("THE LAST WAR - RANKING SCRAPER")
        print("=" * 60)
        print()
        print("[!] PREREQUISITES:")
        print("    1. The Last War is running")
        print("    2. You are on a RANKING/LEADERBOARD screen")
        print("    3. Rankings are visible")
        print()
        print("[!] FAILSAFE: Move mouse to corner to abort!")
        print()
        print(f"[*] Will scrape {num_rankings} ranking entries")
        print()

        input("Press ENTER when ready to start...")

        current_rank = 1
        total_scraped = 0

        try:
            while total_scraped < num_rankings:
                # Scrape visible rankings
                rows = self.scrape_visible_rankings(current_rank)
                self.ranking_data.extend(rows)
                total_scraped += len(rows)

                print(f"[+] Progress: {total_scraped}/{num_rankings}")

                # Scroll down to show next batch
                if total_scraped < num_rankings:
                    self.scroll_rankings(scroll_every)
                    current_rank += scroll_every

        except pyautogui.FailSafeException:
            print("\n[!] Failsafe triggered! Stopping...")
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")

        # Save data
        json_file = self.output_dir / f"rankings_{self.session_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.ranking_data, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Scraping complete!")
        print(f"[+] Scraped {len(self.ranking_data)} ranking entries")
        print(f"[+] Data saved to: {json_file}")
        print(f"[+] Screenshots saved to: {self.output_dir}")

def main():
    import os
    print("[*] Installing required packages...")
    os.system("pip install pyautogui pillow pytesseract --quiet")

    scraper = RankingScraper()

    print("\nHow many ranking entries to scrape?")
    try:
        num = int(input("Enter number (default 50): ") or "50")
    except ValueError:
        num = 50

    scraper.run(num_rankings=num)

if __name__ == "__main__":
    main()
