from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, OrganizationScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from .enums import (
    NotificationChannel,
    NotificationStatus,
    NotificationSubjectType,
)


class NotificationPreference(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base
):
    __tablename__ = "notification_preferences"

    subject_type: Mapped[NotificationSubjectType] = mapped_column(
        Enum(
            NotificationSubjectType,
            name="notification_subject_type",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    triggers: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    channels: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationDelivery(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base
):
    __tablename__ = "notification_deliveries"

    trigger: Mapped[str] = mapped_column(String, nullable=False)
    recipient_subject_type: Mapped[NotificationSubjectType] = mapped_column(
        Enum(
            NotificationSubjectType,
            name="delivery_subject_type",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    recipient_subject_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(
            NotificationChannel,
            name="notification_channel",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str | None] = mapped_column(String)
    body_text: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    delivery_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(
            NotificationStatus,
            name="notification_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=NotificationStatus.QUEUED,
        server_default=text("'queued'::text"),
    )
    failure_reason: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


__all__ = ["NotificationDelivery", "NotificationPreference"]
