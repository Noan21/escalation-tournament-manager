from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.app.models.enums import HeadToHeadResult, StandingSubjectType


class StandingsRow(BaseModel):
    id: UUID
    stage_id: UUID
    subject_type: StandingSubjectType
    subject_id: UUID
    rank: int = Field(..., ge=1)
    match_points: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    byes: int = 0
    total_score: int = 0
    strength_of_schedule: float | None = None
    opponent_match_win_pct: float | None = None
    head_to_head: HeadToHeadResult | None = None
    breakers_applied: list[str] = Field(default_factory=list)
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def summary(self) -> dict[str, object]:
        return {
            "subject_type": self.subject_type,
            "subject_id": str(self.subject_id),
            "rank": self.rank,
            "match_points": self.match_points,
        }


class TiebreakSnapshot(BaseModel):
    standings_row_id: UUID
    breaker_key: str
    value: float
    order_applied: int = Field(..., ge=1)
    subject_ids: list[UUID] = Field(
        default_factory=list,
        description="All subjects tied at this breaker step.",
    )
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StandingsPayload(BaseModel):
    stage_id: UUID
    scoring_profile_key: str
    generated_at: datetime
    rows: list[StandingsRow] = Field(default_factory=list)
    tiebreak_snapshots: list[TiebreakSnapshot] = Field(default_factory=list)


__all__ = [
    "StandingsPayload",
    "StandingsRow",
    "TiebreakSnapshot",
]
