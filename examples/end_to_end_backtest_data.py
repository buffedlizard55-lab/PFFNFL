#!/usr/bin/env python3
"""
End-to-end example: From raw PFF scraping to backtest-ready features.

This is the intended workflow for using PFFNFL as the reliable data source
for an NFL outcome prediction model.

Steps:
1. Collect public PFF data (via samples or network)
2. Ingest into typed, provenance-rich models
3. Write to time-partitioned Parquet (season=YYYY/week=XX/)
4. Load safely for feature engineering
5. Produce model-ready features (no future leakage)
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from pff_data.ingest import ingest_roster_snapshot
from pff_data.writer import write_rosters
from pff_data.loader import load_rosters
import pandas as pd


def main():
    print("=" * 70)
    print("PFFNFL → Reliable Data Source for NFL Prediction Backtesting")
    print("=" * 70)

    SEASON = 2026

    # === 1. Collect / Ingest ===
    print("\n[1] Ingesting PFF roster data (using sample for reproducibility)...")
    players = ingest_roster_snapshot(
        team_slug="buffalo-bills",
        team_id=4,
        season=SEASON,
        snapshot_date="2026-08-17",
        sample_name="bills_roster_real_2026",
    )
    print(f"    Ingested {len(players)} typed player records")

    # === 2. Write partitioned ===
    print("\n[2] Writing to backtest-friendly layout...")
    roster_path = write_rosters(players, season=SEASON)
    print(f"    Written: {roster_path}")

    # === 3. Load for modeling ===
    print("\n[3] Loading data for feature engineering (time-safe)...")
    df = load_rosters(season=SEASON)
    print(f"    Loaded {len(df)} rows")

    # === 4. Build safe features ===
    print("\n[4] Building example team-level features...")
    team_feats = (
        df.groupby(["season", "team"])
        .agg(
            team_avg_pff_grade=("overall_grade", "mean"),
            total_player_snaps=("snaps", "sum"),
            roster_size=("player_id", "nunique"),
            qb_grade=("overall_grade", lambda x: x[df.loc[x.index, "position"] == "QB"].mean()),
        )
        .reset_index()
    )

    # In real backtesting you would:
    # - Load only up to week T
    # - Create lags (e.g. last 4 weeks avg grade)
    # - Join with game results on (season, week, team)

    print(team_feats.to_string(index=False))

    # Save features
    feat_path = Path(f"data/processed/pff/season={SEASON}/team_features.parquet")
    feat_path.parent.mkdir(parents=True, exist_ok=True)
    team_feats.to_parquet(feat_path, index=False)
    print(f"\n    Saved features → {feat_path}")

    print("\n" + "=" * 70)
    print("Ready for backtesting pipeline:")
    print("  - Time-partitioned data")
    print("  - Full provenance in manifest files")
    print("  - Typed records (no schema drift)")
    print("  - Safe for lag features and point-in-time joins")
    print("=" * 70)


if __name__ == "__main__":
    main()
