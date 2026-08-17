# PFF Reverse Engineering Guide

This document is the central place for all knowledge about scraping public data from profootballfocus.com.

## Current Focus
- **Only** public pages (no login / premium cookies)
- Rosters, lineups/depth charts, schedules, player profiles, game pages
- Snap counts (the holy grail for prediction models)
- Player grades and usage when visible publicly

## Observed Page Structures (2026)

### Roster Page: `/nfl/teams/{slug}/{id}/roster`
- Heavy use of `<a href="/nfl/players/...">` links
- Data is often in flat text or inside `<tr>` / card-like `<div>`
- Grades appear as `90.6 84.2 90.8` sequences or with labels (`Pass`, `Run`, etc.)
- Snap counts appear as large numbers (e.g. `1,175`)
- Bio info (age, height, college, draft) is usually at the end of each player's block

### Lineup Page: `/nfl/teams/{slug}/{id}/lineup`
- Shows current offensive and defensive units
- Personnel packages (11, 12, Nickel, Base, etc.)
- Player names with jersey numbers

### Game Page: `/nfl/scores/{season}/{week}/{matchup}`
- Score
- Play-by-play text
- Player participation hints

### Player Page: `/nfl/players/{slug}/{id}`
- Season grades
- Advanced stats (aDOT, big time throws, etc. when public)
- Bio + career

## Useful Reverse Engineering Techniques

1. **Capture real HTML**
   ```bash
   python scripts/capture_pff.py --url "https://www.pff.com/nfl/teams/buffalo-bills/4/roster" --name bills_roster_2026
   ```

2. **Inspect structure**
   ```bash
   python scripts/capture_pff.py --sample bills_roster_2026 --inspect --next
   ```

3. **Look for `__NEXT_DATA__`**
   Many PFF pages preload a large JSON blob with all the data. This is often the cleanest source.

4. **Text slicing between player anchors**
   Because markup is inconsistent, the most reliable method is:
   - Find all `/nfl/players/` links
   - Slice the page text between consecutive players

## Snap Counts Strategy

Public snap counts are the hardest but most valuable data.

Current approaches:
- Large numbers near player names on rosters (season totals)
- "Usage and Production" news articles (weekly)
- Preseason depth chart articles (snap shares)
- Game pages (sometimes list snaps played)

## Next Priorities (PFF-only)

- [ ] Robust roster parser with per-player text slicing
- [ ] Lineup / depth chart parser
- [ ] Player profile enrichment
- [ ] Game box score + basic participation
- [ ] Weekly snap count / usage extractor from articles
- [ ] Detection + extraction of `__NEXT_DATA__` JSON
- [ ] Historical backfill support (by season)

## Rules

- Never use paid cookies or premium endpoints
- Always cache aggressively
- Keep samples in `data/samples/` for offline development
- Document every new pattern discovered here
