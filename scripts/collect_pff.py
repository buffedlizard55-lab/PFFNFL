#!/usr/bin/env python3
"""
PFF Data Collection Script

Collects public PFF data and writes it using typed models + partitioned layout
suitable as a reliable source for NFL prediction backtesting.

Usage examples:
    python scripts/collect_pff.py --season 2026 --team buffalo-bills 4
    python scripts/collect_pff.py --season 2026 --all-teams --sample
"""
import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from pff_data.ingest import ingest_roster_snapshot, ingest_lineup_snapshot, ingest_schedule_snapshot
from pff_data.writer import write_rosters, write_lineups, write_schedule, write_run_manifest
from pff_data.models import PFFCollectionRun
from scrapers.teams import TeamScraper


def main():
    parser = argparse.ArgumentParser(description="Collect public PFF data for backtesting")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", default=None, help="Week identifier (e.g. '1', 'P1')")
    parser.add_argument("--team", nargs=2, metavar=("SLUG", "ID"), help="Single team: slug id")
    parser.add_argument("--all-teams", action="store_true")
    parser.add_argument("--sample", action="store_true", help="Use local samples instead of network")
    args = parser.parse_args()

    run_id = str(uuid.uuid4())[:8]
    started = datetime.now(timezone.utc)

    print(f"=== PFF Collection Run {run_id} ===")
    print(f"Season: {args.season}  Week: {args.week or 'roster-snapshot'}")
    print(f"Mode: {'SAMPLE' if args.sample else 'NETWORK'}")

    teams_to_collect = []

    if args.team:
        slug, tid = args.team
        teams_to_collect.append((slug, int(tid)))
    elif args.all_teams:
        ts = TeamScraper(cache_enabled=True)
        teams = ts.fetch_teams()
        teams_to_collect = [(t["slug"], t["id"]) for t in teams]
        print(f"Collecting all {len(teams_to_collect)} teams...")
    else:
        print("No teams specified. Use --team or --all-teams")
        return

    all_rosters = []
    all_lineups = []
    all_schedules = []
    errors = []

    sample_map = {
        "buffalo-bills": "bills_roster_real_2026",
    }
    lineup_sample = "bills_lineup_test" if args.sample else None
    schedule_sample = "bills_schedule_sample_2026" if args.sample else None

    for slug, tid in teams_to_collect:
        try:
            print(f"  → {slug} ...", end=" ", flush=True)

            sample_name = sample_map.get(slug) if args.sample else None

            rosters = ingest_roster_snapshot(
                team_slug=slug,
                team_id=tid,
                season=args.season,
                week=args.week,
                sample_name=sample_name,
            )
            all_rosters.extend(rosters)

            lineups = ingest_lineup_snapshot(
                team_slug=slug,
                team_id=tid,
                season=args.season,
                week=args.week,
                sample_name=lineup_sample if "bills" in slug else None,
            )
            all_lineups.extend(lineups)

            # Schedule integration (sample-driven for now)
            sched_sample = schedule_sample if "bills" in slug and args.sample else None
            if sched_sample or not args.sample:  # allow for future network
                try:
                    schedules = ingest_schedule_snapshot(
                        team_slug=slug,
                        team_id=tid,
                        season=args.season,
                        sample_name=sched_sample,
                    )
                    all_schedules.extend(schedules)
                    print(f"roster={len(rosters)} lineup={len(lineups)} schedule={len(schedules)}")
                except Exception as se:
                    print(f"roster={len(rosters)} lineup={len(lineups)} schedule=ERR:{se}")
                    errors.append(f"{slug} schedule: {se}")
            else:
                print(f"roster={len(rosters)} lineup={len(lineups)}")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(f"{slug}: {e}")

    # Write partitioned data
    if all_rosters:
        path = write_rosters(all_rosters, args.season, args.week)
        print(f"\nWrote rosters → {path}")

    if all_lineups:
        path = write_lineups(all_lineups, args.season, args.week)
        print(f"Wrote lineups → {path}")

    if all_schedules:
        path = write_schedule(all_schedules, args.season, args.week)
        print(f"Wrote schedule → {path}")

    # Write run manifest (for audit / reproducibility)
    run = PFFCollectionRun(
        run_id=run_id,
        started_at=started,
        completed_at=datetime.now(timezone.utc),
        season=args.season,
        weeks=[args.week] if args.week else [],
        teams_scraped=len(teams_to_collect) - len(errors),
        players_collected=len(all_rosters),
        errors=errors,
    )
    manifest_path = write_run_manifest(run)
    print(f"Wrote manifest → {manifest_path}")

    print(f"\nCollection complete. Players collected: {len(all_rosters)}")


if __name__ == "__main__":
    main()
