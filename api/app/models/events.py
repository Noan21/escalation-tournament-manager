from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    Base,
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from .enums import (
    CheckInMethod,
    EventStatus,
    MatchOutcome,
    MatchState,
    RegistrationStatus,
    RegistrationSubjectType,
    RoundStatus,
    StageStatus,
)


class Event(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "events"

    season_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str | None] = mapped_column(String, unique=True)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status", native_enum=False, create_constraint=True),
        nullable=False,
        default=EventStatus.DRAFT,
        server_default=text("'draft'::text"),
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_opens_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    registration_closes_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    registration_capacity: Mapped[int | None] = mapped_column(Integer)
    waitlist_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    auto_promote_waitlist: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    default_format_key: Mapped[str] = mapped_column(String, nullable=False)
    default_scoring_key: Mapped[str] = mapped_column(String, nullable=False)
    location_name: Mapped[str | None] = mapped_column(String)
    location_url: Mapped[str | None] = mapped_column(String)
    max_rounds_override: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    season: Mapped[Season] = relationship(back_populates="events")
    stages: Mapped[list[Stage]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    registrations: Mapped[list[Registration]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_events_season_starts_at", "season_id", "starts_at"),
    )


class Stage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stages"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[StageStatus] = mapped_column(
        Enum(
            StageStatus,
            name="stage_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=StageStatus.PENDING,
        server_default=text("'pending'::text"),
    )
    format_key: Mapped[str | None] = mapped_column(String)
    scoring_key: Mapped[str | None] = mapped_column(String)
    round_count: Mapped[int | None] = mapped_column(Integer)
    advance_top: Mapped[int | None] = mapped_column(Integer)
    drop_cut: Mapped[int | None] = mapped_column(Integer)
    start_after_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("stages.id", ondelete="SET NULL")
    )
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    event: Mapped[Event] = relationship(back_populates="stages")
    rounds: Mapped[list[Round]] = relationship(
        back_populates="stage", cascade="all, delete-orphan"
    )
    standings: Mapped[list[Standing]] = relationship(
        "Standing", back_populates="stage", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("event_id", "order", name="uq_stages_event_order"),
    )


class Registration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "registrations"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    subject_type: Mapped[RegistrationSubjectType] = mapped_column(
        Enum(
            RegistrationSubjectType,
            name="registration_subject_type",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    participant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE")
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE")
    )
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(
            RegistrationStatus,
            name="registration_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=RegistrationStatus.PENDING,
        server_default=text("'pending'::text"),
    )
    seeding_score: Mapped[Numeric | None] = mapped_column(Numeric)
    notes: Mapped[str | None] = mapped_column(Text)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    event: Mapped[Event] = relationship(back_populates="registrations")
    participant: Mapped[Participant | None] = relationship(
        "Participant",
        back_populates="registrations",
        foreign_keys=[participant_id],
    )
    team: Mapped[Team | None] = relationship(
        "Team",
        back_populates="registrations",
        foreign_keys=[team_id],
    )
    check_ins: Mapped[list[CheckIn]] = relationship(
        back_populates="registration", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "((participant_id IS NOT NULL)::int + (team_id IS NOT NULL)::int) = 1",
            name="ck_registrations_subject_xor",
        ),
        CheckConstraint(
            "(subject_type = 'PARTICIPANT' AND participant_id IS NOT NULL) OR "
            "(subject_type = 'TEAM' AND team_id IS NOT NULL)",
            name="ck_registrations_subject_match",
        ),
        Index(
            "uq_registrations_event_participant",
            "event_id",
            "participant_id",
            unique=True,
            postgresql_where=text("participant_id IS NOT NULL"),
        ),
        Index(
            "uq_registrations_event_team",
            "event_id",
            "team_id",
            unique=True,
            postgresql_where=text("team_id IS NOT NULL"),
        ),
    )


class CheckIn(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "check_ins"

    registration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False
    )
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL")
    )
    method: Mapped[CheckInMethod] = mapped_column(
        Enum(
            CheckInMethod,
            name="check_in_method",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    registration: Mapped[Registration] = relationship(back_populates="check_ins")
    recorded_by_participant: Mapped[Participant | None] = relationship(
        "Participant",
        foreign_keys=[recorded_by],
    )


class Round(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rounds"

    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RoundStatus] = mapped_column(
        Enum(
            RoundStatus,
            name="round_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=RoundStatus.SCHEDULED,
        server_default=text("'scheduled'::text"),
    )
    pairings_released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    games_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submissions_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pairing_seed: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(Text)

    stage: Mapped[Stage] = relationship(back_populates="rounds")
    matches: Mapped[list[Match]] = relationship(
        back_populates="round", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("stage_id", "number", name="uq_rounds_stage_number"),
    )


class Match(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matches"

    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    pairing_order: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[MatchState] = mapped_column(
        Enum(MatchState, name="match_state", native_enum=False, create_constraint=True),
        nullable=False,
        default=MatchState.SCHEDULED,
        server_default=text("'scheduled'::text"),
    )
    table_number: Mapped[int | None] = mapped_column(Integer)
    judge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL")
    )
    stream_url: Mapped[str | None] = mapped_column(String)
    slot_a_participant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL")
    )
    slot_b_participant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL")
    )
    slot_a_team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL")
    )
    slot_b_team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL")
    )
    slot_a_seed: Mapped[int | None] = mapped_column(Integer)
    slot_b_seed: Mapped[int | None] = mapped_column(Integer)
    wins_a: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    wins_b: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    draws: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    total_points_a: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    total_points_b: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    reported_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL")
    )
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL")
    )
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    round: Mapped[Round] = relationship(back_populates="matches")
    games: Mapped[list[MatchGame]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("round_id", "pairing_order", name="uq_matches_round_order"),
        CheckConstraint(
            "NOT (slot_a_participant_id IS NOT NULL AND slot_a_team_id IS NOT NULL)",
            name="ck_matches_slot_a_exclusive",
        ),
        CheckConstraint(
            "NOT (slot_b_participant_id IS NOT NULL AND slot_b_team_id IS NOT NULL)",
            name="ck_matches_slot_b_exclusive",
        ),
    )


class MatchGame(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "match_games"

    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    game_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[MatchOutcome] = mapped_column(
        Enum(
            MatchOutcome,
            name="match_outcome",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=MatchOutcome.PENDING,
        server_default=text("'pending'::text"),
    )
    score_a: Mapped[int | None] = mapped_column(Integer)
    score_b: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    match: Mapped[Match] = relationship(back_populates="games")

    __table_args__ = (
        UniqueConstraint("match_id", "game_number", name="uq_match_games_number"),
    )


# Late imports for type checking / circular references
from .participants import Participant, Team  # noqa: E402
from .standings import Standing  # noqa: E402
from .structure import Season  # noqa: E402

__all__ = [
    "CheckIn",
    "Event",
    "Match",
    "MatchGame",
    "Registration",
    "Round",
    "Stage",
]
