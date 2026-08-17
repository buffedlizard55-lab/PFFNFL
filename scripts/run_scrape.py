#!/usr/bin/env python3
"""
PFFNFL Data Scraper Runner

Usage examples:
    python scripts/run_scrape.py --season 2026 --type teams
    python scripts/run_scrape.py --season 2026 --type roster --team buffalo-bills
    python scripts/run_scrape.py --season 2026 --type schedule --team buffalo-bills
    python scripts/run_scrape.py --season 2026 --type scores --week 1
"""
import argparse
import json
from pathlib import Path
from datetime import datetime

from scrapers.teams import TeamScraper
from scrapers.roster import RosterScraper
from scrapers.schedule import ScheduleScraper

DATA_DIR = Path("data/processed")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_json(data, filename: str):
    path = DATA_DIR / filename
    path.write_text(json.dumps(data, indent=2, default=str))
    print(f"Saved → {path}")


def main():
    parser = argparse.ArgumentParser(description="PFFNFL Public Data Scraper")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--type", choices=["teams", "roster", "schedule", "scores"], required=True)
    parser.add_argument("--team", help="Team slug, e.g. buffalo-bills")
    parser.add_argument("--week", default="1")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    print(f"PFFNFL Scraper — season={args.season} type={args.type}")

    if args.type == "teams":
        scraper = TeamScraper(cache_enabled=not args.no_cache)
        teams = scraper.fetch_teams()
        save_json(teams, f"teams_{args.season}.json")
        print(f"Fetched {len(teams)} teams")

    elif args.type == "roster":
        if not args.team:
            print("ERROR: --team is required for roster")
            return
        scraper = RosterScraper(cache_enabled=not args.no_cache)
        # Get team id from teams list
        team_scraper = TeamScraper(cache_enabled=True)
        teams = team_scraper.fetch_teams()
        team = next((t for t in teams if t["slug"] == args.team), None)
        if not team:
            print(f"Team not found: {args.team}")
            return

        players = scraper.fetch_roster(team["slug"], team["id"])
        save_json(players, f"roster_{args.team}_{args.season}.json")
        print(f"Fetched {len(players)} players for {args.team}")

    elif args.type == "schedule":
        if not args.team:
            print("ERROR: --team is required for schedule")
            return
        scraper = ScheduleScraper(cache_enabled=not args.no_cache)
        team_scraper = TeamScraper(cache_enabled=True)
        teams = team_scraper.fetch_teams()
        team = next((t for t in teams if t["slug"] == args.team), None)
        if not team:
            print(f"Team not found: {args.team}")
            return

        games = scraper.fetch_team_schedule(team["slug"], team["id"], args.season)
        save_json(games, f"schedule_{args.team}_{args.season}.json")
        print(f"Fetched {len(games)} games for {args.team}")

    elif args.type == "scores":
        scraper = ScheduleScraper(cache_enabled=not args.no_cache)
        games = scraper.fetch_scores_page(args.week, args.season)
        save_json(games, f"scores_week{args.week}_{args.season}.json")
        print(f"Fetched {len(games)} games for week {args.week}")

    print("Done.")


if __name__ == "__main__":
    main()
