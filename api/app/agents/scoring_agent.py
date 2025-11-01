from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.schemas.rounds import MatchResultSubmit, RoundProfile
from api.app.services.scoring import ScoringService


class ScoringAgent:
    def __init__(self, session: AsyncSession) -> None:
        self.service = ScoringService(session)

    async def submit_result(self, payload: MatchResultSubmit, *, actor_id: UUID):
        return await self.service.submit_match_result(payload, actor_id=actor_id)

    async def lock_round(self, round_id: UUID, *, actor_id: UUID) -> RoundProfile:
        return await self.service.lock_round(round_id, actor_id=actor_id)


__all__ = ["ScoringAgent"]
