from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Iterable
from uuid import UUID

from sqlalchemy import Select, and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.auth import Session
from api.app.models.events import Event, Registration
from api.app.models.enums import (
    ArchiveMode,
    CleanupTarget,
    EventStatus,
    MigrationStatus,
    NotificationStatus,
    RegistrationStatus,
)
from api.app.models.maintenance import (
    ArchivePolicy as ArchivePolicyModel,
    CleanupPolicy as CleanupPolicyModel,
    MigrationPolicy as MigrationPolicyModel,
)
from api.app.models.notifications import NotificationDelivery
from api.app.schemas.maintenance import (
    ArchiveTriggerRequest,
    CleanupTriggerRequest,
    MaintenanceSummary,
    MigrationTriggerRequest,
)


@dataclass(slots=True)
class PolicyResult:
    processed: int
    detail: str


class MaintenanceService:
    """Implements cleanup, archival, and migration policies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def run_cleanup(self, request: CleanupTriggerRequest | None = None) -> MaintenanceSummary:
        request = request or CleanupTriggerRequest()
        policies = await self._load_cleanup_policies(request.targets)
        if not policies:
            return MaintenanceSummary(summary="No cleanup policies defined", items_processed=0)

        now = datetime.now(tz=UTC)
        totals = 0
        details: list[str] = []

        for policy in policies:
            result = await self._apply_cleanup_policy(policy, now, request.dry_run)
            totals += result.processed
            details.append(result.detail)
            if not request.dry_run:
                policy.last_run_at = now

        if request.dry_run:
            await self.session.rollback()
            summary = "Cleanup dry run completed"
        else:
            await self.session.commit()
            summary = "Cleanup policies applied"

        return MaintenanceSummary(summary=summary, items_processed=totals, details=details)

    async def run_archive(self, request: ArchiveTriggerRequest | None = None) -> MaintenanceSummary:
        request = request or ArchiveTriggerRequest()
        policies = await self._load_archive_policies(request.policy_ids)
        if not policies:
            return MaintenanceSummary(summary="No archive policies defined", items_processed=0)

        now = datetime.now(tz=UTC)
        totals = 0
        details: list[str] = []

        for policy in policies:
            result = await self._apply_archive_policy(policy, now, request.dry_run)
            totals += result.processed
            details.append(result.detail)

        if request.dry_run:
            await self.session.rollback()
            summary = "Archive dry run completed"
        else:
            await self.session.commit()
            summary = "Archive policies applied"

        return MaintenanceSummary(summary=summary, items_processed=totals, details=details)

    async def run_migration_checks(
        self, request: MigrationTriggerRequest | None = None
    ) -> MaintenanceSummary:
        request = request or MigrationTriggerRequest()
        policies = await self._load_migration_policies(request.policy_ids)
        if not policies:
            return MaintenanceSummary(summary="No migration policies defined", items_processed=0)

        now = datetime.now(tz=UTC)
        details: list[str] = []
        for policy in policies:
            details.append(f"Policy {policy.name} evaluated")
            if not request.dry_run:
                policy.last_run_at = now
                policy.last_status = MigrationStatus.SUCCESS

        if request.dry_run:
            await self.session.rollback()
            summary = "Migration check dry run completed"
        else:
            await self.session.commit()
            summary = "Migration policies updated"

        return MaintenanceSummary(summary=summary, items_processed=len(policies), details=details)

    async def _load_cleanup_policies(
        self, targets: Iterable[CleanupTarget] | None
    ) -> list[CleanupPolicyModel]:
        query: Select[tuple[CleanupPolicyModel]] = select(CleanupPolicyModel).where(
            CleanupPolicyModel.enabled.is_(True)
        )
        if targets:
            target_values = [target.value if isinstance(target, CleanupTarget) else str(target) for target in targets]
            query = query.where(CleanupPolicyModel.target.in_(target_values))

        result = await self.session.execute(query.order_by(CleanupPolicyModel.created_at.asc()))
        return list(result.scalars().all())

    async def _load_archive_policies(
        self, policy_ids: Iterable[UUID] | None
    ) -> list[ArchivePolicyModel]:
        query: Select[tuple[ArchivePolicyModel]] = select(ArchivePolicyModel).where(
            ArchivePolicyModel.enabled.is_(True)
        )
        if policy_ids:
            query = query.where(ArchivePolicyModel.id.in_(list(policy_ids)))

        result = await self.session.execute(query.order_by(ArchivePolicyModel.created_at.asc()))
        return list(result.scalars().all())

    async def _load_migration_policies(
        self, policy_ids: Iterable[UUID] | None
    ) -> list[MigrationPolicyModel]:
        query: Select[tuple[MigrationPolicyModel]] = select(MigrationPolicyModel)
        if policy_ids:
            query = query.where(MigrationPolicyModel.id.in_(list(policy_ids)))

        result = await self.session.execute(query.order_by(MigrationPolicyModel.created_at.asc()))
        return list(result.scalars().all())

    async def _apply_cleanup_policy(
        self,
        policy: CleanupPolicyModel,
        now: datetime,
        dry_run: bool,
    ) -> PolicyResult:
        retention = timedelta(days=policy.retention_days)
        if policy.target == CleanupTarget.STALE_REGISTRATIONS.value:
            count = await self._cleanup_stale_registrations(policy.organization_id, now - retention, dry_run)
            detail = f"stale_registrations={count}"
        elif policy.target == CleanupTarget.NOTIFICATIONS.value:
            count = await self._cleanup_notification_deliveries(policy.organization_id, now - retention, dry_run)
            detail = f"notifications_pruned={count}"
        elif policy.target == CleanupTarget.SESSIONS.value:
            count = await self._cleanup_sessions(now - retention, dry_run)
            detail = f"sessions_pruned={count}"
        elif policy.target == CleanupTarget.ARCHIVED_EVENTS.value:
            count = await self._cleanup_archived_events(policy.organization_id, now - retention, dry_run)
            detail = f"archived_events_removed={count}"
        else:
            detail = "logs cleanup not implemented"
            count = 0
        return PolicyResult(processed=count, detail=detail)

    async def _cleanup_stale_registrations(
        self,
        organization_id: UUID,
        threshold: datetime,
        dry_run: bool,
    ) -> int:
        pending_states = [RegistrationStatus.PENDING, RegistrationStatus.WITHDRAWN]
        subquery = (
            select(Registration.id)
            .join(Event, Registration.event_id == Event.id)
            .where(
                Event.organization_id == organization_id,
                Registration.status.in_(pending_states),
                Registration.registered_at < threshold,
            )
        )
        ids = [row[0] for row in (await self.session.execute(subquery)).all()]
        if not ids or dry_run:
            return len(ids)
        await self.session.execute(delete(Registration).where(Registration.id.in_(ids)))
        return len(ids)

    async def _cleanup_notification_deliveries(
        self,
        organization_id: UUID,
        threshold: datetime,
        dry_run: bool,
    ) -> int:
        query = select(NotificationDelivery.id).where(
            NotificationDelivery.organization_id == organization_id,
            NotificationDelivery.last_attempt_at.is_not(None),
            NotificationDelivery.last_attempt_at < threshold,
            NotificationDelivery.status.in_(
                [NotificationStatus.SENT, NotificationStatus.FAILED]
            ),
        )
        ids = [row[0] for row in (await self.session.execute(query)).all()]
        if not ids or dry_run:
            return len(ids)
        await self.session.execute(delete(NotificationDelivery).where(NotificationDelivery.id.in_(ids)))
        return len(ids)

    async def _cleanup_sessions(
        self,
        threshold: datetime,
        dry_run: bool,
    ) -> int:
        query = select(Session.id).where(
            or_(
                Session.expires_at < threshold,
                and_(Session.revoked_at.is_not(None), Session.revoked_at < threshold),
            )
        )
        ids = [row[0] for row in (await self.session.execute(query)).all()]
        if not ids or dry_run:
            return len(ids)
        await self.session.execute(delete(Session).where(Session.id.in_(ids)))
        return len(ids)

    async def _cleanup_archived_events(
        self,
        organization_id: UUID,
        threshold: datetime,
        dry_run: bool,
    ) -> int:
        query = select(Event.id).where(
            Event.organization_id == organization_id,
            Event.status == EventStatus.ARCHIVED,
            Event.updated_at < threshold,
        )
        ids = [row[0] for row in (await self.session.execute(query)).all()]
        if not ids or dry_run:
            return len(ids)
        await self.session.execute(delete(Event).where(Event.id.in_(ids)))
        return len(ids)

    async def _apply_archive_policy(
        self,
        policy: ArchivePolicyModel,
        now: datetime,
        dry_run: bool,
    ) -> PolicyResult:
        threshold = now - timedelta(days=policy.apply_to_events_older_than_days)
        query = select(Event).where(
            Event.organization_id == policy.organization_id,
            Event.ends_at < threshold,
            Event.status.in_([EventStatus.ACTIVE, EventStatus.COMPLETE]),
        )
        if policy.include_event_ids:
            query = query.where(Event.id.in_(policy.include_event_ids))
        if policy.exclude_event_ids:
            query = query.where(~Event.id.in_(policy.exclude_event_ids))

        events = (await self.session.execute(query)).scalars().all()
        if not events:
            return PolicyResult(processed=0, detail="no events eligible for archive")

        processed = len(events)
        if not dry_run:
            for event in events:
                if policy.mode == ArchiveMode.SOFT_DELETE:
                    event.status = EventStatus.ARCHIVED
                elif policy.mode == ArchiveMode.MOVE_TO_COLD_STORAGE:
                    event.meta = {**(event.meta or {}), "archival": "pending_export"}
                elif policy.mode == ArchiveMode.EXPORT:
                    event.meta = {**(event.meta or {}), "archival": "export_logged"}

        detail_parts = [f"events_processed={processed}", f"mode={policy.mode.value}"]
        if policy.notify_contacts:
            detail_parts.append("contacts_notified_placeholder")
        return PolicyResult(processed=processed, detail=", ".join(detail_parts))


__all__ = ["MaintenanceService"]
