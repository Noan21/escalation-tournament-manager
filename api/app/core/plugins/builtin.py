from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins.base import PairingRequest, PairingStrategy, ScoringContext, ScoringStrategy
from app.core.plugins.registry import pairing_registry, scoring_registry


class NullPairingStrategy(PairingStrategy):
    key = "null"

    async def generate(self, request: PairingRequest, session: AsyncSession):
        _ = (request, session)
        return []


class NullScoringStrategy(ScoringStrategy):
    key = "null"

    async def update_standings(self, context: ScoringContext, session: AsyncSession) -> None:
        _ = (context, session)


pairing_registry.register(NullPairingStrategy())
scoring_registry.register(NullScoringStrategy())
