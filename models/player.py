from pydantic import BaseModel, Field
from typing import Optional


class Player(BaseModel):
    player_id: int
    slug: str
    name: str
    position: str = "UNK"
    number: Optional[str] = None
    team: Optional[str] = None
    team_id: Optional[int] = None

    overall_grade: Optional[float] = None
    url: Optional[str] = None

    age: Optional[float] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    college: Optional[str] = None
    draft_year: Optional[int] = None

    class Config:
        frozen = True
