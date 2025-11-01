from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import (
    Base,
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from .enums import ArchiveMode, CleanupTarget, MigrationStatus


class CleanupPolicy(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cleanup_policies"

    target: Mapped[CleanupTarget] = mapped_column(
        Enum(
            CleanupTarget,
            name="cleanup_target",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    run_every_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class ArchivePolicy(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "archive_policies"

    apply_to_events_older_than_days: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[ArchiveMode] = mapped_column(
        Enum(
            ArchiveMode,
            name="archive_mode",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    include_event_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=False,
        server_default=text("'{}'::uuid[]"),
    )
    exclude_event_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=False,
        server_default=text("'{}'::uuid[]"),
    )
    notify_contacts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class MigrationPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "migration_policies"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    run_on_startup: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    retry_on_failure: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default=text("3")
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[MigrationStatus | None] = mapped_column(
        Enum(
            MigrationStatus,
            name="migration_status",
            native_enum=False,
            create_constraint=True,
        )
    )


__all__ = [
    "ArchivePolicy",
    "CleanupPolicy",
    "MigrationPolicy",
]
