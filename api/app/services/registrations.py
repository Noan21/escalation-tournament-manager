from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.events import CheckIn, Event, Registration
from api.app.models.enums import RegistrationStatus, RegistrationSubjectType
from api.app.models.participants import Participant, Team
from api.app.schemas.mappers import to_check_in_record, to_event_registration
from api.app.schemas.players import (
    CheckInRecord,
    CheckInRequest,
    EventRegistration,
    EventRegistrationCreate,
    SeedRosterResult,
)
from api.app.services.exceptions import ConflictError, NotFoundError


class RegistrationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _event_query(self, event_id: UUID) -> Event:
        event = await self.session.get(Event, event_id)
        if not event:
            raise NotFoundError("Event not found")
        return event

    async def _load_registration(self, registration_id: UUID) -> Registration:
        registration = await self.session.get(Registration, registration_id)
        if not registration:
            raise NotFoundError("Registration not found")
        return registration

    async def _ensure_subject_exists(
        self,
        subject_type: RegistrationSubjectType,
        participant_id: UUID | None,
        team_id: UUID | None,
    ) -> None:
        if subject_type == RegistrationSubjectType.PARTICIPANT:
            participant = await self.session.get(Participant, participant_id)
            if not participant:
                raise NotFoundError("Participant not found")
        else:
            team = await self.session.get(Team, team_id)
            if not team:
                raise NotFoundError("Team not found")

    async def create_registration(
        self,
        event_id: UUID,
        payload: EventRegistrationCreate,
        *,
        actor_id: UUID,
    ) -> EventRegistration:
        await self._event_query(event_id)
        await self._ensure_subject_exists(
            payload.subject_type,
            payload.participant_id,
            payload.team_id,
        )

        subject_token = payload.subject_type.name

        existing_query: Select[tuple[Registration]] = select(Registration).where(
            and_(
                Registration.event_id == event_id,
                Registration.subject_type == subject_token,
                Registration.participant_id == payload.participant_id,
                Registration.team_id == payload.team_id,
            )
        )
        existing = await self.session.execute(existing_query)
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("Registration already exists for subject")

        registration = Registration(
            event_id=event_id,
            subject_type=subject_token,
            participant_id=payload.participant_id,
            team_id=payload.team_id,
            seeding_score=payload.seeding_score,
            notes=payload.notes,
            registered_at=datetime.now(tz=UTC),
            meta=payload.meta,
        )
        self.session.add(registration)
        await self.session.flush()
        await self.session.refresh(registration)
        await self.session.commit()
        return to_event_registration(registration)

    async def update_registration_status(
        self,
        registration_id: UUID,
        status: RegistrationStatus,
        *,
        actor_id: UUID,
    ) -> EventRegistration:
        registration = await self._load_registration(registration_id)
        now = datetime.now(tz=UTC)
        registration.status = status
        if status == RegistrationStatus.CONFIRMED and not registration.confirmed_at:
            registration.confirmed_at = now
        if status == RegistrationStatus.CHECKED_IN:
            registration.confirmed_at = registration.confirmed_at or now
            registration.checked_in_at = now
        await self.session.commit()
        await self.session.refresh(registration)
        return to_event_registration(registration)

    async def list_event_registrations(
        self,
        event_id: UUID,
        *,
        include_waitlist: bool = False,
    ) -> list[EventRegistration]:
        await self._event_query(event_id)
        query: Select[tuple[Registration]] = select(Registration).where(
            Registration.event_id == event_id
        )
        if not include_waitlist:
            query = query.where(Registration.status != RegistrationStatus.WITHDRAWN)

        result = await self.session.execute(query.order_by(Registration.registered_at))
        registrations = result.scalars().all()
        return [to_event_registration(reg) for reg in registrations]

    async def record_check_in(
        self,
        registration_id: UUID,
        request: CheckInRequest,
        *,
        actor_id: UUID,
    ) -> CheckInRecord:
        registration = await self._load_registration(registration_id)
        now = datetime.now(tz=UTC)
        check_in = CheckIn(
            registration_id=registration.id,
            recorded_by=actor_id,
            method=request.method,
            note=request.note,
            recorded_at=now,
        )
        registration.status = RegistrationStatus.CHECKED_IN
        registration.checked_in_at = now
        registration.confirmed_at = registration.confirmed_at or now
        self.session.add(check_in)
        await self.session.commit()
        await self.session.refresh(check_in)
        return to_check_in_record(check_in)

    async def seed_event_roster(
        self,
        event_id: UUID,
        *,
        actor_id: UUID,
    ) -> SeedRosterResult:
        # Placeholder implementation—future enhancements can import roster templates.
        await self._event_query(event_id)
        return SeedRosterResult(created=0, skipped=0, already_present=0)


__all__ = ["RegistrationService"]
