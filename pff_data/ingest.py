"""
Ingestion helpers that turn raw scraper output into typed, provenance-rich PFF data.

This layer is the bridge between "reverse engineering scrapers" and
"reliable data source for backtesting".
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .models import PFFPlayerRoster, PFFProvenance, PFFLineupSnapshot, PFFGameSnapshot, PFFScheduleEntry
from scrapers.roster import RosterScraper
from scrapers.lineup import LineupScraper
from scrapers.game import GameScraper
from scrapers.schedule import ScheduleScraper


def ingest_roster_snapshot(
    team_slug: str,
    team_id: int,
    season: int,
    week: Optional[str] = None,
    snapshot_date: Optional[str] = None,
    sample_name: Optional[str] = None,
) -> List[PFFPlayerRoster]:
    """
    Parse a roster page (or sample) and return strongly typed PFFPlayerRoster records.
    """
    scraper = RosterScraper(cache_enabled=True)
    html = scraper.load_sample(sample_name) if sample_name else scraper.get(
        f"https://www.pff.com/nfl/teams/{team_slug}/{team_id}/roster"
    )

    raw_players = scraper.parse_roster(html, team_slug, team_id)

    provenance = PFFProvenance(
        source="pff_public_roster",
        page_url=f"https://www.pff.com/nfl/teams/{team_slug}/{team_id}/roster",
        sample_name=sample_name,
    )

    typed = []
    for p in raw_players:
        typed.append(
            PFFPlayerRoster(
                season=season,
                week=week,
                snapshot_date=snapshot_date,
                player_id=p["player_id"],
                slug=p["slug"],
                name=p["name"],
                team=team_slug,
                team_id=team_id,
                position=p.get("position", "UNK"),
                number=p.get("number"),
                overall_grade=p.get("overall_grade"),
                pass_grade=p.get("pass_grade"),
                run_grade=p.get("run_grade"),
                receiving_grade=p.get("receiving_grade"),
                defense_grade=p.get("defense_grade"),
                snaps=p.get("snaps"),
                age=p.get("age"),
                college=p.get("college"),
                draft_year=p.get("draft_year"),
                draft_round=p.get("draft_round"),
                draft_pick=p.get("draft_pick"),
                provenance=provenance,
            )
        )
    return typed


def ingest_lineup_snapshot(
    team_slug: str,
    team_id: int,
    season: int,
    week: Optional[str] = None,
    sample_name: Optional[str] = None,
) -> List[PFFLineupSnapshot]:
    scraper = LineupScraper(cache_enabled=True)
    html = scraper.load_sample(sample_name) if sample_name else scraper.get(
        f"https://www.pff.com/nfl/teams/{team_slug}/{team_id}/lineup"
    )
    raw = scraper.parse_lineup(html, team_slug)

    prov = PFFProvenance(
        source="pff_public_lineup",
        page_url=f"https://www.pff.com/nfl/teams/{team_slug}/{team_id}/lineup",
        sample_name=sample_name,
    )

    results = []
    for side in ("offense", "defense"):
        for i, entry in enumerate(raw.get(side, []), start=1):
            results.append(
                PFFLineupSnapshot(
                    season=season,
                    week=week,
                    team=team_slug,
                    side=side,
                    position_rank=i,
                    player_id=entry.get("player_id"),
                    player_name=entry.get("name", ""),
                    provenance=prov,
                )
            )
    return results


def ingest_game_snapshot(
    game_path: str,
    season: int,
    week: Optional[str] = None,
    sample_name: Optional[str] = None,
) -> PFFGameSnapshot:
    """
    Parse a public PFF game page (or sample) into a typed PFFGameSnapshot.
    This captures score + player participation / box stats for backtesting.
    """
    scraper = GameScraper(cache_enabled=True)
    html = scraper.load_sample(sample_name) if sample_name else scraper.get(
        f"https://www.pff.com/nfl/scores/{game_path}"
    )

    raw = scraper.parse_game(html, game_path)

    prov = PFFProvenance(
        source="pff_public_game",
        page_url=f"https://www.pff.com/nfl/scores/{game_path}",
        sample_name=sample_name,
    )

    return PFFGameSnapshot(
        season=season,
        week=week or raw.get("week"),
        game_path=game_path,
        away_team=raw.get("away_team"),
        home_team=raw.get("home_team"),
        away_score=raw.get("away_score"),
        home_score=raw.get("home_score"),
        player_stats=raw.get("player_stats", []),
        plays=raw.get("plays", []),
        provenance=prov,
    )


def ingest_schedule_snapshot(
    team_slug: str,
    team_id: int,
    season: int,
    sample_name: Optional[str] = None,
) -> List[PFFScheduleEntry]:
    """
    Parse a public PFF team schedule page (or sample) into typed PFFScheduleEntry records.
    """
    scraper = ScheduleScraper(cache_enabled=True)
    html = scraper.load_sample(sample_name) if sample_name else scraper.get(
        f"https://www.pff.com/nfl/teams/{team_slug}/{team_id}/schedule"
    )

    raw_games = scraper.parse_team_schedule(html, team_slug, season)

    prov = PFFProvenance(
        source="pff_public_schedule",
        page_url=f"https://www.pff.com/nfl/teams/{team_slug}/{team_id}/schedule",
        sample_name=sample_name,
    )

    typed = []
    for g in raw_games:
        typed.append(
            PFFScheduleEntry(
                season=g.get("season", season),
                week=g.get("week"),
                team=g.get("team", team_slug),
                opponent=g.get("opponent", ""),
                is_home=g.get("is_home", False),
                date_text=g.get("date_text"),
                url=g.get("url"),
                provenance=prov,
            )
        )
    return typed
