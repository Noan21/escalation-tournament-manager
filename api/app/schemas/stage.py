from __future__ import annotations

from pydantic import BaseModel, Field


class StageCreate(BaseModel):
    event_id: str = Field(..., description="Event the stage belongs to")
    name: str
    stage_order: int = Field(..., ge=1)
    format_key: str
    scoring_key: str
    config: dict = Field(default_factory=dict)


class StageRead(StageCreate):
    id: str

    class Config:
        from_attributes = True


class StageCatalog(BaseModel):
    pairing_strategies: dict[str, str]
    scoring_strategies: dict[str, str]
