from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins.base import PairingRequest
from app.core.plugins.registry import pairing_registry
from app.models import Match, Round, Stage


async def run(stage_id: str, round_number: int, session: AsyncSession) -> dict[str, int]:
    stage_uuid = uuid.UUID(stage_id)
    stage = await session.scalar(select(Stage).where(Stage.id == stage_uuid))
    if stage is None:
        raise ValueError("Stage not found")

    pairing_request = PairingRequest(stage=stage, round_number=round_number)
    strategy = pairing_registry.get(stage.format_key)
    matches = await strategy.generate(pairing_request, session)

    round_obj = Round(stage_id=stage.id, number=round_number)
    session.add(round_obj)
    await session.flush()

    match_models = [
        Match(
            round_id=round_obj.id,
            table_no=descriptor.table_no,
            meta=descriptor.meta or {},
            side_a_participant_id=descriptor.side_a.get("participant_id"),
            side_b_participant_id=descriptor.side_b.get("participant_id"),
            side_a_team_id=descriptor.side_a.get("team_id"),
            side_b_team_id=descriptor.side_b.get("team_id"),
        )
        for descriptor in matches
    ]

    session.add_all(match_models)
    await session.commit()
    return {"round": round_number, "matches_created": len(match_models)}
