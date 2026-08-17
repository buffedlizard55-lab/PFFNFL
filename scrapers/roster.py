"""
PFF Roster Parser — Reverse Engineered (Public Pages Only)

Key observations from real PFF HTML:
- Each player block starts with an <a href="/nfl/players/...">
- Position is usually in a following <a href="/nfl/grades/position/...">
- Grades are sequences of floats or "lock-solid"
- Snap counts are the largest 3-4 digit numbers
- Bio (age, height, college, draft) appears at the end of each player's text block
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from .base import PFFScraper


class RosterScraper(PFFScraper):
    POSITIONS = {"QB", "HB", "WR", "TE", "C", "G", "T", "FB",
                 "CB", "S", "LB", "DI", "ED", "K", "P"}

    def fetch_roster(self, team_slug: str, team_id: int, force_refresh: bool = False) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/nfl/teams/{team_slug}/{team_id}/roster"
        html = self.get(url, force_refresh=force_refresh)
        return self.parse_roster(html, team_slug, team_id)

    def parse_roster(self, html: str, team_slug: str, team_id: int) -> List[Dict[str, Any]]:
        if not html or len(html) < 100:
            return []

        soup = BeautifulSoup(html, "lxml")
        players: List[Dict[str, Any]] = []

        anchors = soup.select('a[href*="/nfl/players/"]')
        if not anchors:
            return []

        # Build ordered list with text positions
        items = []
        full_text = soup.get_text(" ", strip=True)

        for a in anchors:
            href = a.get("href", "")
            m = re.search(r"/nfl/players/([^/]+)/(\d+)", href)
            if not m:
                continue
            name = a.get_text(strip=True).strip()
            if len(name) < 3:
                continue
            try:
                pos_in_text = full_text.index(name)
            except ValueError:
                pos_in_text = 0
            items.append({
                "name": name,
                "slug": m.group(1),
                "player_id": int(m.group(2)),
                "href": href,
                "start": pos_in_text
            })

        items.sort(key=lambda x: x["start"])

        for i, item in enumerate(items):
            start = item["start"]
            end = items[i + 1]["start"] if i + 1 < len(items) else len(full_text)
            block = full_text[start:end]

            pos = self._extract_position(block)
            number = self._extract_number(block)
            grades = self._extract_grades(block)
            snaps = self._extract_snaps(block)
            bio = self._extract_bio(block)

            players.append({
                "team": team_slug,
                "team_id": team_id,
                "player_id": item["player_id"],
                "slug": item["slug"],
                "name": item["name"],
                "position": pos,
                "number": number,
                **grades,
                "snaps": snaps,
                **bio,
                "url": f"https://www.pff.com{item['href']}",
                "source": "pff_public_roster",
            })

        return players

    def _extract_position(self, text: str) -> str:
        # Best: explicit position link text
        for pos in self.POSITIONS:
            if f"/grades/position/{pos.lower()}" in text.lower():
                return pos

        # Look for standalone position near the beginning of the block
        m = re.search(r"\b(QB|HB|WR|TE|C|G|T|FB|CB|S|LB|DI|ED|K|P)\b", text[:200])
        if m:
            return m.group(1)

        return "UNK"

    def _extract_number(self, text: str) -> Optional[str]:
        m = re.search(r"#\s*(\d{1,2})", text[:150])
        return m.group(1) if m else None

    def _extract_grades(self, text: str) -> Dict[str, Optional[float]]:
        result = {
            "overall_grade": None,
            "pass_grade": None,
            "run_grade": None,
            "receiving_grade": None,
            "pass_block_grade": None,
            "run_block_grade": None,
            "defense_grade": None,
        }

        # First prominent float is usually overall
        floats = re.findall(r"\b(\d{1,2}\.\d)\b", text)
        if floats:
            result["overall_grade"] = float(floats[0])
            if len(floats) > 1:
                result["pass_grade"] = float(floats[1])

        # Named grades
        patterns = {
            "pass_grade": r"(?:pass|Pass)\s*(\d{1,2}\.\d)",
            "run_grade": r"(?:run|Run)\s*(\d{1,2}\.\d)",
            "receiving_grade": r"(?:recv|receiving)\s*(\d{1,2}\.\d)",
            "defense_grade": r"(?:def|defense)\s*(\d{1,2}\.\d)",
        }
        for key, pat in patterns.items():
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    result[key] = float(m.group(1))
                except:
                    pass
        return result

    def _extract_snaps(self, text: str) -> Optional[int]:
        """Smart snap count extraction.

        Prefers:
        - Numbers explicitly near "snaps"
        - The largest plausible season total in the player block
        """
        candidates = []

        # Look for "1,234 snaps" or "1234 Snaps"
        for m in re.finditer(r"(\d{1,3}(?:,\d{3})*)\s*(?:snaps|Snaps|SNAPS)?", text, re.IGNORECASE):
            try:
                val = int(m.group(1).replace(",", ""))
                if 50 <= val <= 1700:
                    candidates.append((val, 10))  # high priority
            except:
                pass

        # Any large number in the block (fallback)
        for m in re.finditer(r"\b(\d{3,4})\b", text):
            try:
                val = int(m.group(1))
                if 80 <= val <= 1600:
                    candidates.append((val, 1))
            except:
                pass

        if not candidates:
            return None

        # Return the highest priority + largest value
        candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return candidates[0][0]

    def _extract_bio(self, text: str) -> Dict[str, Any]:
        bio = {"age": None, "height": None, "weight": None, "college": None,
               "draft_year": None, "draft_round": None, "draft_pick": None}

        # Age
        am = re.search(r"(\d{1,2}\.\d)\s*(?:A|y/o)", text)
        if am:
            bio["age"] = float(am.group(1))

        # Height
        hm = re.search(r"(\d'\d{1,2}\")", text)
        if hm:
            bio["height"] = hm.group(1)

        # Weight
        wm = re.search(r"(\d{2,3})\s*(?:lbs|lb)", text, re.IGNORECASE)
        if wm:
            bio["weight"] = int(wm.group(1))

        # College + draft year
        cm = re.search(r"\b([A-Z][A-Z\s]{3,})\s+(\d{4})", text)
        if cm:
            bio["college"] = cm.group(1).strip()
            bio["draft_year"] = int(cm.group(2))

        # Draft round/pick
        dm = re.search(r"(\d{4})\s+(\d+)\s+(\d+)", text)
        if dm:
            bio["draft_year"] = int(dm.group(1))
            bio["draft_round"] = int(dm.group(2))
            bio["draft_pick"] = int(dm.group(3))

        return bio
