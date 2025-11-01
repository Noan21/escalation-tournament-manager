from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_season_service
from api.app.schemas.events import EventProfile
from api.app.schemas.season import SeasonLeaderboard
from api.app.schemas.structure import SeasonProfile
from api.app.services.exceptions import ServiceError
from api.app.services.season import SeasonService

router = APIRouter(prefix="/api/seasons", tags=["seasons"])


def _err(exc: ServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/{season_id}/set-current", response_model=SeasonProfile)
async def set_current_season(
    season_id: UUID,
    service: SeasonService = Depends(get_season_service),
    current_user=Depends(require_roles("admin")),
) -> SeasonProfile:
    try:
        return await service.set_current_season(season_id, actor_id=current_user.id)
    except ServiceError as exc:
        raise _err(exc) from exc


@router.post("/{season_id}/recompute", response_model=SeasonLeaderboard)
async def recompute_leaderboard(
    season_id: UUID,
    service: SeasonService = Depends(get_season_service),
    current_user=Depends(require_roles("admin")),
) -> SeasonLeaderboard:
    try:
        return await service.recompute_season_leaderboard(season_id, actor_id=current_user.id)
    except ServiceError as exc:
        raise _err(exc) from exc


@router.get("/{season_id}/events", response_model=list[EventProfile])
async def list_season_events(
    season_id: UUID,
    service: SeasonService = Depends(get_season_service),
    current_user=Depends(require_roles("player", "staff", "admin")),
) -> list[EventProfile]:
    try:
        return await service.list_season_events(season_id)
    except ServiceError as exc:
        raise _err(exc) from exc


__all__ = ["router"]
