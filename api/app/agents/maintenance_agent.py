from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.schemas.maintenance import (
    ArchiveTriggerRequest,
    CleanupTriggerRequest,
    MaintenanceSummary,
    MigrationTriggerRequest,
)
from api.app.services.maintenance import MaintenanceService


class MaintenanceAgent:
    def __init__(self, session: AsyncSession) -> None:
        self.service = MaintenanceService(session)

    async def run_cleanup(
        self, request: CleanupTriggerRequest | None = None
    ) -> MaintenanceSummary:
        return await self.service.run_cleanup(request)

    async def run_archive(
        self, request: ArchiveTriggerRequest | None = None
    ) -> MaintenanceSummary:
        return await self.service.run_archive(request)

    async def run_migration_checks(
        self, request: MigrationTriggerRequest | None = None
    ) -> MaintenanceSummary:
        return await self.service.run_migration_checks(request)


__all__ = ["MaintenanceAgent"]
