from __future__ import annotations

from fastapi import APIRouter, Depends

from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_maintenance_service
from api.app.schemas.maintenance import (
    ArchiveTriggerRequest,
    CleanupTriggerRequest,
    MaintenanceSummary,
    MigrationTriggerRequest,
)
from api.app.services.maintenance import MaintenanceService


router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.post("/run-cleanup", response_model=MaintenanceSummary)
async def run_cleanup(
    payload: CleanupTriggerRequest | None = None,
    service: MaintenanceService = Depends(get_maintenance_service),
    current_user=Depends(require_roles("admin")),
) -> MaintenanceSummary:
    request = payload or CleanupTriggerRequest()
    return await service.run_cleanup(request)


@router.post("/run-archive", response_model=MaintenanceSummary)
async def run_archive(
    payload: ArchiveTriggerRequest | None = None,
    service: MaintenanceService = Depends(get_maintenance_service),
    current_user=Depends(require_roles("admin")),
) -> MaintenanceSummary:
    request = payload or ArchiveTriggerRequest()
    return await service.run_archive(request)


@router.post("/run-migrations", response_model=MaintenanceSummary)
async def run_migration_checks(
    payload: MigrationTriggerRequest | None = None,
    service: MaintenanceService = Depends(get_maintenance_service),
    current_user=Depends(require_roles("admin")),
) -> MaintenanceSummary:
    request = payload or MigrationTriggerRequest()
    return await service.run_migration_checks(request)


__all__ = ["router"]
