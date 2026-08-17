from pydantic import BaseModel
from typing import Optional


class Game(BaseModel):
    season: int
    week: str
    team: Optional[str] = None
    opponent: Optional[str] = None
    is_home: bool = False
    date_text: Optional[str] = None
    url: str

    away_team: Optional[str] = None
    home_team: Optional[str] = None
    score_away: Optional[int] = None
    score_home: Optional[int] = None

    class Config:
        frozen = True
