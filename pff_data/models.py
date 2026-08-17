"""
Pydantic models for PFF data intended for reliable backtesting.

These models enforce schema and include provenance fields critical for
reproducible prediction model backtesting.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class PFFProvenance(BaseModel):
    """Where and when this data was collected."""
    source: str = "pff_public"
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    scraper_version: str = "0.1.0"
    page_url: Optional[str] = None
    sample_name: Optional[str] = None   # for offline/reproducible runs


class PFFPlayerRoster(BaseModel):
    """
    Player record from a PFF roster page snapshot.
    This is a point-in-time observation of a player's status/grade/snaps.
    """
    # Time context (CRITICAL for backtesting)
    season: int
    week: Optional[str] = None          # "1", "P1", "WC", etc. or None for roster snapshot
    snapshot_date: Optional[str] = None # ISO date when this roster was observed

    # Player identity
    player_id: int
    slug: str
    name: str
    team: str
    team_id: int

    # Position & depth
    position: str
    number: Optional[str] = None

    # PFF grades (0-100 scale where available)
    overall_grade: Optional[float] = None
    pass_grade: Optional[float] = None
    run_grade: Optional[float] = None
    receiving_grade: Optional[float] = None
    pass_block_grade: Optional[float] = None
    run_block_grade: Optional[float] = None
    defense_grade: Optional[float] = None

    # Usage (very important for prediction)
    snaps: Optional[int] = None

    # Bio (relatively static)
    age: Optional[float] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    college: Optional[str] = None
    draft_year: Optional[int] = None
    draft_round: Optional[int] = None
    draft_pick: Optional[int] = None

    # Provenance
    provenance: PFFProvenance = Field(default_factory=PFFProvenance)
    source: str = "pff_public_roster"

    @field_validator("position")
    @classmethod
    def normalize_position(cls, v: str) -> str:
        return v.upper().strip() if v else "UNK"

    @field_validator("overall_grade", "pass_grade", "run_grade", mode="before")
    @classmethod
    def clamp_grade(cls, v):
        if v is None:
            return None
        try:
            g = float(v)
            return max(0.0, min(100.0, g))
        except (ValueError, TypeError):
            return None

    @field_validator("snaps", mode="before")
    @classmethod
    def validate_snaps(cls, v):
        if v is None:
            return None
        try:
            s = int(v)
            return max(0, s)
        except (ValueError, TypeError):
            return None


class PFFLineupSnapshot(BaseModel):
    """A depth chart / lineup snapshot at a point in time."""
    season: int
    week: Optional[str] = None
    team: str
    side: Literal["offense", "defense"]
    position_rank: Optional[int] = None   # 1 = starter, 2 = backup, etc.
    player_id: Optional[int] = None
    player_name: str
    provenance: PFFProvenance = Field(default_factory=PFFProvenance)


class PFFCollectionRun(BaseModel):
    """Metadata about a full collection run (for auditability)."""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    season: int
    weeks: list[str] = Field(default_factory=list)
    teams_scraped: int = 0
    players_collected: int = 0
    errors: list[str] = Field(default_factory=list)
    git_commit: Optional[str] = None
    notes: Optional[str] = None


class PFFGameSnapshot(BaseModel):
    """Point-in-time game box / participation snapshot from public PFF game page."""
    season: int
    week: Optional[str] = None
    game_path: str
    away_team: Optional[str] = None
    home_team: Optional[str] = None
    away_score: Optional[int] = None
    home_score: Optional[int] = None

    # Extracted box / participation data (high signal for features)
    player_stats: list[dict] = Field(default_factory=list)   # [{name, raw}, ...]
    plays: list[str] = Field(default_factory=list)

    # Provenance
    provenance: PFFProvenance = Field(default_factory=PFFProvenance)
    source: str = "pff_public_game"


class PFFScheduleEntry(BaseModel):
    """A single game from a team's public schedule page."""
    season: int
    week: Optional[str] = None
    team: str
    opponent: str
    is_home: bool = False
    date_text: Optional[str] = None
    url: Optional[str] = None

    # Provenance
    provenance: PFFProvenance = Field(default_factory=PFFProvenance)
    source: str = "pff_public_schedule"
