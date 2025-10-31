from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.plugins.registry import pairing_registry, scoring_registry
from app.models import Event, Stage
from app.schemas.stage import StageCatalog, StageCreate, StageRead

router = APIRouter()


@router.get("/catalog", response_model=StageCatalog)
async def catalog() -> StageCatalog:
    """Expose registered pairing and scoring strategy keys."""
    return StageCatalog(
        pairing_strategies={key: strategy.__class__.__name__ for key, strategy in pairing_registry.catalog.items()},
        scoring_strategies={key: strategy.__class__.__name__ for key, strategy in scoring_registry.catalog.items()},
    )


@router.post("/", response_model=StageRead, status_code=status.HTTP_201_CREATED)
async def create_stage(
    payload: StageCreate,
    session: AsyncSession = Depends(get_session),
) -> Stage:
    event_id = uuid.UUID(payload.event_id)
    event = await session.scalar(select(Event).where(Event.id == event_id))
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    try:
        pairing_registry.get(payload.format_key)
    except KeyError as exc:  # pragma: no cover - thin validation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown pairing strategy") from exc

    try:
        scoring_registry.get(payload.scoring_key)
    except KeyError as exc:  # pragma: no cover - thin validation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown scoring strategy") from exc

    stage = Stage(
        event_id=event.id,
        name=payload.name,
        stage_order=payload.stage_order,
        format_key=payload.format_key,
        scoring_key=payload.scoring_key,
        config=payload.config,
    )
    session.add(stage)
    await session.commit()
    await session.refresh(stage)
    return stage


@router.get("/", response_model=list[StageRead])
async def list_stages(
    event_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[Stage]:
    stage_event_id = uuid.UUID(event_id)
    result = await session.execute(select(Stage).where(Stage.event_id == stage_event_id).order_by(Stage.stage_order))
    return list(result.scalars().all())
