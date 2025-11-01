from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    Base,
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from .enums import ParticipantStatus, TeamMemberRole, TeamStatus

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from .events import Registration


class Participant(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "participants"

    display_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(
            ParticipantStatus,
            name="participant_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=ParticipantStatus.ACTIVE,
        server_default=text("'active'::text"),
    )
    email: Mapped[str | None] = mapped_column(String)
    handles: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    teams: Mapped[list[TeamMember]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )
    registrations: Mapped[list[Registration]] = relationship(
        "Registration",
        back_populates="participant",
        foreign_keys="Registration.participant_id",
    )


class Team(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[TeamStatus] = mapped_column(
        Enum(TeamStatus, name="team_status", native_enum=False, create_constraint=True),
        nullable=False,
        default=TeamStatus.ACTIVE,
        server_default=text("'active'::text"),
    )
    handles: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    members: Mapped[list[TeamMember]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )
    registrations: Mapped[list[Registration]] = relationship(
        "Registration",
        back_populates="team",
        foreign_keys="Registration.team_id",
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[TeamMemberRole] = mapped_column(
        Enum(
            TeamMemberRole,
            name="team_member_role",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=TeamMemberRole.MEMBER,
        server_default=text("'member'::text"),
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    team: Mapped[Team] = relationship(back_populates="members")
    participant: Mapped[Participant] = relationship(back_populates="teams")

    __table_args__ = (
        PrimaryKeyConstraint("team_id", "participant_id", name="pk_team_members"),
    )


__all__ = ["Participant", "Team", "TeamMember"]
