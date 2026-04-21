#!/usr/bin/env python3
"""
Live Alliance Data Monitor
Watches memory in real-time as you scroll through alliance rankings
Press Ctrl+C to stop and save data
"""

import sys

if sys.platform != "win32":
    print("This script requires Windows.")
    sys.exit(1)

from pathlib import Path

from lw_alliance_monitor_core import (
    close_handle,
    find_process,
    merge_alliances,
    open_game_handle,
    quick_scan,
    write_alliance_csv,
)

output_file = Path("live_alliance_data.csv")


def main() -> None:
    if "--debug" in sys.argv:
        from lw_debug_log import setup_monitor_logging

        setup_monitor_logging(
            verbose=True,
            log_file=Path.cwd() / "lw_monitor_debug.log",
            stream=sys.stderr,
        )

    print("Live Alliance Monitor")
    print("=" * 60)
    print("\n[*] Instructions:")
    print("    1. Make sure alliance rankings window is open in game")
    print("    2. Slowly scroll through the rankings")
    print("    3. This will continuously scan and capture data")
    print("    4. Press Ctrl+C when done to save\n")

    game_proc = find_process("LastWar")
    if not game_proc:
        print("[!] Game not running")
        sys.exit(1)

    print(f"[+] Found game: {game_proc.name()} (PID: {game_proc.pid})")

    opened = open_game_handle(game_proc.pid)
    if not opened:
        print("[!] Failed to open process")
        sys.exit(1)

    h_process, kernel32 = opened

    print("[+] Memory access granted")
    print("\n[*] Monitoring... (Ctrl+C to stop)\n")

    all_alliances: dict = {}
    scan_count = 0

    try:
        import time

        while True:
            scan_count += 1
            print(f"\r[Scan #{scan_count}] Alliances found: {len(all_alliances)}", end="", flush=True)

            new_data = quick_scan(h_process, kernel32)
            merge_alliances(all_alliances, new_data)

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n[*] Stopping monitor...")

    finally:
        close_handle(kernel32, h_process)

        print(f"\n[+] Captured {len(all_alliances)} unique alliances!")

        if all_alliances:
            alliances_list = list(all_alliances.values())
            alliances_with_rank = [a for a in alliances_list if a["rank"]]

            print(f"\n{'Rank':<6} {'Abbr':<8} {'Full Name':<30} {'Power'}")
            print("=" * 70)

            alliances_with_rank.sort(key=lambda x: x["rank"])
            for a in alliances_with_rank[:20]:
                rank = a["rank"] if a["rank"] else "?"
                power = f"{a['power']:,}" if a["power"] else "Unknown"
                print(f"{rank:<6} {a['abbr']:<8} {a['name']:<30} {power}")

            if len(alliances_with_rank) > 20:
                print(f"... and {len(alliances_with_rank) - 20} more")

            write_alliance_csv(output_file, all_alliances)
            print(f"\n[+] Data saved to: {output_file}")
        else:
            print("\n[!] No alliance data captured")


if __name__ == "__main__":
    main()
