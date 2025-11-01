from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.schemas.rounds import GenerateRoundRequest, RoundProfile
from api.app.services.pairings import PairingService


class PairingAgent:
    def __init__(self, session: AsyncSession) -> None:
        self.service = PairingService(session)

    async def run(self, stage_id: UUID, request: GenerateRoundRequest, *, actor_id: UUID) -> RoundProfile:
        return await self.service.generate_round_pairings(stage_id, request, actor_id=actor_id)


__all__ = ["PairingAgent"]
