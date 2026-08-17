"""
Game / Box Score / Play-by-play scraper for PFF.

Public game pages contain:
- Score
- Basic box stats
- Sometimes play-by-play
- Player participation hints
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from .base import PFFScraper


class GameScraper(PFFScraper):
    def fetch_game(self, game_path: str) -> Dict[str, Any]:
        """
        game_path example: 2026/P1/carolina-panthers_at_buffalo-bills_31908
        Full url: https://www.pff.com/nfl/scores/{game_path}
        """
        url = f"{self.base_url}/nfl/scores/{game_path}"
        html = self.get(url)
        return self.parse_game(html, game_path)

    def parse_game(self, html: str, game_path: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        data: Dict[str, Any] = {
            "game_path": game_path,
            "source": "pff_public_game",
            "plays": [],
        }

        text = soup.get_text(" ", strip=True)

        # Score
        score_match = re.search(r"(\d+)\s*–\s*(\d+)", text)
        if score_match:
            data["away_score"] = int(score_match.group(1))
            data["home_score"] = int(score_match.group(2))

        # Team names from URL or page
        m = re.search(r"([a-z-]+)_at_([a-z-]+)_", game_path)
        if m:
            data["away_team"] = m.group(1)
            data["home_team"] = m.group(2)

        # Week detection
        week_m = re.search(r"Week\s*(\d+|P\d+)", text, re.IGNORECASE)
        if week_m:
            data["week"] = week_m.group(1)

        # Rich player box stats (high value for feature engineering)
        player_stats = []
        # Stricter patterns: name starts line or after common delimiters
        patterns = [
            # Passing
            r"(?:^|[\n> ])([A-Z][a-z]+(?: [A-Z][a-z]+)*):?\s*(\d+/\d+),\s*(\d+)\s*pass yds?,\s*(\d+)\s*TD,\s*(\d+)\s*INT",
            # Rushing
            r"(?:^|[\n> ])([A-Z][a-z]+(?: [A-Z][a-z]+)*):\s*(\d+)\s*carries?,\s*(\d+)\s*rush yds?,\s*(\d+)\s*TD",
            # Defense
            r"(?:^|[\n> ])([A-Z][a-z]+(?: [A-Z][a-z]+)*):\s*(\d+)\s*tackles?,\s*(\d+)\s*INT",
        ]
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
                name = match.group(1).strip()
                # Remove common noise prefixes that regex sometimes grabs
                for noise in ("PM ", "INT ", "TD ", "Rush ", "Pass "):
                    if name.startswith(noise):
                        name = name[len(noise):].strip()
                if len(name) < 3 or name.lower().startswith(("rush", "yds", "pass", "td", "int")):
                    continue
                player_stats.append({
                    "name": name,
                    "raw": match.group(0).strip()[:140],
                })
        # Dedup
        seen = {}
        for s in player_stats:
            if s["name"] not in seen:
                seen[s["name"]] = s
        data["player_stats"] = list(seen.values())[:15]

        # Key events / plays for participation features
        plays = []
        for line in text.split("\n"):
            line = line.strip()
            if len(line) > 12 and any(kw.lower() in line.lower() for kw in ["pass", "rush", "touchdown", "field goal", "sack", "interception", "yds", "td"]):
                plays.append(line[:160])
        data["plays"] = list(dict.fromkeys(plays))[:25]

        return data
