from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, constr

from api.app.models.enums import (
    CheckInMethod,
    ParticipantStatus,
    RegistrationStatus,
    RegistrationSubjectType,
    TeamMemberRole,
    TeamStatus,
)

HandleType = Literal["email", "discord", "bcp", "custom"]


class ContactHandle(BaseModel):
    kind: HandleType
    value: constr(strip_whitespace=True, min_length=2, max_length=120)

    model_config = ConfigDict(from_attributes=True)


class ParticipantProfile(BaseModel):
    id: UUID
    display_name: constr(strip_whitespace=True, min_length=2, max_length=80)
    organization_id: UUID
    status: ParticipantStatus = ParticipantStatus.ACTIVE
    email: EmailStr | None = None
    handles: list[ContactHandle] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def preferred_contact(self) -> str | None:
        """Return email or Discord handle preference when available."""

        for handle in self.handles:
            if handle.kind in {"email", "discord"}:
                return handle.value
        return self.email


class TeamMember(BaseModel):
    team_id: UUID
    participant_id: UUID
    role: TeamMemberRole = TeamMemberRole.MEMBER
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamProfile(BaseModel):
    id: UUID
    organization_id: UUID
    name: constr(strip_whitespace=True, min_length=2, max_length=80)
    status: TeamStatus = TeamStatus.ACTIVE
    handles: list[ContactHandle] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)
    members: list[TeamMember] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def captain_ids(self) -> list[UUID]:
        return [member.participant_id for member in self.members if member.role == TeamMemberRole.CAPTAIN]


class EventRegistration(BaseModel):
    id: UUID
    event_id: UUID
    subject_type: RegistrationSubjectType
    subject_id: UUID
    status: RegistrationStatus = RegistrationStatus.PENDING
    seeding_score: float | None = None
    notes: str | None = Field(default=None, max_length=512)
    registered_at: datetime
    confirmed_at: datetime | None = None
    checked_in_at: datetime | None = None
    meta: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    def is_active(self) -> bool:
        return self.status in {
            RegistrationStatus.PENDING,
            RegistrationStatus.CONFIRMED,
            RegistrationStatus.CHECKED_IN,
        }


class CheckInRecord(BaseModel):
    registration_id: UUID
    recorded_by: UUID | None
    method: CheckInMethod
    recorded_at: datetime
    note: str | None = Field(default=None, max_length=256)

    model_config = ConfigDict(from_attributes=True)


class ParticipantCreate(BaseModel):
    display_name: constr(strip_whitespace=True, min_length=2, max_length=80)
    organization_id: UUID
    email: EmailStr | None
    handles: list[ContactHandle] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)


class ParticipantUpdate(BaseModel):
    display_name: constr(strip_whitespace=True, min_length=2, max_length=80) | None = None
    email: EmailStr | None = None
    handles: list[ContactHandle] | None = None
    status: ParticipantStatus | None = None
    meta: dict[str, object] | None = None


__all__ = [
    "CheckInRecord",
    "ContactHandle",
    "EventRegistration",
    "HandleType",
    "ParticipantCreate",
    "ParticipantProfile",
    "ParticipantUpdate",
    "TeamMember",
    "TeamProfile",
]
