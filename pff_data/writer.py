"""
Writer utilities for PFF data.

Saves typed PFF records in a backtest-friendly layout:

data/processed/pff/
    season=2025/
        week=1/
            rosters.parquet
            lineups.parquet
        week=P1/
            ...
    season=2026/
        ...
    _manifest/
        runs/
            2026-08-17T12-00-00Z.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Iterable

import pandas as pd

from .models import PFFPlayerRoster, PFFLineupSnapshot, PFFCollectionRun, PFFGameSnapshot, PFFScheduleEntry


BASE_DIR = Path("data/processed/pff")


def _season_week_path(season: int, week: str | None = None) -> Path:
    season_dir = BASE_DIR / f"season={season}"
    if week:
        return season_dir / f"week={week}"
    return season_dir


def write_rosters(records: List[PFFPlayerRoster], season: int, week: str | None = None) -> Path:
    if not records:
        return Path()

    df = pd.DataFrame([r.model_dump() for r in records])
    # Flatten provenance for Parquet friendliness
    if "provenance" in df.columns:
        prov = pd.json_normalize(df.pop("provenance"))
        df = pd.concat([df, prov.add_prefix("provenance_")], axis=1)

    out_dir = _season_week_path(season, week)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rosters.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def write_lineups(records: List[PFFLineupSnapshot], season: int, week: str | None = None) -> Path:
    if not records:
        return Path()

    df = pd.DataFrame([r.model_dump() for r in records])
    if "provenance" in df.columns:
        prov = pd.json_normalize(df.pop("provenance"))
        df = pd.concat([df, prov.add_prefix("provenance_")], axis=1)

    out_dir = _season_week_path(season, week)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lineups.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def write_run_manifest(run: PFFCollectionRun) -> Path:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_dir = BASE_DIR / "_manifest" / "runs"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    ts = run.started_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = manifest_dir / f"{ts}.json"
    path.write_text(run.model_dump_json(indent=2))
    return path


def load_rosters(season: int, week: str | None = None) -> pd.DataFrame:
    path = _season_week_path(season, week) / "rosters.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def write_games(records: List[PFFGameSnapshot], season: int, week: str | None = None) -> Path:
    """Write typed game snapshots (score + participation stats) to the season-root layout."""
    if not records:
        return Path()

    df = pd.DataFrame([r.model_dump() for r in records])

    # Flatten provenance
    if "provenance" in df.columns:
        prov = pd.json_normalize(df.pop("provenance"))
        df = pd.concat([df, prov.add_prefix("provenance_")], axis=1)

    # Serialize complex fields for Parquet
    for col in ("player_stats", "plays"):
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else (x or "[]"))

    out_dir = _season_week_path(season, week)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "games.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def write_schedule(records: List[PFFScheduleEntry], season: int, week: str | None = None) -> Path:
    """Write typed schedule entries to the season-root layout."""
    if not records:
        return Path()

    df = pd.DataFrame([r.model_dump() for r in records])

    if "provenance" in df.columns:
        prov = pd.json_normalize(df.pop("provenance"))
        df = pd.concat([df, prov.add_prefix("provenance_")], axis=1)

    out_dir = _season_week_path(season, week)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "schedule.parquet"
    df.to_parquet(out_path, index=False)
    return out_path
