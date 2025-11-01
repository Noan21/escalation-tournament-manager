from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from api.app.models.enums import OrganizationVisibility, SeasonStatus


class OrganizationProfile(BaseModel):
    id: UUID
    name: str = Field(..., min_length=3, max_length=120)
    slug: str = Field(..., pattern=r"^[a-z0-9-]{3,50}$")
    visibility: OrganizationVisibility = OrganizationVisibility.PUBLIC
    contact_email: EmailStr | None = None
    website: HttpUrl | None = None
    discord_url: HttpUrl | None = None
    timezone: str = Field(..., description="IANA timezone string, e.g., 'America/New_York'")
    meta: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationSettings(BaseModel):
    allow_public_registration: bool = True
    default_max_players: int | None = Field(default=None, ge=2)
    default_format_key: str | None = None
    default_scoring_key: str | None = None
    announcement_webhook: HttpUrl | None = None


class SeasonProfile(BaseModel):
    id: UUID
    organization_id: UUID
    name: str = Field(..., min_length=3, max_length=120)
    year: int = Field(..., ge=2000, le=2100)
    status: SeasonStatus = SeasonStatus.PLANNING
    is_current: bool = False
    starts_on: datetime
    ends_on: datetime
    description: str | None = Field(default=None, max_length=1024)
    visibility: OrganizationVisibility = OrganizationVisibility.PUBLIC
    leaderboard_url: HttpUrl | None = None
    meta: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_active(self) -> bool:
        return self.status == SeasonStatus.ACTIVE


class SeasonStandingConfig(BaseModel):
    scoring_profile_key: str = Field(
        ..., description="Reference into scoring_profiles registry."
    )
    include_events: list[UUID] = Field(default_factory=list)
    exclude_events: list[UUID] = Field(default_factory=list)
    min_events_required: int | None = Field(default=None, ge=1)
    drop_lowest_results: int = Field(default=0, ge=0)


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    visibility: OrganizationVisibility = OrganizationVisibility.PUBLIC
    contact_email: EmailStr | None
    timezone: str
    meta: dict[str, object] = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    name: str | None = None
    visibility: OrganizationVisibility | None = None
    contact_email: EmailStr | None = None
    website: HttpUrl | None = None
    discord_url: HttpUrl | None = None
    timezone: str | None = None
    meta: dict[str, object] | None = None


class SeasonCreate(BaseModel):
    organization_id: UUID
    name: str
    year: int
    starts_on: datetime
    ends_on: datetime
    description: str | None = None
    leaderboard_url: HttpUrl | None = None
    meta: dict[str, object] = Field(default_factory=dict)


class SeasonUpdate(BaseModel):
    name: str | None = None
    year: int | None = None
    status: SeasonStatus | None = None
    is_current: bool | None = None
    starts_on: datetime | None = None
    ends_on: datetime | None = None
    description: str | None = None
    visibility: OrganizationVisibility | None = None
    leaderboard_url: HttpUrl | None = None
    meta: dict[str, object] | None = None


__all__ = [
    "OrganizationCreate",
    "OrganizationProfile",
    "OrganizationSettings",
    "OrganizationUpdate",
    "SeasonCreate",
    "SeasonProfile",
    "SeasonStandingConfig",
    "SeasonUpdate",
]
