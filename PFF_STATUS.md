# PFFNFL - Current Reverse Engineering Status

**Mission:** Make public Pro Football Focus data a reliable, structured source.

## What Works Today (Public Pages)

### Roster Extraction (`/nfl/teams/{slug}/{id}/roster`)
- Player identity (player_id, slug, name, URL)
- Position + Jersey number
- PFF Grades (overall + pass/run/receiving when visible)
- **Snap counts** (season totals when shown)
- Bio data (age, height, college, draft year/round/pick)

Example output from public Bills roster:
- Josh Allen: QB #17, Grade 90.6, 237 snaps, Age 30.2, Wyoming, 2018 1st rd
- Dalton Kincaid: TE #86, Grade 86.7, 368 snaps

### Lineup / Depth Chart (`/nfl/teams/{slug}/{id}/lineup`)
- Offense and Defense units
- Basic personnel package detection (11, 12, Nickel, etc.)

### Supporting Infrastructure
- `PFFScraper` base with heavy caching + `__NEXT_DATA__` extraction
- Sample-driven development (`data/samples/`)
- `scripts/capture_pff.py` — capture + inspect any page
- `scripts/fetch_pff_team.py` — fetch roster + lineup for a team

## High-Value Next Targets (PFF Only)

1. **Better Snap Count / Usage Data**
   - Weekly "Usage and Production" articles
   - Preseason depth chart articles
   - Game participation from box scores

2. **__NEXT_DATA__ Mining**
   - Many PFF pages preload a large JSON blob. This is often cleaner than HTML parsing.

3. **Player Profiles** (`/nfl/players/{slug}/{id}`)
   - Advanced stats (aDOT, big-time throws, pressures allowed, etc.)
   - Historical grades

4. **Game Pages + Participation**
   - `/nfl/scores/{season}/{week}/{game}`

5. **Depth Charts** (fantasy depth + official lineup pages)

## Workflow (Recommended)

```bash
# Capture a new page for analysis
python scripts/capture_pff.py \
  --url "https://www.pff.com/nfl/teams/buffalo-bills/4/roster" \
  --name bills_roster_2026 \
  --inspect

# Inspect __NEXT_DATA__ if present
python scripts/capture_pff.py --sample bills_roster_2026 --next

# Parse using existing code
python -c "
from scrapers.roster import RosterScraper
r = RosterScraper()
players = r.parse_roster(r.load_sample('bills_roster_2026'), 'buffalo-bills', 4)
print(len(players), 'players')
"
```

All development is done against saved samples so it works offline and is reproducible.

## Rules for This Project
- 100% focused on PFF.com public pages
- No nflverse, ESPN, PFR, etc. (those are separate projects)
- Respect rate limits + heavy caching
- Document every pattern in PFF_REVERSE_ENGINEERING.md
