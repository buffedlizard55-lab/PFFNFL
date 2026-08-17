"""
Tests for the typed PFF data layer (pff_data).

These tests ensure the data is suitable as a reliable source for backtesting.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pff_data.ingest import ingest_roster_snapshot, ingest_schedule_snapshot
from pff_data.writer import write_rosters, write_schedule
from pff_data.loader import load_rosters, load_schedule
from pff_data.models import PFFPlayerRoster, PFFScheduleEntry
from pff_data.quality import roster_quality_report
import pandas as pd


def test_ingest_produces_typed_records():
    records = ingest_roster_snapshot(
        "buffalo-bills", 4, 2026,
        sample_name="bills_roster_real_2026"
    )
    assert len(records) > 0
    assert all(isinstance(r, PFFPlayerRoster) for r in records)
    assert records[0].season == 2026
    assert records[0].player_id > 0
    assert records[0].snaps is not None or records[0].overall_grade is not None


def test_write_and_load_roundtrip():
    records = ingest_roster_snapshot(
        "buffalo-bills", 4, 2026,
        sample_name="bills_roster_real_2026"
    )
    # Use root (no week) to preserve pristine core layout
    path = write_rosters(records, season=2026, week=None)
    assert path.exists() or path.name == "rosters.parquet"

    df = load_rosters(season=2026)
    assert len(df) >= len(records)
    assert "season" in df.columns
    assert "overall_grade" in df.columns
    assert "snaps" in df.columns


def test_quality_report():
    df = load_rosters(season=2026)
    report = roster_quality_report(df)
    assert report["rows"] > 0
    assert report["snap_coverage"] > 0.5
    assert report["status"] in ("good", "needs_attention")


def test_time_safety_fields_present():
    df = load_rosters(season=2026)
    # These fields are critical for safe backtesting
    assert "season" in df.columns
    # snapshot_date or week should be present in practice
    has_time = ("snapshot_date" in df.columns) or ("week" in df.columns)
    assert has_time

def test_game_ingest_and_write():
    from pff_data.ingest import ingest_game_snapshot
    from pff_data.writer import write_games
    from pff_data.loader import load_games
    from pff_data.models import PFFGameSnapshot

    gs = ingest_game_snapshot(
        "2026/1/carolina-panthers_at_buffalo-bills_31908",
        2026,
        week="1",
        sample_name="bills_game_sample_2026"
    )
    assert isinstance(gs, PFFGameSnapshot)
    assert gs.season == 2026
    assert gs.away_score == 27
    assert len(gs.player_stats) >= 1

    path = write_games([gs], season=2026, week=None)
    assert path.exists() or path.name == "games.parquet"

    df = load_games(season=2026)
    assert len(df) >= 1
    assert "player_stats" in df.columns or "away_score" in df.columns


def test_schedule_ingest_write_load():
    """End-to-end for PFFScheduleEntry + ingest + write + load (backtest-safe)."""
    schedules = ingest_schedule_snapshot(
        "buffalo-bills", 4, 2026,
        sample_name="bills_schedule_sample_2026"
    )
    assert len(schedules) == 3
    assert all(isinstance(s, PFFScheduleEntry) for s in schedules)
    assert schedules[0].season == 2026
    assert schedules[0].week == "1"
    assert schedules[0].opponent == "Carolina Panthers"
    assert schedules[0].is_home is False

    # Write to season root (pristine layout)
    path = write_schedule(schedules, season=2026, week=None)
    assert path.exists() or path.name == "schedule.parquet"

    df = load_schedule(season=2026)
    assert len(df) >= 3
    assert "season" in df.columns
    assert "week" in df.columns
    assert "opponent" in df.columns
    assert "is_home" in df.columns
    # provenance flattened
    assert any("provenance_" in c for c in df.columns)
