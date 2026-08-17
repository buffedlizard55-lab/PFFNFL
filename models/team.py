from pydantic import BaseModel, Field
from typing import Optional, List


class Team(BaseModel):
    id: int
    name: str
    slug: str
    conference: Optional[str] = None
    division: Optional[str] = None
    url: Optional[str] = None

    class Config:
        frozen = True
