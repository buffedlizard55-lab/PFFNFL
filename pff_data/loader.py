"""
Data loader for PFF data prepared for backtesting.

Provides convenient functions to load PFF data in a time-aware way
so that features can be built without future leakage.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Iterable

import pandas as pd

BASE = Path("data/processed/pff")


def list_available_seasons() -> List[int]:
    seasons = []
    for p in BASE.glob("season=*"):
        try:
            seasons.append(int(p.name.split("=")[1]))
        except (ValueError, IndexError):
            pass
    return sorted(seasons)


def load_rosters(
    season: Optional[int] = None,
    weeks: Optional[Iterable[str]] = None,
    teams: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """
    Load roster data.

    Parameters
    ----------
    season : int or None
        If None, loads all seasons.
    weeks : iterable of str or None
        e.g. ["1", "2", "P1"]. If None, loads all weeks for the season(s).
    teams : iterable of str or None
        Filter by team slug.
    """
    frames = []

    season_dirs = [BASE / f"season={season}"] if season else sorted(BASE.glob("season=*"))

    for sdir in season_dirs:
        if not sdir.exists():
            continue

        week_dirs = (
            [sdir / f"week={w}" for w in weeks]
            if weeks
            else sorted(sdir.glob("week=*")) + [sdir]   # also check root for roster snapshots
        )

        for wdir in week_dirs:
            path = wdir / "rosters.parquet"
            if path.exists():
                df = pd.read_parquet(path)
                frames.append(df)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    if teams:
        team_set = set(teams)
        df = df[df["team"].isin(team_set)]

    # Ensure time columns exist for backtesting
    if "season" not in df.columns:
        df["season"] = season

    # Deduplicate by the most stable key when the same player appears
    # in multiple week folders from repeated collections
    key_cols = ["season", "team", "player_id"]
    if all(c in df.columns for c in key_cols):
        df = df.drop_duplicates(subset=key_cols, keep="last")

    return df.sort_values(["season", "snapshot_date", "team", "position"]).reset_index(drop=True)


def load_lineups(season: Optional[int] = None, weeks: Optional[Iterable[str]] = None) -> pd.DataFrame:
    frames = []
    season_dirs = [BASE / f"season={season}"] if season else sorted(BASE.glob("season=*"))

    for sdir in season_dirs:
        week_dirs = (
            [sdir / f"week={w}" for w in weeks] if weeks else sorted(sdir.glob("week=*"))
        )
        for wdir in week_dirs:
            path = wdir / "lineups.parquet"
            if path.exists():
                frames.append(pd.read_parquet(path))

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

def load_games(season: Optional[int] = None, weeks: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Load game snapshots (scores + player participation/box stats)."""
    frames = []
    season_dirs = [BASE / f"season={season}"] if season else sorted(BASE.glob("season=*"))

    for sdir in season_dirs:
        week_dirs = (
            [sdir / f"week={w}" for w in weeks] if weeks else sorted(sdir.glob("week=*")) + [sdir]
        )
        for wdir in week_dirs:
            path = wdir / "games.parquet"
            if path.exists():
                df = pd.read_parquet(path)
                frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_schedule(season: Optional[int] = None, weeks: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Load schedule entries."""
    frames = []
    season_dirs = [BASE / f"season={season}"] if season else sorted(BASE.glob("season=*"))

    for sdir in season_dirs:
        week_dirs = (
            [sdir / f"week={w}" for w in weeks] if weeks else sorted(sdir.glob("week=*")) + [sdir]
        )
        for wdir in week_dirs:
            path = wdir / "schedule.parquet"
            if path.exists():
                df = pd.read_parquet(path)
                frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
