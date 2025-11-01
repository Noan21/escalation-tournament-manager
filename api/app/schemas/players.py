from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

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
    value: str = Field(..., min_length=2, max_length=120)

    model_config = ConfigDict(from_attributes=True)


class ParticipantProfile(BaseModel):
    id: UUID
    display_name: str = Field(..., min_length=2, max_length=80)
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
    name: str = Field(..., min_length=2, max_length=80)
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
    display_name: str = Field(..., min_length=2, max_length=80)
    organization_id: UUID
    email: EmailStr | None
    handles: list[ContactHandle] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)


class ParticipantUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=80)
    email: EmailStr | None = None
    handles: list[ContactHandle] | None = None
    status: ParticipantStatus | None = None
    meta: dict[str, object] | None = None


class EventRegistrationCreate(BaseModel):
    subject_type: RegistrationSubjectType = RegistrationSubjectType.PARTICIPANT
    participant_id: UUID | None = Field(default=None)
    team_id: UUID | None = Field(default=None)
    seeding_score: float | None = None
    notes: str | None = Field(default=None, max_length=512)
    meta: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_subject(self) -> EventRegistrationCreate:
        participant = self.participant_id is not None
        team = self.team_id is not None
        if participant == team:
            raise ValueError("Provide exactly one of participant_id or team_id")
        if self.subject_type == RegistrationSubjectType.PARTICIPANT and not participant:
            raise ValueError("participant_id required when subject_type=participant")
        if self.subject_type == RegistrationSubjectType.TEAM and not team:
            raise ValueError("team_id required when subject_type=team")
        return self


class UpdateRegistrationStatus(BaseModel):
    status: RegistrationStatus


class CheckInRequest(BaseModel):
    method: CheckInMethod = CheckInMethod.ADMIN_MANUAL
    note: str | None = Field(default=None, max_length=256)


class SeedRosterResult(BaseModel):
    created: int = 0
    skipped: int = 0
    already_present: int = 0


__all__ = [
    "CheckInRecord",
    "ContactHandle",
    "CheckInRequest",
    "EventRegistrationCreate",
    "EventRegistration",
    "HandleType",
    "ParticipantCreate",
    "ParticipantProfile",
    "ParticipantUpdate",
    "SeedRosterResult",
    "TeamMember",
    "TeamProfile",
    "UpdateRegistrationStatus",
]
