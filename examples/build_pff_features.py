#!/usr/bin/env python3
"""
Example: Building time-aware features from PFF data for backtesting.

This shows the intended usage pattern:
- Load PFF data by season/week (never future data)
- Create lag features safely
- Prepare a feature matrix that can be joined with game outcomes
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from pff_data.loader import load_rosters


def main():
    print("=== Building PFF Features for Backtesting ===\n")

    # Load historical PFF roster data
    df = load_rosters(season=2026)

    if df.empty:
        print("No data found. Run collection first.")
        return

    print(f"Loaded {len(df)} player-week observations")

    # Example: Create simple team-level features from PFF grades + snaps
    # (In real use you would do this per week, then lag)
    team_features = (
        df.groupby(["season", "team"])
        .agg(
            avg_grade=("overall_grade", "mean"),
            total_snaps=("snaps", "sum"),
            qb_grade=("overall_grade", lambda x: x[df.loc[x.index, "position"] == "QB"].mean() if "QB" in df.loc[x.index, "position"].values else None),
            num_players=("player_id", "nunique"),
        )
        .reset_index()
    )

    print("\nTeam-level PFF features (example):")
    print(team_features.head().to_string(index=False))

    print("\nUsage pattern for backtesting:")
    print("  1. Load PFF features up to week T")
    print("  2. Join with game outcomes for week T+1")
    print("  3. Never use future PFF data to predict past games")
    print("  4. Use manifest files in data/processed/pff/_manifest/runs/ for reproducibility")

    # In a real pipeline you would save this as features_2026.parquet
    out = Path("data/processed/pff/season=2026/team_features_example.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    team_features.to_parquet(out, index=False)
    print(f"\nSaved example features → {out}")


if __name__ == "__main__":
    main()
