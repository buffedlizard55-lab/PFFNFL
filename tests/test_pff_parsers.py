"""
PFF Reverse Engineering Parser Tests

Run with:
    python -m tests.test_pff_parsers
    or
    python tests/test_pff_parsers.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.roster import RosterScraper
from scrapers.lineup import LineupScraper
from scrapers.base import PFFScraper
import json


def test_roster_parser():
    print("Testing RosterScraper...")
    r = RosterScraper(cache_enabled=True)
    html = r.load_sample("bills_roster_real_2026")
    players = r.parse_roster(html, "buffalo-bills", 4)

    assert len(players) >= 4, f"Expected at least 4 players, got {len(players)}"
    assert players[0]["name"] == "Josh Allen"
    assert players[0]["position"] == "QB"
    assert players[0]["player_id"] == 46601
    assert players[0]["overall_grade"] == 90.6
    assert players[0]["snaps"] is not None and players[0]["snaps"] > 100

    # Check key fields exist
    required = ["player_id", "slug", "name", "position", "overall_grade", "snaps", "url"]
    for field in required:
        assert field in players[0], f"Missing field: {field}"

    print(f"  ✓ Roster: {len(players)} players parsed correctly")
    print(f"  ✓ Josh Allen: grade={players[0]['overall_grade']}, snaps={players[0]['snaps']}")
    return True


def test_lineup_parser():
    print("Testing LineupScraper...")
    l = LineupScraper(cache_enabled=True)
    try:
        html = l.load_sample("bills_lineup_test")
    except FileNotFoundError:
        print("  ⚠ bills_lineup_test.html not found, skipping detailed lineup test")
        return True

    lu = l.parse_lineup(html, "buffalo-bills")

    assert "offense" in lu
    assert "defense" in lu
    assert isinstance(lu["offense"], list)
    assert isinstance(lu["defense"], list)

    print(f"  ✓ Lineup: offense={len(lu['offense'])}, defense={len(lu['defense'])}")
    return True


def test_base_scraper():
    print("Testing PFFScraper base...")
    sc = PFFScraper(cache_enabled=True)

    # Test next_data extraction on a fake page
    fake_html = '<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"test":123}}}</script>'
    data = sc.parse_next_data(fake_html)
    assert data is not None
    assert data.get("props", {}).get("pageProps", {}).get("test") == 123

    print("  ✓ Base: parse_next_data works")
    return True


def test_player_sanity():
    """Basic sanity on roster output structure"""
    print("Testing player record sanity...")
    r = RosterScraper(cache_enabled=True)
    html = r.load_sample("bills_roster_real_2026")
    players = r.parse_roster(html, "buffalo-bills", 4)

    for p in players:
        assert isinstance(p["player_id"], int)
        assert p["name"] and len(p["name"]) > 2
        assert p["position"] in {"QB", "HB", "WR", "TE", "CB", "ED", "UNK"} or p["position"] != ""

    print("  ✓ All player records have valid structure")
    return True


def run_all():
    print("\n" + "=" * 60)
    print("PFFNFL — Parser Test Suite (Pure PFF Reverse Engineering)")
    print("=" * 60 + "\n")

    results = []
    results.append(("roster", test_roster_parser()))
    results.append(("lineup", test_lineup_parser()))
    results.append(("base", test_base_scraper()))
    results.append(("sanity", test_player_sanity()))
    results.append(("game", test_game_parser()))
    results.append(("schedule", test_schedule_parser()))

    print("\n" + "-" * 60)
    passed = sum(1 for _, ok in results if ok)
    print(f"Results: {passed}/{len(results)} tests passed")

    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {name}")

    print("=" * 60 + "\n")

    if passed == len(results):
        print("✅ All PFF parser tests passing")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all())

def test_game_parser():
    print("Testing GameScraper (new)...")
    from scrapers.game import GameScraper
    g = GameScraper(cache_enabled=True)
    try:
        html = g.load_sample("bills_game_sample_2026")
    except FileNotFoundError:
        print("  ⚠ game sample not found, skipping")
        return True

    parsed = g.parse_game(html, "2026/1/carolina-panthers_at_buffalo-bills_31908")
    assert "away_score" in parsed and parsed["away_score"] == 27
    assert "home_score" in parsed and parsed["home_score"] == 20
    assert parsed.get("week") == "1"
    assert len(parsed.get("player_stats", [])) >= 1
    print(f"  ✓ Game: score {parsed.get('away_score')}-{parsed.get('home_score')}, week={parsed.get('week')}, players={len(parsed.get('player_stats',[]))}")
    return True


def test_schedule_parser():
    print("Testing ScheduleScraper (new)...")
    from scrapers.schedule import ScheduleScraper
    s = ScheduleScraper(cache_enabled=True)
    try:
        html = s.load_sample("bills_schedule_sample_2026")
    except FileNotFoundError:
        print("  ⚠ schedule sample not found, skipping")
        return True

    games = s.parse_team_schedule(html, "buffalo-bills", 2026)
    assert len(games) == 3
    assert games[0]["week"] == "1"
    assert games[0]["opponent"] == "Carolina Panthers"
    assert games[0]["is_home"] is False
    assert "/nfl/scores/" in games[0].get("url", "")   # schedule entries link to scores pages
    assert games[1]["is_home"] is True
    assert games[2]["week"] == "3"
    print(f"  ✓ Schedule: {len(games)} games parsed | Week1: {games[0]['team']} { 'vs' if games[0]['is_home'] else 'at'} {games[0]['opponent']}")
    return True
