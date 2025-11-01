# Maintenance Policies

Pydantic models describing automation policies for cleanup, archiving, and migrations managed by the MaintenanceAgent.

## 🧹 Cleanup Policies

```python
from datetime import datetime, timedelta
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

CleanupTarget = Literal[
    "stale_registrations",
    "archived_events",
    "logs",
    "notifications",
    "sessions",
]


class CleanupPolicy(BaseModel):
    id: UUID
    organization_id: UUID
    target: CleanupTarget
    run_every_hours: int = Field(..., ge=1)
    retention_days: int = Field(..., ge=1)
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    meta: dict[str, object] = Field(default_factory=dict)

    @property
    def retention_timedelta(self) -> timedelta:
        return timedelta(days=self.retention_days)
```

- `retention_days` controls how long data is kept before cleanup.
- `run_every_hours` feeds the scheduler cadence.

## 📦 Archive Policies

```python
ArchiveMode = Literal["soft_delete", "move_to_cold_storage", "export"]


class ArchivePolicy(BaseModel):
    id: UUID
    organization_id: UUID
    apply_to_events_older_than_days: int = Field(..., ge=1)
    mode: ArchiveMode = "soft_delete"
    include_event_ids: list[UUID] = Field(default_factory=list)
    exclude_event_ids: list[UUID] = Field(default_factory=list)
    notify_contacts: bool = False
    enabled: bool = True
```

- Dictates when completed events should be archived and in what manner.

## 🔄 Migration Policies

```python
class MigrationPolicy(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    run_on_startup: bool = True
    retry_on_failure: bool = True
    max_retries: int = Field(default=3, ge=0)
    last_run_at: Optional[datetime] = None
    last_status: Optional[Literal["success", "failure"]] = None
```

- The MaintenanceAgent can read these to determine whether to execute pending data migrations.

## ✅ Implementation Notes

1. Persist policy models in `app/models/maintenance.py`.
2. MaintenanceAgent should filter policies by `enabled` before scheduling jobs.
3. For archive operations, align modes with actual implementations (soft delete vs. export).
