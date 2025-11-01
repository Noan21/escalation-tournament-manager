from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .enums import OrganizationVisibility, SeasonStatus

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from .events import Event


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str | None] = mapped_column(String, unique=True)
    visibility: Mapped[OrganizationVisibility] = mapped_column(
        Enum(
            OrganizationVisibility,
            name="organization_visibility",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=OrganizationVisibility.PRIVATE,
        server_default=text("'private'::text"),
    )
    contact_email: Mapped[str | None] = mapped_column(String)
    website: Mapped[str | None] = mapped_column(String)
    discord_url: Mapped[str | None] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String, nullable=False)
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    seasons: Mapped[list[Season]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class Season(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seasons"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str | None] = mapped_column(String, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SeasonStatus] = mapped_column(
        Enum(
            SeasonStatus,
            name="season_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=SeasonStatus.PLANNING,
        server_default=text("'planning'::text"),
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    starts_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    leaderboard_url: Mapped[str | None] = mapped_column(String)
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    organization: Mapped[Organization] = relationship(back_populates="seasons")
    events: Mapped[list[Event]] = relationship(
        back_populates="season", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "uq_seasons_organization_current",
            "organization_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )


# avoid circular import typing
__all__ = ["Organization", "Season"]
