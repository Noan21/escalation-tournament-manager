from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_standings_service
from api.app.schemas.standings import ComputeStandingsRequest, StandingsPayload
from api.app.services.exceptions import ServiceError
from api.app.services.standings import StandingsService

router = APIRouter(prefix="/api/stages/{stage_id}/standings", tags=["standings"])


def _error(exc: ServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/compute", response_model=StandingsPayload)
async def compute_standings(
    stage_id: UUID,
    request: ComputeStandingsRequest | None = None,
    service: StandingsService = Depends(get_standings_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> StandingsPayload:
    try:
        scoring_key = request.scoring_profile_key if request else None
        return await service.compute_stage_standings(stage_id, scoring_profile_key=scoring_key, actor_id=current_user.id)
    except ServiceError as exc:
        raise _error(exc) from exc


@router.get("", response_model=StandingsPayload)
async def get_standings(
    stage_id: UUID,
    refresh: bool = Query(False),
    service: StandingsService = Depends(get_standings_service),
    current_user=Depends(require_roles("player", "staff", "admin")),
) -> StandingsPayload:
    try:
        if refresh:
            return await service.compute_stage_standings(stage_id, scoring_profile_key=None, actor_id=current_user.id)
        return await service.get_stage_standings(stage_id)
    except ServiceError as exc:
        raise _error(exc) from exc


@router.post("/publish", response_model=StandingsPayload)
async def publish_standings(
    stage_id: UUID,
    service: StandingsService = Depends(get_standings_service),
    current_user=Depends(require_roles("admin")),
) -> StandingsPayload:
    try:
        return await service.publish_stage_standings(stage_id, actor_id=current_user.id)
    except ServiceError as exc:
        raise _error(exc) from exc


__all__ = ["router"]
