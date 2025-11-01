from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field

from api.app.models.enums import ArchiveMode, CleanupTarget, MigrationStatus


class CleanupPolicy(BaseModel):
    id: UUID
    organization_id: UUID
    target: CleanupTarget
    run_every_hours: int = Field(..., ge=1)
    retention_days: int = Field(..., ge=1)
    enabled: bool = True
    last_run_at: datetime | None = None
    meta: dict[str, object] = Field(default_factory=dict)

    @property
    def retention_timedelta(self) -> timedelta:
        return timedelta(days=self.retention_days)


class ArchivePolicy(BaseModel):
    id: UUID
    organization_id: UUID
    apply_to_events_older_than_days: int = Field(..., ge=1)
    mode: ArchiveMode = ArchiveMode.SOFT_DELETE
    include_event_ids: list[UUID] = Field(default_factory=list)
    exclude_event_ids: list[UUID] = Field(default_factory=list)
    notify_contacts: bool = False
    enabled: bool = True


class MigrationPolicy(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    run_on_startup: bool = True
    retry_on_failure: bool = True
    max_retries: int = Field(default=3, ge=0)
    last_run_at: datetime | None = None
    last_status: MigrationStatus | None = None


class CleanupTriggerRequest(BaseModel):
    targets: list[CleanupTarget] | None = None
    dry_run: bool = False


class ArchiveTriggerRequest(BaseModel):
    policy_ids: list[UUID] | None = None
    dry_run: bool = False


class MigrationTriggerRequest(BaseModel):
    policy_ids: list[UUID] | None = None
    dry_run: bool = False


class MaintenanceSummary(BaseModel):
    summary: str
    items_processed: int = 0
    details: list[str] = Field(default_factory=list)


__all__ = [
    "ArchivePolicy",
    "ArchiveTriggerRequest",
    "CleanupPolicy",
    "CleanupTriggerRequest",
    "MaintenanceSummary",
    "MigrationPolicy",
    "MigrationTriggerRequest",
]
