from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.schemas.season import SeasonLeaderboard
from api.app.services.season import SeasonService


class SeasonAgent:
    def __init__(self, session: AsyncSession) -> None:
        self.service = SeasonService(session)

    async def recompute(self, season_id: UUID, *, actor_id: UUID | None = None) -> SeasonLeaderboard:
        return await self.service.recompute_season_leaderboard(season_id, actor_id=actor_id)


__all__ = ["SeasonAgent"]
