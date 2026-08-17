#!/usr/bin/env python3
"""
Fetch full public PFF data for one team.

Example:
    python scripts/fetch_pff_team.py buffalo-bills 4
"""
import argparse
import json
from pathlib import Path
from scrapers.roster import RosterScraper
from scrapers.lineup import LineupScraper
from scrapers.base import PFFScraper

DATA_DIR = Path("data/processed/pff")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Team slug, e.g. buffalo-bills")
    parser.add_argument("team_id", type=int, help="Team numeric ID, e.g. 4")
    parser.add_argument("--season", default=2026, type=int)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching PFF public data for {args.slug} (id={args.team_id})")

    r = RosterScraper(cache_enabled=not args.force)
    roster = r.fetch_roster(args.slug, args.team_id, force_refresh=args.force)

    l = LineupScraper(cache_enabled=not args.force)
    lineup = l.fetch_lineup(args.slug, args.team_id)

    out = {
        "team": args.slug,
        "team_id": args.team_id,
        "season": args.season,
        "roster": roster,
        "lineup": lineup,
    }

    out_path = DATA_DIR / f"{args.slug}_{args.season}.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Saved → {out_path}")
    print(f"  Roster: {len(roster)} players")
    print(f"  Lineup offense: {len(lineup.get('offense', []))}")
    print(f"  Lineup defense: {len(lineup.get('defense', []))}")

if __name__ == "__main__":
    main()
