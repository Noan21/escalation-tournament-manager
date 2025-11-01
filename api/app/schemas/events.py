from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from api.app.models.enums import EventStatus, StageStatus


class RegistrationWindow(BaseModel):
    opens_at: datetime
    closes_at: datetime
    waitlist_enabled: bool = False
    capacity: int | None = Field(default=None, ge=2)
    auto_promote_waitlist: bool = False

    @model_validator(mode="after")
    def validate_window(self) -> RegistrationWindow:
        if self.closes_at <= self.opens_at:
            raise ValueError("Registration closes_at must be after opens_at")
        return self


class EventProfile(BaseModel):
    id: UUID
    season_id: UUID
    organization_id: UUID
    name: str = Field(..., min_length=3, max_length=120)
    slug: str = Field(..., pattern=r"^[a-z0-9-]{3,50}$")
    status: EventStatus = EventStatus.DRAFT
    starts_at: datetime
    ends_at: datetime
    registration: RegistrationWindow
    default_format_key: str = Field(
        ..., description="Reference into tournament_formats registry."
    )
    default_scoring_key: str = Field(
        ..., description="Reference into scoring_profiles registry."
    )
    location_name: str | None = None
    location_url: HttpUrl | None = None
    max_rounds_override: int | None = Field(default=None, ge=1)
    published_at: datetime | None = None
    meta: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_dates(self) -> EventProfile:
        if self.ends_at <= self.starts_at:
            raise ValueError("Event ends_at must be after starts_at")
        return self


class StageConfig(BaseModel):
    id: UUID
    event_id: UUID
    order: int = Field(..., ge=1, description="1-indexed ordering within the event.")
    name: str = Field(..., min_length=2, max_length=80)
    status: StageStatus = StageStatus.PENDING
    format_key: str = Field(..., description="Overrides event default if provided.")
    scoring_key: str = Field(
        ..., description="Overrides event default if provided."
    )
    round_count: int | None = Field(default=None, ge=1)
    advance_top: int | None = Field(
        default=None, ge=2, description="Players advancing to next stage."
    )
    drop_cut: int | None = Field(
        default=None, ge=2, description="Players below this cut are eliminated."
    )
    start_after_stage_id: UUID | None = Field(
        default=None, description="Explicit dependency on another stage finishing."
    )
    config: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def effective_format_key(self, event: EventProfile) -> str:
        return self.format_key or event.default_format_key

    def effective_scoring_key(self, event: EventProfile) -> str:
        return self.scoring_key or event.default_scoring_key


class StageCreate(BaseModel):
    name: str
    order: int = Field(ge=1)
    format_key: str | None = None
    scoring_key: str | None = None
    round_count: int | None = Field(default=None, ge=1)
    advance_top: int | None = Field(default=None, ge=2)
    drop_cut: int | None = Field(default=None, ge=2)
    start_after_stage_id: UUID | None = None
    config: dict[str, object] = Field(default_factory=dict)


class StageUpdate(BaseModel):
    name: str | None = None
    order: int | None = Field(default=None, ge=1)
    status: StageStatus | None = None
    format_key: str | None = None
    scoring_key: str | None = None
    round_count: int | None = Field(default=None, ge=1)
    advance_top: int | None = Field(default=None, ge=2)
    drop_cut: int | None = Field(default=None, ge=2)
    start_after_stage_id: UUID | None = None
    config: dict[str, object] | None = None


__all__ = [
    "EventProfile",
    "RegistrationWindow",
    "StageConfig",
    "StageCreate",
    "StageUpdate",
]
