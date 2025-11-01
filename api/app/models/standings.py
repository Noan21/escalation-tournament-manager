from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .enums import HeadToHeadResult, StandingSubjectType


class Standing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "standings"

    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"), nullable=False
    )
    subject_type: Mapped[StandingSubjectType] = mapped_column(
        Enum(
            StandingSubjectType,
            name="standing_subject_type",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    match_points: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    wins: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    losses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    draws: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    byes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    total_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    strength_of_schedule: Mapped[Numeric | None] = mapped_column(Numeric)
    opponent_match_win_pct: Mapped[Numeric | None] = mapped_column(Numeric)
    head_to_head: Mapped[HeadToHeadResult | None] = mapped_column(
        Enum(
            HeadToHeadResult,
            name="head_to_head_result",
            native_enum=False,
            create_constraint=True,
        )
    )
    breakers_applied: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    stage: Mapped[Stage] = relationship(back_populates="standings")
    snapshots: Mapped[list[TiebreakSnapshot]] = relationship(
        back_populates="standing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "stage_id",
            "subject_type",
            "subject_id",
            name="uq_standings_stage_subject",
        ),
    )


class TiebreakSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tiebreak_snapshots"

    standings_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("standings.id", ondelete="CASCADE"), nullable=False
    )
    breaker_key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[Numeric] = mapped_column(Numeric, nullable=False)
    order_applied: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=False,
        server_default=text("'{}'::uuid[]"),
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    standing: Mapped[Standing] = relationship(back_populates="snapshots")


# Circular references
from .events import Stage  # noqa: E402

__all__ = ["Standing", "TiebreakSnapshot"]
