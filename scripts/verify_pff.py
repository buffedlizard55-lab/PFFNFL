#!/usr/bin/env python3
"""
PFFNFL Verification Script

Runs all available PFF parsers against samples and reports status.
Use this before making changes or to confirm the current state of reverse engineering.

Usage:
    python scripts/verify_pff.py
"""
import sys
from pathlib import Path

# Make sure we can import from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.roster import RosterScraper
from scrapers.lineup import LineupScraper
from scrapers.base import PFFScraper
from scrapers.player import PlayerScraper
from scrapers.game import GameScraper
from scrapers.schedule import ScheduleScraper


def verify():
    print("\n" + "=" * 65)
    print("PFFNFL VERIFICATION — Pure Pro Football Focus Reverse Engineering")
    print("=" * 65)

    results = []

    # 1. Roster (most important)
    try:
        r = RosterScraper(cache_enabled=True)
        html = r.load_sample("bills_roster_real_2026")
        players = r.parse_roster(html, "buffalo-bills", 4)

        assert len(players) >= 5
        assert players[0]["name"] == "Josh Allen"
        assert players[0]["overall_grade"] == 90.6
        assert players[0]["snaps"] and players[0]["snaps"] > 100

        print(f"✅ ROSTER     : {len(players)} players  |  Example: Josh Allen (Grade {players[0]['overall_grade']}, Snaps {players[0]['snaps']})")
        results.append(True)
    except Exception as e:
        print(f"❌ ROSTER     : FAILED — {e}")
        results.append(False)

    # 2. Lineup
    try:
        l = LineupScraper(cache_enabled=True)
        html = l.load_sample("bills_lineup_test")
        lu = l.parse_lineup(html, "buffalo-bills")

        off = len(lu.get("offense", []))
        deff = len(lu.get("defense", []))
        assert off + deff >= 3

        print(f"✅ LINEUP     : offense={off}  defense={deff}  |  personnel={lu.get('personnel', [])}")
        results.append(True)
    except Exception as e:
        print(f"❌ LINEUP     : FAILED — {e}")
        results.append(False)

    # 3. Base scraper + __NEXT_DATA__
    try:
        sc = PFFScraper(cache_enabled=True)
        fake = '<script id="__NEXT_DATA__">{"props":{"test": "ok"}}</script>'
        data = sc.parse_next_data(fake)
        assert data and data.get("props", {}).get("test") == "ok"
        print("✅ BASE       : parse_next_data works")
        results.append(True)
    except Exception as e:
        print(f"❌ BASE       : FAILED — {e}")
        results.append(False)

    # 4. Other scrapers load
    try:
        PlayerScraper(cache_enabled=True)
        GameScraper(cache_enabled=True)
        ScheduleScraper(cache_enabled=True)
        print("✅ OTHER      : PlayerScraper + GameScraper + ScheduleScraper load successfully")
        results.append(True)
    except Exception as e:
        print(f"❌ OTHER      : FAILED — {e}")
        results.append(False)

    # 5. Schedule parser (sample)
    try:
        s = ScheduleScraper(cache_enabled=True)
        html = s.load_sample("bills_schedule_sample_2026")
        games = s.parse_team_schedule(html, "buffalo-bills", 2026)
        assert len(games) == 3
        assert games[0]["week"] == "1"
        assert "Carolina Panthers" in games[0]["opponent"]
        print(f"✅ SCHEDULE   : {len(games)} entries | W1: {games[0]['team']} at {games[0]['opponent']}")
        results.append(True)
    except Exception as e:
        print(f"❌ SCHEDULE   : FAILED — {e}")
        results.append(False)

    # Summary
    print("-" * 65)
    passed = sum(results)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")

    if passed == total:
        print("✅ PFF reverse engineering stack is healthy")
        return 0
    else:
        print("⚠️  Some components need attention")
        return 1


if __name__ == "__main__":
    sys.exit(verify())
