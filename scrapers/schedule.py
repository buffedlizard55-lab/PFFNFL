"""
Schedule & scores scraper.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import PFFScraper


class ScheduleScraper(PFFScraper):
    def fetch_team_schedule(self, team_slug: str, team_id: int, season: int = 2026) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/nfl/teams/{team_slug}/{team_id}/schedule"
        html = self.get(url)
        return self.parse_team_schedule(html, team_slug, season)

    def fetch_scores_page(self, week: str = "1", season: int = 2026) -> List[Dict[str, Any]]:
        """Scrape the main scores page for a given week."""
        url = f"{self.base_url}/nfl/scores?week={week}"
        # or /nfl/scores/2026/1/...
        html = self.get(url)
        return self.parse_scores(html, season)

    def parse_team_schedule(self, html: str, team_slug: str, season: int) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        games = []

        # Look for week links and scores
        # From observed pages: links like /nfl/scores/2026/1/buffalo-bills_at_houston-texans_30612
        game_links = soup.select('a[href*="/nfl/scores/"]')

        for link in game_links:
            href = link.get("href", "")
            if "/nfl/scores/" not in href:
                continue

            text = link.get_text(" ", strip=True)
            # Typical pattern: "1 — Sun, Sep 13, 1:00 PM View Game at Houston Texans"
            match = re.search(r"(\d+|P\d+)\s*—\s*(.+?)\s+(at|vs)\s+(.+?)\s*$", text)
            if not match:
                continue

            week, date_str, home_away, opponent = match.groups()

            game = {
                "season": season,
                "week": week,
                "team": team_slug,
                "opponent": opponent.strip(),
                "is_home": "at" not in home_away.lower(),
                "date_text": date_str.strip(),
                "url": f"https://www.pff.com{href}",
            }
            games.append(game)

        return games

    def parse_scores(self, html: str, season: int) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        games = []

        # Look for game containers. PFF shows matchups with times
        # Rough parse of visible game blocks
        for matchup in soup.select('a[href*="/nfl/scores/"]'):
            href = matchup.get("href", "")
            if "/nfl/scores/" not in href:
                continue

            full_text = matchup.get_text(" ", strip=True)
            # Example patterns from page:
            # "Bills 0-0 • ATS 0-0 Texans 0-0 • ATS 0-0 1:00p CBS/P1 Pick"
            teams = re.findall(r"([A-Z][a-zA-Z\s]+?)(?:\s+\d+-\d+|\s*$)", full_text)
            if len(teams) >= 2:
                away, home = teams[0].strip(), teams[1].strip()
                games.append({
                    "season": season,
                    "away_team": away,
                    "home_team": home,
                    "url": f"https://www.pff.com{href}",
                    "raw": full_text[:200],
                })

        return games
