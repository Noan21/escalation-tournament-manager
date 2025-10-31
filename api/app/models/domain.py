import enum
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"


class StageSubject(str, enum.Enum):
    PARTICIPANT = "participant"
    TEAM = "team"


class MatchState(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    BYE = "bye"
    CANCELLED = "cancelled"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    seasons: Mapped[list["Season"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="seasons")
    events: Mapped[list["Event"]] = relationship(back_populates="season", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    members: Mapped[list["TeamMember"]] = relationship(back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "participant_id", name="uq_team_participant"),)

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), primary_key=True
    )

    team: Mapped["Team"] = relationship(back_populates="members")
    participant: Mapped["Participant"] = relationship()


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus, name="event_status"), nullable=False, default=EventStatus.DRAFT)

    season: Mapped["Season"] = relationship(back_populates="events")
    stages: Mapped[list["Stage"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Stage(Base):
    __tablename__ = "stages"
    __table_args__ = (Index("ix_stages_order", "event_id", "stage_order"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    format_key: Mapped[str] = mapped_column(String(100), nullable=False)
    scoring_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    event: Mapped["Event"] = relationship(back_populates="stages")
    rounds: Mapped[list["Round"]] = relationship(back_populates="stage", cascade="all, delete-orphan")
    standings: Mapped[list["Standing"]] = relationship(back_populates="stage", cascade="all, delete-orphan")


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("event_id", "participant_id", name="uq_event_participant"),
        UniqueConstraint("event_id", "team_id", name="uq_event_team"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (UniqueConstraint("stage_id", "number", name="uq_stage_round_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    stage: Mapped["Stage"] = relationship(back_populates="rounds")
    matches: Mapped[list["Match"]] = relationship(back_populates="round", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False, index=True
    )
    table_no: Mapped[int] = mapped_column(Integer, nullable=False)
    side_a_participant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("participants.id"), nullable=True)
    side_b_participant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("participants.id"), nullable=True)
    side_a_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    side_b_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    state: Mapped[MatchState] = mapped_column(Enum(MatchState, name="match_state"), default=MatchState.SCHEDULED)
    score_a: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_b: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    round: Mapped["Round"] = relationship(back_populates="matches")


class Standing(Base):
    __tablename__ = "standings"
    __table_args__ = (
        UniqueConstraint("stage_id", "subject_type", "subject_id", name="uq_stage_subject"),
        Index(
            "ix_stage_subject_points",
            "stage_id",
            "subject_type",
            "match_points",
            postgresql_using="btree",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_type: Mapped[StageSubject] = mapped_column(Enum(StageSubject, name="stage_subject"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    match_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tb1: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tb2: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    stage: Mapped["Stage"] = relationship(back_populates="standings")
