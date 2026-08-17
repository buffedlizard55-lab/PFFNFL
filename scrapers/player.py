"""
Player profile scraper for PFF.

Reverse engineered from public player pages like:
https://www.pff.com/nfl/players/josh-allen/46601
"""
from __future__ import annotations

import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .base import PFFScraper


class PlayerScraper(PFFScraper):
    def fetch_player(self, slug: str, player_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/nfl/players/{slug}/{player_id}"
        html = self.get(url)
        return self.parse_player(html, slug, player_id)

    def parse_player(self, html: str, slug: str, player_id: int) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        data: Dict[str, Any] = {
            "player_id": player_id,
            "slug": slug,
            "source": "pff_public_player",
        }

        # Name
        h1 = soup.find("h1")
        if h1:
            data["name"] = h1.get_text(strip=True).split("\n")[0].strip()

        # Basic bio block
        text = soup.get_text(" ", strip=True)

        # Position / Team
        m = re.search(r"([A-Z]{1,3})\s*\|\s*([A-Z]{2,4})\s+([A-Za-z\s]+)", text)
        if m:
            data["position"] = m.group(1)
            data["team_abbr"] = m.group(2)

        # Grades
        grade_patterns = {
            "overall_grade": r"Overall Grade[^0-9]*(\d{1,2}\.\d)",
            "passing_grade": r"Passing Grade[^0-9]*(\d{1,2}\.\d)",
            "rushing_grade": r"Rushing Grade[^0-9]*(\d{1,2}\.\d)",
        }
        for key, pat in grade_patterns.items():
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    data[key] = float(m.group(1))
                except:
                    pass

        # Season stats (common visible numbers)
        stats = {}
        for label, pat in [
            ("passing_yards", r"Passing Yards[^0-9]*([\d,]+)"),
            ("passing_tds", r"Passing TDs[^0-9]*(\d+)"),
            ("interceptions", r"Interceptions[^0-9]*(\d+)"),
            ("rush_yards", r"rush[^0-9]*([\d,]+)"),
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).replace(",", "")
                try:
                    stats[label] = int(val) if val.isdigit() else val
                except:
                    pass
        data["season_stats"] = stats

        # Bio details
        bio_match = re.search(r"(\d{1,2}y/o).*?(\d'\d{1,2}\").*?(\d{2,3})lbs", text)
        if bio_match:
            data["age"] = bio_match.group(1)
            data["height"] = bio_match.group(2).replace(" ", "")
            data["weight"] = int(bio_match.group(3))

        # College / draft from text
        if "College" in text or re.search(r"\d{4}", text):
            m = re.search(r"([A-Z][A-Z\s]{3,})\s+(\d{4})", text)
            if m:
                data["college"] = m.group(1).strip()
                data["draft_year"] = int(m.group(2))

        return data
