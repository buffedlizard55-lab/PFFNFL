"""
Team list scraper for PFF.
"""
from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import PFFScraper


class TeamScraper(PFFScraper):
    TEAMS_URL = "/nfl/teams"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def fetch_teams(self) -> List[Dict[str, Any]]:
        """Return list of teams with name, slug, id, conference, division."""
        url = f"{self.base_url}{self.TEAMS_URL}"
        html = self.get(url)
        soup = BeautifulSoup(html, "lxml")

        teams: List[Dict[str, Any]] = []

        # Strategy 1: Look for links like /nfl/teams/{team-slug}/{id}
        links = soup.select('a[href*="/nfl/teams/"]')
        seen = set()

        for link in links:
            href = link.get("href", "")
            if "/nfl/teams/" not in href or href.count("/") < 4:
                continue

            parts = href.strip("/").split("/")
            if len(parts) < 4:
                continue

            slug = parts[2]
            try:
                team_id = int(parts[3])
            except (ValueError, IndexError):
                continue

            name = link.get_text(strip=True)
            if not name or name in seen:
                continue

            seen.add(name)

            # Try to extract conference/division from surrounding context or text
            parent = link.parent or link
            section_text = ""
            for ancestor in [parent, parent.parent, parent.parent.parent if parent.parent else None]:
                if ancestor:
                    section_text += ancestor.get_text(" ", strip=True)[:200]

            conf = "AFC" if "AFC" in section_text else ("NFC" if "NFC" in section_text else None)
            div = None
            for d in ["East", "North", "South", "West"]:
                if d in section_text:
                    div = d
                    break

            teams.append({
                "name": name,
                "slug": slug,
                "id": team_id,
                "conference": conf,
                "division": div,
                "url": f"https://www.pff.com{href}",
            })

        # Fallback: Hardcoded 2026 teams (in case of heavy JS or network issues)
        if len(teams) < 20:
            print("[teams] Using hardcoded fallback list (network / parsing issue)")
            teams = self._hardcoded_teams()

        return teams

    def _hardcoded_teams(self) -> List[Dict[str, Any]]:
        """Fallback list of all 32 teams (2026 season)."""
        return [
            {"name": "Arizona Cardinals", "slug": "arizona-cardinals", "id": 1, "conference": "NFC", "division": "West"},
            {"name": "Atlanta Falcons", "slug": "atlanta-falcons", "id": 2, "conference": "NFC", "division": "South"},
            {"name": "Baltimore Ravens", "slug": "baltimore-ravens", "id": 3, "conference": "AFC", "division": "North"},
            {"name": "Buffalo Bills", "slug": "buffalo-bills", "id": 4, "conference": "AFC", "division": "East"},
            {"name": "Carolina Panthers", "slug": "carolina-panthers", "id": 5, "conference": "NFC", "division": "South"},
            {"name": "Chicago Bears", "slug": "chicago-bears", "id": 6, "conference": "NFC", "division": "North"},
            {"name": "Cincinnati Bengals", "slug": "cincinnati-bengals", "id": 7, "conference": "AFC", "division": "North"},
            {"name": "Cleveland Browns", "slug": "cleveland-browns", "id": 8, "conference": "AFC", "division": "North"},
            {"name": "Dallas Cowboys", "slug": "dallas-cowboys", "id": 9, "conference": "NFC", "division": "East"},
            {"name": "Denver Broncos", "slug": "denver-broncos", "id": 10, "conference": "AFC", "division": "West"},
            {"name": "Detroit Lions", "slug": "detroit-lions", "id": 11, "conference": "NFC", "division": "North"},
            {"name": "Green Bay Packers", "slug": "green-bay-packers", "id": 12, "conference": "NFC", "division": "North"},
            {"name": "Houston Texans", "slug": "houston-texans", "id": 13, "conference": "AFC", "division": "South"},
            {"name": "Indianapolis Colts", "slug": "indianapolis-colts", "id": 14, "conference": "AFC", "division": "South"},
            {"name": "Jacksonville Jaguars", "slug": "jacksonville-jaguars", "id": 15, "conference": "AFC", "division": "South"},
            {"name": "Kansas City Chiefs", "slug": "kansas-city-chiefs", "id": 16, "conference": "AFC", "division": "West"},
            {"name": "Las Vegas Raiders", "slug": "las-vegas-raiders", "id": 23, "conference": "AFC", "division": "West"},
            {"name": "Los Angeles Chargers", "slug": "los-angeles-chargers", "id": 27, "conference": "AFC", "division": "West"},
            {"name": "Los Angeles Rams", "slug": "los-angeles-rams", "id": 26, "conference": "NFC", "division": "West"},
            {"name": "Miami Dolphins", "slug": "miami-dolphins", "id": 17, "conference": "AFC", "division": "East"},
            {"name": "Minnesota Vikings", "slug": "minnesota-vikings", "id": 18, "conference": "NFC", "division": "North"},
            {"name": "New England Patriots", "slug": "new-england-patriots", "id": 19, "conference": "AFC", "division": "East"},
            {"name": "New Orleans Saints", "slug": "new-orleans-saints", "id": 20, "conference": "NFC", "division": "South"},
            {"name": "New York Giants", "slug": "new-york-giants", "id": 21, "conference": "NFC", "division": "East"},
            {"name": "New York Jets", "slug": "new-york-jets", "id": 22, "conference": "AFC", "division": "East"},
            {"name": "Philadelphia Eagles", "slug": "philadelphia-eagles", "id": 24, "conference": "NFC", "division": "East"},
            {"name": "Pittsburgh Steelers", "slug": "pittsburgh-steelers", "id": 25, "conference": "AFC", "division": "North"},
            {"name": "San Francisco 49ers", "slug": "san-francisco-49ers", "id": 28, "conference": "NFC", "division": "West"},
            {"name": "Seattle Seahawks", "slug": "seattle-seahawks", "id": 29, "conference": "NFC", "division": "West"},
            {"name": "Tampa Bay Buccaneers", "slug": "tampa-bay-buccaneers", "id": 30, "conference": "NFC", "division": "South"},
            {"name": "Tennessee Titans", "slug": "tennessee-titans", "id": 31, "conference": "AFC", "division": "South"},
            {"name": "Washington Commanders", "slug": "washington-commanders", "id": 32, "conference": "NFC", "division": "East"},
        ]
