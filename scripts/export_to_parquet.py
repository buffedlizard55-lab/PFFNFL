#!/usr/bin/env python3
"""
Export PFF extracted data to Parquet.

Currently focused on roster data (the most mature extractor).
Run after fetching new roster data.
"""
import json
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def export_rosters_from_samples():
    """Export all roster samples we have parsed into a single Parquet."""
    from scrapers.roster import RosterScraper

    r = RosterScraper(cache_enabled=True)
    all_players = []

    sample_files = list(Path("data/samples").glob("*roster*.html"))
    for sample in sample_files:
        try:
            html = sample.read_text(encoding="utf-8", errors="ignore")
            # Try to infer team from filename or default
            team_slug = "unknown"
            if "bills" in sample.name.lower():
                team_slug = "buffalo-bills"
            players = r.parse_roster(html, team_slug, 0)
            all_players.extend(players)
        except Exception as e:
            print(f"  Skipped {sample.name}: {e}")

    if all_players:
        df = pd.DataFrame(all_players)
        out_path = OUT_DIR / "pff_rosters.parquet"
        df.to_parquet(out_path, index=False)
        print(f"Exported {len(df)} roster rows → {out_path}")
        print(f"Columns: {list(df.columns)[:10]}...")
        return out_path
    return None


def main():
    print("PFFNFL Parquet Export (PFF-only)")
    print("-" * 40)
    export_rosters_from_samples()
    print("Done.")


if __name__ == "__main__":
    main()
