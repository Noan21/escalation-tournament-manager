from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.app.models.enums import MatchOutcome, MatchState, RoundStatus


class RoundTiming(BaseModel):
    pairings_released_at: datetime | None = None
    games_start_at: datetime | None = None
    submissions_due_at: datetime | None = None
    locked_at: datetime | None = None
    published_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RoundProfile(BaseModel):
    id: UUID
    stage_id: UUID
    number: int = Field(..., ge=1)
    status: RoundStatus = RoundStatus.SCHEDULED
    timing: RoundTiming = Field(default_factory=RoundTiming)
    pairing_seed: str | None = Field(
        default=None,
        description="Optional deterministic seed used by the pairing strategy.",
    )
    notes: str | None = Field(default=None, max_length=512)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def is_locked(self) -> bool:
        return self.status in {RoundStatus.LOCKED, RoundStatus.PUBLISHED}


class MatchAssignment(BaseModel):
    table_number: int | None = Field(default=None, ge=1)
    judge_id: UUID | None = None
    stream_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ParticipantSlot(BaseModel):
    participant_id: UUID | None = None
    team_id: UUID | None = None
    seed: int | None = None
    points_before_round: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @property
    def subject_id(self) -> UUID | None:
        return self.participant_id or self.team_id


class GameResult(BaseModel):
    game_number: int = Field(..., ge=1)
    outcome: MatchOutcome = MatchOutcome.PENDING
    score_a: int | None = None
    score_b: int | None = None
    completed_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=256)

    model_config = ConfigDict(from_attributes=True)


class MatchScore(BaseModel):
    wins_a: int = Field(default=0, ge=0)
    wins_b: int = Field(default=0, ge=0)
    draws: int = Field(default=0, ge=0)
    total_points_a: int = Field(default=0, ge=0)
    total_points_b: int = Field(default=0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class MatchProfile(BaseModel):
    id: UUID
    round_id: UUID
    state: MatchState = MatchState.SCHEDULED
    pairing_order: int = Field(..., ge=1, description="Within-round ordering for display.")
    assignment: MatchAssignment = Field(default_factory=MatchAssignment)
    slot_a: ParticipantSlot = Field(default_factory=ParticipantSlot)
    slot_b: ParticipantSlot = Field(default_factory=ParticipantSlot)
    games: list[GameResult] = Field(default_factory=list)
    score: MatchScore = Field(default_factory=MatchScore)
    reported_by: UUID | None = None
    reported_at: datetime | None = None
    confirmed_by: UUID | None = None
    confirmed_at: datetime | None = None
    meta: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    def is_complete(self) -> bool:
        return self.state in {
            MatchState.COMPLETED,
            MatchState.BYE,
            MatchState.FORFEIT,
            MatchState.CANCELLED,
        }


class MatchResultSubmit(BaseModel):
    match_id: UUID
    reported_by: UUID
    wins_a: int = Field(ge=0)
    wins_b: int = Field(ge=0)
    draws: int = Field(ge=0)
    total_points_a: int | None = Field(default=None, ge=0)
    total_points_b: int | None = Field(default=None, ge=0)
    game_details: list[GameResult] | None = None
    note: str | None = Field(default=None, max_length=512)


class GenerateRoundRequest(BaseModel):
    round_number: int | None = Field(default=None, ge=1)
    pairing_seed: str | None = None


class TableAssignment(BaseModel):
    match_id: UUID
    table_number: int = Field(..., ge=1)


class AssignTablesRequest(BaseModel):
    assignments: list[TableAssignment] = Field(default_factory=list)


class PairingPreview(BaseModel):
    stage_id: UUID
    round_number: int
    matches: list[MatchProfile] = Field(default_factory=list)


class ReopenRoundRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=280)


__all__ = [
    "AssignTablesRequest",
    "GameResult",
    "GenerateRoundRequest",
    "MatchAssignment",
    "MatchProfile",
    "MatchResultSubmit",
    "PairingPreview",
    "MatchScore",
    "ReopenRoundRequest",
    "ParticipantSlot",
    "RoundProfile",
    "RoundTiming",
    "TableAssignment",
]
