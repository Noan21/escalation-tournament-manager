from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_scoring_service
from api.app.schemas.rounds import MatchProfile, MatchResultSubmit, ReopenRoundRequest, RoundProfile
from api.app.services.exceptions import ServiceError
from api.app.services.scoring import ScoringService

router = APIRouter(tags=["scoring"])


def _error(exc: ServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/api/matches/{match_id}/result", response_model=MatchProfile)
async def submit_match_result(
    match_id: UUID,
    payload: MatchResultSubmit,
    service: ScoringService = Depends(get_scoring_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> MatchProfile:
    if payload.match_id != match_id:
        payload = payload.model_copy(update={"match_id": match_id})
    try:
        return await service.submit_match_result(payload, actor_id=current_user.id)
    except ServiceError as exc:
        raise _error(exc) from exc


@router.post("/api/rounds/{round_id}/lock", response_model=RoundProfile)
async def lock_round(
    round_id: UUID,
    service: ScoringService = Depends(get_scoring_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> RoundProfile:
    try:
        return await service.lock_round(round_id, actor_id=current_user.id)
    except ServiceError as exc:
        raise _error(exc) from exc


@router.post("/api/rounds/{round_id}/reopen", response_model=RoundProfile)
async def reopen_round(
    round_id: UUID,
    request: ReopenRoundRequest,
    service: ScoringService = Depends(get_scoring_service),
    current_user=Depends(require_roles("admin")),
) -> RoundProfile:
    try:
        return await service.reopen_round(round_id, request, actor_id=current_user.id)
    except ServiceError as exc:
        raise _error(exc) from exc


__all__ = ["router"]
