from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeasonLeaderboardRow(BaseModel):
    subject_id: UUID
    subject_type: str = Field(default="participant")
    display_name: str
    events_played: int = 0
    match_points: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0

    model_config = ConfigDict(from_attributes=True)


class SeasonLeaderboard(BaseModel):
    season_id: UUID
    computed_at: datetime
    scoring_profile_key: str
    rows: list[SeasonLeaderboardRow] = Field(default_factory=list)


__all__ = ["SeasonLeaderboard", "SeasonLeaderboardRow"]
