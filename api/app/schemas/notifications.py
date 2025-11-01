from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.app.models.enums import (
    NotificationChannel,
    NotificationStatus,
    NotificationSubjectType,
)

EventTrigger = Literal[
    "registration_confirmed",
    "round_pairings",
    "round_locked",
    "standings_published",
    "season_leaderboard",
]


class ChannelConfig(BaseModel):
    channel: NotificationChannel
    address: str = Field(..., description="Email address or webhook URL")
    enabled: bool = True
    rate_limit_per_hour: int | None = Field(default=None, ge=1)

    def is_webhook(self) -> bool:
        return self.channel in {
            NotificationChannel.DISCORD_WEBHOOK,
            NotificationChannel.SLACK_WEBHOOK,
            NotificationChannel.WEBHOOK,
        }


class NotificationPreference(BaseModel):
    id: UUID
    organization_id: UUID
    subject_type: NotificationSubjectType
    subject_id: UUID
    triggers: list[EventTrigger] = Field(default_factory=list)
    channels: list[ChannelConfig] = Field(default_factory=list)
    muted_until: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def is_muted(self, now: datetime) -> bool:
        return self.muted_until is not None and self.muted_until > now


class NotificationMessage(BaseModel):
    trigger: EventTrigger
    recipient_subject_type: NotificationSubjectType
    recipient_subject_id: UUID
    channel: NotificationChannel
    address: str
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationDelivery(BaseModel):
    id: UUID
    message: NotificationMessage
    sent_at: datetime | None = None
    status: NotificationStatus = NotificationStatus.QUEUED
    failure_reason: str | None = None
    retry_count: int = 0
    last_attempt_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpsert(BaseModel):
    id: UUID | None = None
    organization_id: UUID
    subject_type: NotificationSubjectType
    subject_id: UUID
    triggers: list[EventTrigger] = Field(default_factory=list)
    channels: list[ChannelConfig] = Field(default_factory=list)
    muted_until: datetime | None = None


class NotificationDispatchRequest(BaseModel):
    trigger: EventTrigger
    organization_id: UUID | None = None
    stage_id: UUID | None = None
    round_id: UUID | None = None
    season_id: UUID | None = None
    recipient_subject_type: NotificationSubjectType | None = None
    recipient_subject_ids: list[UUID] | None = None
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    context: dict[str, object] = Field(default_factory=dict)


__all__ = [
    "ChannelConfig",
    "EventTrigger",
    "NotificationDelivery",
    "NotificationDispatchRequest",
    "NotificationMessage",
    "NotificationPreferenceUpsert",
    "NotificationPreference",
]
