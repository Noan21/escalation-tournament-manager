from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.events import Event, Round, Stage
from api.app.models.structure import Season
from api.app.models.enums import NotificationSubjectType
from api.app.schemas.notifications import EventTrigger, NotificationDelivery
from api.app.services.exceptions import NotFoundError
from api.app.services.notifications import NotificationDispatcher, NotificationService


class NotificationAgent:
    """High-level orchestration for notification dispatch."""

    def __init__(
        self,
        session: AsyncSession,
        dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self.session = session
        self.service = NotificationService(session, dispatcher=dispatcher)

    async def notify(
        self,
        trigger: EventTrigger,
        *,
        stage_id: UUID | None = None,
        round_id: UUID | None = None,
        season_id: UUID | None = None,
        organization_id: UUID | None = None,
        recipient_subject_type: NotificationSubjectType | None = None,
        recipient_subject_ids: list[UUID] | None = None,
        subject: str | None = None,
        body_text: str | None = None,
        body_html: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[NotificationDelivery]:
        context = dict(context or {})
        inferred_stage_id = stage_id
        inferred_org_id = organization_id
        subject_suffix = ""

        if round_id:
            round_obj = await self._load_round(round_id)
            context.setdefault("round_id", str(round_obj.id))
            context.setdefault("round_number", round_obj.number)
            context.setdefault("round_status", round_obj.status)
            inferred_stage_id = inferred_stage_id or round_obj.stage_id

        if inferred_stage_id:
            stage, event = await self._load_stage_with_event(inferred_stage_id)
            context.setdefault("stage_id", str(stage.id))
            context.setdefault("stage_name", stage.name)
            context.setdefault("event_id", str(event.id))
            context.setdefault("event_name", event.name)
            context.setdefault("event_status", event.status)
            if event.starts_at:
                context.setdefault("event_starts_at", event.starts_at.isoformat())
            inferred_org_id = inferred_org_id or event.organization_id
            subject_suffix = f" – {event.name}"

        if season_id:
            season = await self._load_season(season_id)
            context.setdefault("season_id", str(season.id))
            context.setdefault("season_name", season.name)
            context.setdefault("season_status", season.status)
            inferred_org_id = inferred_org_id or season.organization_id

        subject_line = subject
        if subject_line is None and subject_suffix:
            subject_line = f"{_subject_for_trigger(trigger)}{subject_suffix}"

        return await self.service.dispatch_notifications(
            trigger=trigger,
            organization_id=inferred_org_id,
            recipient_subject_type=recipient_subject_type,
            recipient_subject_ids=recipient_subject_ids,
            subject=subject_line,
            body_text=body_text,
            body_html=body_html,
            context=context,
        )

    async def _load_round(self, round_id: UUID) -> Round:
        round_obj = await self.session.get(Round, round_id)
        if not round_obj:
            raise NotFoundError("Round not found")
        return round_obj

    async def _load_stage_with_event(self, stage_id: UUID) -> tuple[Stage, Event]:
        stmt = (
            select(Stage, Event)
            .join(Event, Stage.event_id == Event.id)
            .where(Stage.id == stage_id)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if not row:
            raise NotFoundError("Stage not found")
        stage, event = row
        return stage, event

    async def _load_season(self, season_id: UUID) -> Season:
        season = await self.session.get(Season, season_id)
        if not season:
            raise NotFoundError("Season not found")
        return season


__all__ = ["NotificationAgent"]


def _subject_for_trigger(trigger: EventTrigger) -> str:
    mapping = {
        "registration_confirmed": "Registration Confirmed",
        "round_pairings": "New Round Pairings Available",
        "round_locked": "Round Results Locked",
        "standings_published": "Standings Updated",
        "season_leaderboard": "Season Leaderboard Update",
    }
    return mapping.get(trigger, f"Notification: {trigger.replace('_', ' ').title()}")
