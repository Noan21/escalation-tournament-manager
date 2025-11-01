# Player Entities

Strong typing around players/teams keeps registration flows predictable and lets the agents rely on consistent payloads. These Pydantic models capture the canonical shapes used by the RegistrationAgent, OrchestratorAgent, and front-end forms.

## 👤 Participant Models

```python
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, constr


HandleType = Literal["email", "discord", "bcp", "custom"]


class ContactHandle(BaseModel):
    kind: HandleType
    value: constr(strip_whitespace=True, min_length=2, max_length=120)


class ParticipantProfile(BaseModel):
    id: UUID
    display_name: constr(strip_whitespace=True, min_length=2, max_length=80)
    organization_id: UUID
    status: Literal["active", "suspended", "retired"] = "active"
    email: Optional[EmailStr] = None
    handles: list[ContactHandle] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    def preferred_contact(self) -> Optional[str]:
        for handle in self.handles:
            if handle.kind in {"email", "discord"}:
                return handle.value
        return self.email
```

- `ParticipantProfile` mirrors the `participants` table. `handles` keeps optional game-specific identifiers (Discord, BCP, etc.).
- Single-organization deployment means `organization_id` always references the lone organization record.
- Phone numbers are intentionally excluded; email + contact handles cover outbound messaging needs.
- `preferred_contact` offers an ergonomic helper for outbound notifications.

## 👫 Team Models

```python
class TeamMember(BaseModel):
    team_id: UUID
    participant_id: UUID
    role: Literal["captain", "member", "alternate"] = "member"
    joined_at: datetime


class TeamProfile(BaseModel):
    id: UUID
    organization_id: UUID
    name: constr(strip_whitespace=True, min_length=2, max_length=80)
    status: Literal["active", "inactive"] = "active"
    handles: list[ContactHandle] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)
    members: list[TeamMember] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    def captain_ids(self) -> list[UUID]:
        return [member.participant_id for member in self.members if member.role == "captain"]
```

- `TeamProfile` embeds `TeamMember` objects so team rosters can be hydrated in a single call.
- `captain_ids()` helps the NotificationAgent target team captains quickly.

## 📝 Event Registration

```python
from typing import Annotated

RegistrationStatus = Literal["pending", "confirmed", "checked_in", "withdrawn"]
RegistrationSubject = Annotated[UUID, "Participant or Team ID"]


class EventRegistration(BaseModel):
    id: UUID
    event_id: UUID
    subject_type: Literal["participant", "team"]
    subject_id: RegistrationSubject
    status: RegistrationStatus = "pending"
    seeding_score: Optional[float] = None
    notes: Optional[str] = Field(default=None, max_length=512)
    registered_at: datetime
    confirmed_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    meta: dict[str, object] = Field(default_factory=dict)

    def is_active(self) -> bool:
        return self.status in {"pending", "confirmed", "checked_in"}
```

- Registration records link participants or teams to events. `subject_type` disambiguates the join without polymorphic tables.
- Timestamps let us audit when players confirm or check in on-site.

## 🎟️ Check-in Records

```python
class CheckInRecord(BaseModel):
    registration_id: UUID
    recorded_by: Optional[UUID]  # admin or self-check-in
    method: Literal["self_service", "admin_manual", "kiosk"]
    recorded_at: datetime
    note: Optional[str] = Field(default=None, max_length=256)
```

Separate check-in rows keep the audit log tidy and decouple state transitions from registrations.

## 🔄 Mutations

```python
class ParticipantCreate(BaseModel):
    display_name: constr(strip_whitespace=True, min_length=2, max_length=80)
    organization_id: UUID
    email: Optional[EmailStr]
    handles: list[ContactHandle] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)


class ParticipantUpdate(BaseModel):
    display_name: Optional[constr(strip_whitespace=True, min_length=2, max_length=80)]
    email: Optional[EmailStr]
    handles: Optional[list[ContactHandle]]
    status: Optional[Literal["active", "suspended", "retired"]]
    meta: Optional[dict[str, object]]
```

- `ParticipantCreate` and `ParticipantUpdate` mirror REST payloads and ensure we validate user input consistently.
- Equivalent create/update models should exist for teams and event registrations.

## ✅ Implementation Notes

1. Promote these models to `app/models/player.py` (or similar) so both FastAPI schemas and agents share them.
2. Use them in service layers before persisting to SQLAlchemy models to catch invalid payloads early.
3. Add serialization helpers so Next.js forms can consume the same shapes via OpenAPI-generated types.
