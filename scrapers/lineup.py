"""
PFF Lineup / Depth Chart Parser (Public pages)

Observed patterns:
- Sections labeled "Offense", "Defense"
- Player entries with jersey + name: "#17 Josh Allen"
- Personnel packages mentioned (11, 12, Nickel, etc.)
- Often appears on /lineup and /fantasy/depth
"""
from __future__ import annotations

import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from .base import PFFScraper


class LineupScraper(PFFScraper):
    def fetch_lineup(self, team_slug: str, team_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/nfl/teams/{team_slug}/{team_id}/lineup"
        html = self.get(url)
        return self.parse_lineup(html, team_slug)

    def parse_lineup(self, html: str, team_slug: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        data = {
            "team": team_slug,
            "offense": [],
            "defense": [],
            "personnel": [],
            "source": "pff_public_lineup"
        }

        text = soup.get_text(" ", strip=True)

        # Personnel packages
        for pkg in re.findall(r"(11|12|21|22)\s*\([^)]+\)|Base|Nickel", text, re.IGNORECASE):
            pkg_clean = pkg.strip()
            if pkg_clean and pkg_clean not in data["personnel"]:
                data["personnel"].append(pkg_clean)

        current_side = "offense"  # default
        seen = set()

        for elem in soup.find_all(["h1", "h2", "h3", "div", "span", "a", "strong", "p"]):
            t = elem.get_text(strip=True).lower()

            if "offense" in t and "defense" not in t:
                current_side = "offense"
            elif "defense" in t:
                current_side = "defense"

            if elem.name == "a" and "/nfl/players/" in (elem.get("href") or ""):
                raw_name = elem.get_text(strip=True).strip()
                # Clean common junk like "#17 Josh Allen"
                name = re.sub(r"^#\d+\s*", "", raw_name).strip()
                if len(name) < 3:
                    continue

                href = elem.get("href", "")
                m = re.search(r"/nfl/players/([^/]+)/(\d+)", href)
                pid = int(m.group(2)) if m else None

                entry = {
                    "name": name,
                    "player_id": pid,
                    "url": f"https://www.pff.com{href}" if href else None
                }

                key = (pid or name)
                if key in seen:
                    continue
                seen.add(key)

                target = data["offense"] if current_side == "offense" else data["defense"]
                target.append(entry)

        # Fallback: if nothing classified, put first ~11 in offense
        if not data["offense"] and not data["defense"]:
            for a in soup.select('a[href*="/nfl/players/"]')[:11]:
                name = a.get_text(strip=True)
                if len(name) > 2:
                    m = re.search(r"/nfl/players/([^/]+)/(\d+)", a.get("href", ""))
                    data["offense"].append({
                        "name": name,
                        "player_id": int(m.group(2)) if m else None,
                        "url": f"https://www.pff.com{a.get('href', '')}"
                    })

        return data
