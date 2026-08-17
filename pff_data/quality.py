"""
Data quality utilities for PFF data used in backtesting.

Helps ensure the collected data is suitable as a reliable feature source.
"""
from __future__ import annotations

from typing import Dict, Any
import pandas as pd


def roster_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a simple quality report for roster data.
    """
    if df.empty:
        return {"rows": 0, "status": "empty"}

    report = {
        "rows": len(df),
        "unique_teams": df["team"].nunique() if "team" in df.columns else 0,
        "unique_players": df["player_id"].nunique() if "player_id" in df.columns else 0,
        "seasons": sorted(df["season"].unique()) if "season" in df.columns else [],
        "snap_coverage": float(df["snaps"].notna().mean()) if "snaps" in df.columns else 0.0,
        "grade_coverage": float(df["overall_grade"].notna().mean()) if "overall_grade" in df.columns else 0.0,
        "missing_critical": [],
    }

    critical = ["player_id", "name", "position", "team", "season"]
    for c in critical:
        if c in df.columns and df[c].isna().any():
            report["missing_critical"].append(c)

    report["status"] = "good" if not report["missing_critical"] and report["snap_coverage"] > 0.7 else "needs_attention"
    return report


def print_quality_report(df: pd.DataFrame, title: str = "PFF Roster Data"):
    report = roster_quality_report(df)
    print(f"\n=== {title} Quality Report ===")
    for k, v in report.items():
        print(f"  {k}: {v}")
    print()
