from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_pairing_service
from api.app.schemas.rounds import (
    AssignTablesRequest,
    GenerateRoundRequest,
    PairingPreview,
    RoundProfile,
)
from api.app.services.exceptions import ServiceError
from api.app.services.pairings import PairingService

router = APIRouter(prefix="/api/stages/{stage_id}/pairings", tags=["pairings"])


def _handle(exc: ServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/rounds", response_model=RoundProfile)
async def generate_round(
    stage_id: UUID,
    request: GenerateRoundRequest,
    service: PairingService = Depends(get_pairing_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> RoundProfile:
    try:
        return await service.generate_round_pairings(stage_id, request, actor_id=current_user.id)
    except ServiceError as exc:
        raise _handle(exc) from exc


@router.post("/rounds/preview", response_model=PairingPreview)
async def preview_round(
    stage_id: UUID,
    request: GenerateRoundRequest,
    service: PairingService = Depends(get_pairing_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> PairingPreview:
    try:
        return await service.preview_pairings(stage_id, request, actor_id=current_user.id)
    except ServiceError as exc:
        raise _handle(exc) from exc


@router.post("/rounds/{round_id}/assign-tables", response_model=RoundProfile)
async def assign_tables(
    stage_id: UUID,
    round_id: UUID,
    request: AssignTablesRequest,
    service: PairingService = Depends(get_pairing_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> RoundProfile:
    try:
        return await service.assign_tables(round_id, request, actor_id=current_user.id)
    except ServiceError as exc:
        raise _handle(exc) from exc


__all__ = ["router"]
