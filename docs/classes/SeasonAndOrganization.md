# Season & Organization

This app operates in a single-organization mode. The `OrganizationProfile` represents that one entity, and admins designate exactly one season as the active season for players. The shapes below still surface `organization_id` for forward compatibility, but it will always reference the same record.

## 🏢 Organization Models

```python
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

OrganizationVisibility = Literal["private", "unlisted", "public"]


class OrganizationProfile(BaseModel):
    id: UUID
    name: str = Field(..., min_length=3, max_length=120)
    slug: str = Field(..., regex=r"^[a-z0-9-]{3,50}$")
    visibility: OrganizationVisibility = "public"
    contact_email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    discord_url: Optional[HttpUrl] = None
    timezone: str = Field(..., description="IANA timezone string, e.g., 'America/New_York'")
    meta: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class OrganizationSettings(BaseModel):
    allow_public_registration: bool = True
    default_max_players: Optional[int] = Field(default=None, ge=2)
    default_format_key: Optional[str] = None
    default_scoring_key: Optional[str] = None
    announcement_webhook: Optional[HttpUrl] = None
```

- Visibility controls whether events appear in public searches.
- Settings let admins provide organization-wide defaults without duplicating data per event.

## 🗓️ Season Models

```python
SeasonStatus = Literal["planning", "active", "complete", "archived"]


class SeasonProfile(BaseModel):
    id: UUID
    organization_id: UUID
    name: str = Field(..., min_length=3, max_length=120)
    year: int = Field(..., ge=2000, le=2100)
    status: SeasonStatus = "planning"
    is_current: bool = False  # exactly one season should have this True
    starts_on: datetime
    ends_on: datetime
    description: Optional[str] = Field(default=None, max_length=1024)
    visibility: OrganizationVisibility = "public"
    leaderboard_url: Optional[HttpUrl] = None
    meta: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @property
    def is_active(self) -> bool:
        return self.status == "active"
```

```python
class SeasonStandingConfig(BaseModel):
    scoring_profile_key: str = Field(..., description="Reference into scoring_profiles registry.")
    include_events: list[UUID] = Field(default_factory=list)
    exclude_events: list[UUID] = Field(default_factory=list)
    min_events_required: Optional[int] = Field(default=None, ge=1)
    drop_lowest_results: int = Field(default=0, ge=0)
```

- `SeasonStandingConfig` powers the `SeasonAgent` to compute aggregate standings.

## 🛠️ Mutations

```python
class OrganizationCreate(BaseModel):
    name: str
    slug: str
    visibility: OrganizationVisibility = "public"
    contact_email: Optional[EmailStr]
    timezone: str
    meta: dict[str, object] = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    name: Optional[str]
    visibility: Optional[OrganizationVisibility]
    contact_email: Optional[EmailStr]
    website: Optional[HttpUrl]
    discord_url: Optional[HttpUrl]
    timezone: Optional[str]
    meta: Optional[dict[str, object]]
```

Analogous create/update models can be defined for seasons to drive admin forms.

## ✅ Implementation Notes

1. Store these models in `app/models/organization.py` and `app/models/season.py`.
2. Because we only support one organization, enforce a singleton row in the database and expose admin UI to edit it.
3. Ensure exactly one `SeasonProfile` has `is_current=True`; the admin panel should toggle this flag when switching seasons.
4. Use `OrganizationSettings` to seed defaults when creating events.
5. `SeasonStandingConfig` should feed directly into the `SeasonAgent` for leaderboard recalculations.
