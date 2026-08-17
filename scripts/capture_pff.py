#!/usr/bin/env python3
"""
PFF Reverse Engineering Capture Tool

Usage:
    python scripts/capture_pff.py --url https://www.pff.com/nfl/teams/buffalo-bills/4/roster --name bills_roster
    python scripts/capture_pff.py --sample bills_roster --inspect
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.base import PFFScraper
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Full PFF URL to capture")
    parser.add_argument("--name", help="Short name for the sample")
    parser.add_argument("--sample", help="Load and inspect a previously saved sample")
    parser.add_argument("--inspect", action="store_true", help="Show structure summary")
    parser.add_argument("--next", action="store_true", help="Try to extract __NEXT_DATA__")
    args = parser.parse_args()

    sc = PFFScraper(cache_enabled=True)

    if args.url:
        html = sc.get(args.url, force_refresh=True)
        name = args.name or "captured_page"
        sc.save_sample(name, html)
        print(f"Captured -> data/samples/{name}.html")
        if args.inspect:
            _inspect(html)

    if args.sample:
        try:
            html = sc.load_sample(args.sample)
            print(f"Loaded sample: {args.sample}")
            if args.inspect:
                _inspect(html)
            if args.next:
                data = sc.parse_next_data(html)
                if data:
                    print("\n=== __NEXT_DATA__ top level keys ===")
                    print(list(data.keys()) if isinstance(data, dict) else "Not a dict")
                    if "props" in data:
                        print("Has 'props' - this is the main state")
                else:
                    print("No __NEXT_DATA__ found")
        except FileNotFoundError:
            print("Sample not found. Run with --url first.")

def _inspect(html: str):
    soup = BeautifulSoup(html, "lxml")
    print(f"\nHTML length: {len(html)}")
    player_links = soup.select('a[href*="/nfl/players/"]')
    print(f"Player links: {len(player_links)}")
    grade_nums = sum(1 for t in soup.find_all(string=True) if any(c.isdigit() for c in str(t)))
    print(f"Elements with digits (grades/snaps): {grade_nums}")
    print(f"Tables: {len(soup.find_all('table'))}")
    print(f"Has __NEXT_DATA__: {'__NEXT_DATA__' in html}")

if __name__ == "__main__":
    main()
