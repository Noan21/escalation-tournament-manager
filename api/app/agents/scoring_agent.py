from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins.base import ScoringContext
from app.core.plugins.registry import scoring_registry
from app.models import Match, Round, Stage


async def run(stage_id: str, round_id: str, session: AsyncSession) -> dict[str, str]:
    stage_uuid = uuid.UUID(stage_id)
    round_uuid = uuid.UUID(round_id)

    stage = await session.scalar(select(Stage).where(Stage.id == stage_uuid))
    if stage is None:
        raise ValueError("Stage not found")

    round_obj = await session.scalar(select(Round).where(Round.id == round_uuid))
    if round_obj is None:
        raise ValueError("Round not found")

    result = await session.execute(select(Match).where(Match.round_id == round_obj.id))
    matches = list(result.scalars().all())

    context = ScoringContext(stage=stage, round=round_obj, matches=matches)
    strategy = scoring_registry.get(stage.scoring_key)
    await strategy.update_standings(context, session)
    await session.commit()
    return {"status": "processed"}
