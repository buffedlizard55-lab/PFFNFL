# PFFNFL

**Sole Purpose:** Reverse engineer **Pro Football Focus (PFF.com)** as a reliable source of **public** NFL data.

This project is **100% focused on PFF.com only**.

## Current Working Extraction (Public Pages)

### Rosters (`/nfl/teams/{slug}/{id}/roster`)
- Player identity (`player_id`, `slug`, `name`, `url`)
- Position + jersey number
- PFF grades (`overall_grade` + facets like `pass_grade` when visible)
- **Snap counts** (when shown on public roster pages)
- Basic bio (`age`, `college`, `draft_year` / `round` / `pick`)

Example output:
```
Josh Allen            | QB #17 | Grade:90.6 | Snaps:237 | Age:30.2
Dalton Kincaid        | TE #86 | Grade:86.7 | Snaps:368 | Age:26.8
...
```

### Lineups / Depth Charts (`/nfl/teams/{slug}/{id}/lineup`)
- Offense and defense units
- Basic personnel package detection

### Supporting Capabilities
- Heavy HTML caching (essential for reverse engineering)
- `__NEXT_DATA__` JSON extraction (often contains the cleanest structured data)
- Sample-driven development (works completely offline)
- Clean parser classes + verification tools

**We only use publicly available pages.** Premium / PFF+ data is out of scope.

## Project Structure

```
PFFNFL/
├── scrapers/
│   ├── base.py          # PFFScraper (caching + __NEXT_DATA__)
│   ├── roster.py        # Best working parser
│   ├── lineup.py
│   ├── player.py
│   ├── game.py
│   ├── schedule.py
│   └── teams.py
├── scripts/
│   ├── capture_pff.py           # Capture + inspect any PFF page
│   ├── fetch_pff_team.py        # Fetch roster + lineup for a team
│   └── verify_pff.py            # Full health check
├── tests/
│   └── test_pff_parsers.py
├── data/samples/                # Saved HTML for offline RE work
├── PFF_REVERSE_ENGINEERING.md
├── PFF_STATUS.md
└── README.md
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify everything is working
python scripts/verify_pff.py

# Capture a new page for reverse engineering
python scripts/capture_pff.py \
  --url "https://www.pff.com/nfl/teams/buffalo-bills/4/roster" \
  --name bills_roster_2026 \
  --inspect --next

# Parse a sample
python -c "
from scrapers.roster import RosterScraper
r = RosterScraper()
players = r.parse_roster(r.load_sample('bills_roster_2026'), 'buffalo-bills', 4)
print(len(players), 'players')
print(players[0])
"
```

## Reverse Engineering Workflow

1. Capture a page:
   ```bash
   python scripts/capture_pff.py --url "..." --name my_page --inspect
   ```

2. Look for `__NEXT_DATA__` (often the best data source):
   ```bash
   python scripts/capture_pff.py --sample my_page --next
   ```

3. Improve the parser against the saved sample (in `data/samples/`).

4. Re-run `python scripts/verify_pff.py` and `python tests/test_pff_parsers.py`.

## Current Status

See:
- `PFF_STATUS.md` — what is currently working
- `PFF_REVERSE_ENGINEERING.md` — patterns and techniques discovered

## Ethics & Rules

- Only public pages
- Aggressive caching + rate limiting
- Never use paid cookies or premium endpoints
- All development is sample-driven and reproducible

Contributions that improve PFF public data extraction are welcome.
