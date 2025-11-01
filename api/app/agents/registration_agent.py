from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.schemas.players import EventRegistration, EventRegistrationCreate, SeedRosterResult
from api.app.services.registrations import RegistrationService


class RegistrationAgent:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.service = RegistrationService(session)

    async def run(self, event_id: UUID, registrations: Sequence[EventRegistrationCreate], *, actor_id: UUID) -> SeedRosterResult:
        created = skipped = 0
        for payload in registrations:
            try:
                await self.service.create_registration(event_id, payload, actor_id=actor_id)
                created += 1
            except Exception:
                skipped += 1
        return SeedRosterResult(created=created, skipped=skipped, already_present=0)


__all__ = ["RegistrationAgent"]
