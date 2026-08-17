#!/usr/bin/env python3
"""
Fetch basic public data for all 32 teams (rosters + schedules).
Useful for initial data collection.
"""
import json
from pathlib import Path
from scrapers.teams import TeamScraper
from scrapers.roster import RosterScraper
from scrapers.schedule import ScheduleScraper

DATA_DIR = Path("data/processed")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def main(season: int = 2026):
    print(f"=== Fetching public PFF data for season {season} ===")

    team_scraper = TeamScraper()
    teams = team_scraper.fetch_teams()
    (DATA_DIR / f"teams_{season}.json").write_text(json.dumps(teams, indent=2))
    print(f"Teams: {len(teams)}")

    roster_scraper = RosterScraper()
    schedule_scraper = ScheduleScraper()

    for t in teams:
        slug = t["slug"]
        tid = t["id"]
        print(f"→ {t['name']} ({slug})")

        try:
            roster = roster_scraper.fetch_roster(slug, tid)
            (DATA_DIR / f"roster_{slug}_{season}.json").write_text(json.dumps(roster, indent=2))
        except Exception as e:
            print(f"  Roster failed: {e}")

        try:
            sched = schedule_scraper.fetch_team_schedule(slug, tid, season)
            (DATA_DIR / f"schedule_{slug}_{season}.json").write_text(json.dumps(sched, indent=2))
        except Exception as e:
            print(f"  Schedule failed: {e}")

    print("All done.")


if __name__ == "__main__":
    main()
