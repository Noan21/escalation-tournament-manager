from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.schemas.standings import ComputeStandingsRequest, StandingsPayload
from api.app.services.standings import StandingsService


class StandingAgent:
    def __init__(self, session: AsyncSession) -> None:
        self.service = StandingsService(session)

    async def compute(self, stage_id: UUID, request: ComputeStandingsRequest | None, *, actor_id: UUID | None) -> StandingsPayload:
        scoring_key = request.scoring_profile_key if request else None
        return await self.service.compute_stage_standings(stage_id, scoring_profile_key=scoring_key, actor_id=actor_id)

    async def publish(self, stage_id: UUID, *, actor_id: UUID) -> StandingsPayload:
        return await self.service.publish_stage_standings(stage_id, actor_id=actor_id)


__all__ = ["StandingAgent"]
