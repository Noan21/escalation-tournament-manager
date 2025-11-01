from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_registration_service
from api.app.schemas.players import (
    CheckInRecord,
    CheckInRequest,
    EventRegistration,
    EventRegistrationCreate,
    SeedRosterResult,
    UpdateRegistrationStatus,
)
from api.app.services.exceptions import ServiceError
from api.app.services.registrations import RegistrationService

router = APIRouter(prefix="/api/registrations", tags=["registrations"])


def _handle_service_error(exc: ServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post(
    "/events/{event_id}",
    response_model=EventRegistration,
    status_code=status.HTTP_201_CREATED,
)
async def create_registration(
    event_id: UUID,
    payload: EventRegistrationCreate,
    service: RegistrationService = Depends(get_registration_service),
    current_user=Depends(require_roles("player", "staff", "admin")),
) -> EventRegistration:
    try:
        return await service.create_registration(event_id, payload, actor_id=current_user.id)
    except ServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.patch(
    "/{registration_id}/status",
    response_model=EventRegistration,
)
async def update_registration_status(
    registration_id: UUID,
    payload: UpdateRegistrationStatus,
    service: RegistrationService = Depends(get_registration_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> EventRegistration:
    try:
        return await service.update_registration_status(
            registration_id,
            payload.status,
            actor_id=current_user.id,
        )
    except ServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.get(
    "/events/{event_id}",
    response_model=list[EventRegistration],
)
async def list_registrations(
    event_id: UUID,
    include_waitlist: bool = Query(False),
    service: RegistrationService = Depends(get_registration_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> list[EventRegistration]:
    try:
        return await service.list_event_registrations(event_id, include_waitlist=include_waitlist)
    except ServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.post(
    "/{registration_id}/check-in",
    response_model=CheckInRecord,
)
async def record_check_in(
    registration_id: UUID,
    payload: CheckInRequest,
    service: RegistrationService = Depends(get_registration_service),
    current_user=Depends(require_roles("staff", "admin")),
) -> CheckInRecord:
    try:
        return await service.record_check_in(
            registration_id,
            payload,
            actor_id=current_user.id,
        )
    except ServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.post(
    "/events/{event_id}/seed",
    response_model=SeedRosterResult,
)
async def seed_event_roster(
    event_id: UUID,
    service: RegistrationService = Depends(get_registration_service),
    current_user=Depends(require_roles("admin")),
) -> SeedRosterResult:
    try:
        return await service.seed_event_roster(event_id, actor_id=current_user.id)
    except ServiceError as exc:
        raise _handle_service_error(exc) from exc


__all__ = ["router"]
