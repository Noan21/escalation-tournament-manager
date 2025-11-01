from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class OrchestratorAction(StrEnum):
    GENERATE_ROUND = "generate_round"
    LOCK_ROUND = "lock_round"
    RECOMPUTE_SEASON = "recompute_season"


class OrchestratorCommand(BaseModel):
    action: OrchestratorAction
    stage_id: UUID | None = None
    round_id: UUID | None = None
    season_id: UUID | None = None
    pairing_seed: str | None = None
    round_number: int | None = Field(default=None, ge=1)


class OrchestratorResult(BaseModel):
    status: str = "ok"
    message: str | None = None
    round_id: UUID | None = None
    season_id: UUID | None = None


__all__ = [
    "OrchestratorAction",
    "OrchestratorCommand",
    "OrchestratorResult",
]
