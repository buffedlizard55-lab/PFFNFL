# pff_data — Typed PFF Data Layer for Backtesting

This package turns raw PFF scraper output into a **reliable, time-aware, provenance-rich** data source suitable for building features for NFL outcome prediction models.

## Philosophy

- **Time safety first**: Every record must carry `season`, `week`, or `snapshot_date`.
- **Provenance**: Every record knows where and when it came from.
- **Typed + validated**: Pydantic models prevent silent schema drift.
- **Partitioned storage**: `season=YYYY/week=XX/` layout makes it hard to accidentally leak future data.
- **Reproducible**: Collection runs are recorded in `_manifest/runs/`.

## Recommended Workflow

```python
from pff_data.ingest import ingest_roster_snapshot
from pff_data.writer import write_rosters
from pff_data.loader import load_rosters
from pff_data.quality import print_quality_report

# 1. Ingest (from live scrape or sample)
players = ingest_roster_snapshot(
    team_slug="buffalo-bills",
    team_id=4,
    season=2026,
    week="1",
    sample_name="..."   # or omit for network
)

# 2. Write to partitioned storage
write_rosters(players, season=2026, week="1")

# 3. Load safely for feature engineering
df = load_rosters(season=2026, weeks=["1", "2"])

# 4. Check quality
print_quality_report(df)
```

## Key Files

- `models.py` — Core Pydantic models (`PFFPlayerRoster`, `PFFLineupSnapshot`, etc.)
- `ingest.py` — Bridge from scrapers → typed models
- `writer.py` — Writes to `data/processed/pff/season=.../week=.../`
- `loader.py` — Time-aware loading (critical for backtesting)
- `quality.py` — Simple data quality reports

## Storage Layout

```
data/processed/pff/
├── season=2026/
│   ├── week=1/
│   │   ├── rosters.parquet
│   │   └── lineups.parquet
│   └── week=roster-snapshot/
│       └── rosters.parquet
├── _manifest/
│   └── runs/
│       └── 2026-08-17T17-27-22Z.json
```

## Backtesting Safety Rules

1. Always load with explicit `season` and `weeks`.
2. Never train on data whose `snapshot_date` or `week` is after the target game.
3. Use the manifest files to record exactly which collection run was used for each experiment.
4. Prefer `PFFPlayerRoster` over raw dicts when building features.

This layer makes PFFNFL suitable as the **primary data source** for a serious NFL prediction backtesting system.
