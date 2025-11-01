# Events & Stages

Typed models that describe event metadata, stage configuration, and how they tie into the format/scoring registries.

## 🗓️ Event Models

```python
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator

EventStatus = Literal["draft", "registration", "active", "complete", "archived"]


class RegistrationWindow(BaseModel):
    opens_at: datetime
    closes_at: datetime
    waitlist_enabled: bool = False
    capacity: Optional[int] = Field(default=None, ge=2)
    auto_promote_waitlist: bool = False

    @validator("closes_at")
    def validate_window(cls, closes_at, values):
        opens_at = values.get("opens_at")
        if opens_at and closes_at <= opens_at:
            raise ValueError("Registration closes_at must be after opens_at")
        return closes_at


class EventProfile(BaseModel):
    id: UUID
    season_id: UUID
    organization_id: UUID
    name: str = Field(..., min_length=3, max_length=120)
    slug: str = Field(..., regex=r"^[a-z0-9-]{3,50}$")
    status: EventStatus = "draft"
    starts_at: datetime
    ends_at: datetime
    registration: RegistrationWindow
    default_format_key: str = Field(..., description="Reference into tournament_formats registry.")
    default_scoring_key: str = Field(..., description="Reference into scoring_profiles registry.")
    location_name: Optional[str] = None
    location_url: Optional[HttpUrl] = None
    max_rounds_override: Optional[int] = Field(default=None, ge=1)
    published_at: Optional[datetime] = None
    meta: dict[str, object] = Field(default_factory=dict)

    @validator("ends_at")
    def validate_dates(cls, ends_at, values):
        starts_at = values.get("starts_at")
        if starts_at and ends_at <= starts_at:
            raise ValueError("Event ends_at must be after starts_at")
        return ends_at
```

Key takeaways:

- `RegistrationWindow` keeps capacity and waitlist behavior centralized.
- `default_format_key` / `default_scoring_key` tie directly into the format/scoring registries defined earlier.
- `max_rounds_override` lets admins cap rounds without redefining the format.
- In the single-organization deployment, `organization_id` always references the singleton organization row.

## 🎯 Stage Models

```python
StageStatus = Literal["pending", "in_progress", "complete"]


class StageConfig(BaseModel):
    id: UUID
    event_id: UUID
    order: int = Field(..., ge=1, description="1-indexed ordering within the event.")
    name: str = Field(..., min_length=2, max_length=80)
    status: StageStatus = "pending"
    format_key: str = Field(..., description="Overrides event default if provided.")
    scoring_key: str = Field(..., description="Overrides event default if provided.")
    round_count: Optional[int] = Field(default=None, ge=1)
    advance_top: Optional[int] = Field(default=None, ge=2, description="Number of players to advance to next stage.")
    drop_cut: Optional[int] = Field(default=None, ge=2, description="Players below this cut are eliminated.")
    start_after_stage_id: Optional[UUID] = Field(default=None, description="Explicit dependency on another stage finishing.")
    config: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    def effective_format_key(self, event: EventProfile) -> str:
        return self.format_key or event.default_format_key

    def effective_scoring_key(self, event: EventProfile) -> str:
        return self.scoring_key or event.default_scoring_key
```

- Stages can override format/scoring registries, which supports things like Swiss followed by Top Cut.
- `advance_top` gives the OrchestratorAgent the information it needs to seed playoffs.
- `start_after_stage_id` enables explicit dependencies (e.g., wait for group stage to finish).

## 🔁 Stage Creation Specs

For API payloads and admin UI forms, provide create/update schemas:

```python
class StageCreate(BaseModel):
    name: str
    order: int = Field(ge=1)
    format_key: Optional[str] = None
    scoring_key: Optional[str] = None
    round_count: Optional[int] = Field(default=None, ge=1)
    advance_top: Optional[int] = Field(default=None, ge=2)
    drop_cut: Optional[int] = Field(default=None, ge=2)
    start_after_stage_id: Optional[UUID] = None
    config: dict[str, object] = Field(default_factory=dict)


class StageUpdate(BaseModel):
    name: Optional[str]
    order: Optional[int] = Field(default=None, ge=1)
    status: Optional[StageStatus]
    format_key: Optional[str]
    scoring_key: Optional[str]
    round_count: Optional[int] = Field(default=None, ge=1)
    advance_top: Optional[int] = Field(default=None, ge=2)
    drop_cut: Optional[int] = Field(default=None, ge=2)
    start_after_stage_id: Optional[UUID]
    config: Optional[dict[str, object]]
```

## ✅ Implementation Notes

1. Persist these models in a dedicated module (e.g., `app/models/events.py`) and align SQLAlchemy models accordingly.
2. Use `EventProfile` in admin surfaces and API responses to keep clients synchronized with server state.
3. When building Orchestrator flows, call `StageConfig.effective_format_key()` and `effective_scoring_key()` before invoking agents.
