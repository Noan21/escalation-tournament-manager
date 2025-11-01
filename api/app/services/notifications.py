from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable, Protocol
from uuid import UUID

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.notifications import (
    NotificationDelivery as DeliveryModel,
    NotificationPreference as PreferenceModel,
)
from api.app.models.enums import (
    NotificationChannel,
    NotificationStatus,
    NotificationSubjectType,
)
from api.app.schemas.notifications import (
    ChannelConfig,
    EventTrigger,
    NotificationDelivery,
    NotificationMessage,
    NotificationPreference,
)
from api.app.services.exceptions import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DispatchResult:
    status: NotificationStatus
    metadata: dict[str, Any] | None = None
    failure_reason: str | None = None


class NotificationDispatcher(Protocol):
    async def send(self, message: NotificationMessage) -> DispatchResult: ...


class ConsoleNotificationDispatcher:
    """Default dispatcher that logs messages instead of sending them."""

    def __init__(self) -> None:
        self._logger = logger

    async def send(self, message: NotificationMessage) -> DispatchResult:
        payload = {
            "trigger": message.trigger,
            "subject_type": message.recipient_subject_type,
            "subject_id": str(message.recipient_subject_id),
            "channel": message.channel,
            "address": message.address,
            "subject": message.subject,
            "body_text": message.body_text,
            "metadata": message.metadata,
        }
        self._logger.info("Dispatching notification: %s", json.dumps(payload))
        return DispatchResult(
            status=NotificationStatus.SENT,
            metadata={"backend": "console"},
        )


def _serialize_channels(channels: Iterable[ChannelConfig]) -> list[dict[str, Any]]:
    return [channel.model_dump(mode="json") for channel in channels]


def _deserialize_channels(raw: Iterable[dict[str, Any]]) -> list[ChannelConfig]:
    return [ChannelConfig.model_validate(item) for item in raw]


def _preference_to_schema(preference: PreferenceModel) -> NotificationPreference:
    return NotificationPreference(
        id=preference.id,
        organization_id=preference.organization_id,
        subject_type=NotificationSubjectType(preference.subject_type),
        subject_id=preference.subject_id,
        triggers=list(preference.triggers or []),
        channels=_deserialize_channels(preference.channels or []),
        muted_until=preference.muted_until,
        created_at=preference.created_at,
        updated_at=preference.updated_at,
    )


def _delivery_to_schema(
    delivery: DeliveryModel,
    message: NotificationMessage,
) -> NotificationDelivery:
    return NotificationDelivery(
        id=delivery.id,
        message=message,
        sent_at=delivery.sent_at,
        status=delivery.status,
        failure_reason=delivery.failure_reason,
        retry_count=delivery.retry_count,
        last_attempt_at=delivery.last_attempt_at,
    )


class NotificationService:
    """Manage notification preferences and dispatch deliveries."""

    def __init__(
        self,
        session: AsyncSession,
        dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self.session = session
        self.dispatcher = dispatcher or ConsoleNotificationDispatcher()

    async def list_preferences(
        self,
        *,
        organization_id: UUID | None = None,
        subject_id: UUID | None = None,
        subject_type: NotificationSubjectType | None = None,
    ) -> list[NotificationPreference]:
        query: Select[tuple[PreferenceModel]] = select(PreferenceModel)
        conditions = []
        if organization_id:
            conditions.append(PreferenceModel.organization_id == organization_id)
        if subject_id:
            conditions.append(PreferenceModel.subject_id == subject_id)
        if subject_type:
            conditions.append(PreferenceModel.subject_type == subject_type.value)
        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(
            query.order_by(PreferenceModel.created_at.asc())
        )
        preferences = result.scalars().all()
        return [_preference_to_schema(pref) for pref in preferences]

    async def _load_preference(self, preference_id: UUID) -> PreferenceModel:
        preference = await self.session.get(PreferenceModel, preference_id)
        if not preference:
            raise NotFoundError("Notification preference not found")
        return preference

    async def upsert_preference(
        self,
        *,
        preference_id: UUID | None,
        organization_id: UUID,
        subject_type: NotificationSubjectType,
        subject_id: UUID,
        triggers: list[EventTrigger],
        channels: list[ChannelConfig],
        muted_until: datetime | None,
    ) -> NotificationPreference:
        if preference_id:
            preference = await self._load_preference(preference_id)
        else:
            query = select(PreferenceModel).where(
                and_(
                    PreferenceModel.organization_id == organization_id,
                    PreferenceModel.subject_type == subject_type.value,
                    PreferenceModel.subject_id == subject_id,
                )
            )
            result = await self.session.execute(query)
            preference = result.scalar_one_or_none()
            if not preference:
                preference = PreferenceModel(
                    organization_id=organization_id,
                    subject_type=subject_type.value,
                    subject_id=subject_id,
                )
                self.session.add(preference)

        preference.triggers = list(triggers)
        preference.channels = _serialize_channels(channels)
        preference.muted_until = muted_until

        await self.session.commit()
        await self.session.refresh(preference)
        return _preference_to_schema(preference)

    async def dispatch_notifications(
        self,
        *,
        trigger: EventTrigger,
        organization_id: UUID | None = None,
        recipient_subject_type: NotificationSubjectType | None = None,
        recipient_subject_ids: list[UUID] | None = None,
        subject: str | None = None,
        body_text: str | None = None,
        body_html: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[NotificationDelivery]:
        preferences = await self.list_preferences(
            organization_id=organization_id,
            subject_type=recipient_subject_type,
        )
        now = datetime.now(tz=UTC)
        deliveries: list[NotificationDelivery] = []
        requested_ids = set(recipient_subject_ids) if recipient_subject_ids else None

        for preference in preferences:
            if trigger not in preference.triggers:
                continue
            if preference.is_muted(now):
                continue
            if requested_ids and preference.subject_id not in requested_ids:
                continue

            for channel in preference.channels:
                if not channel.enabled:
                    continue
                message = NotificationMessage(
                    trigger=trigger,
                    recipient_subject_type=preference.subject_type,
                    recipient_subject_id=preference.subject_id,
                    channel=channel.channel,
                    address=channel.address,
                    subject=subject
                    or _default_subject_for_trigger(trigger),
                    body_text=body_text
                    or _default_body_for_trigger(trigger, context),
                    body_html=body_html,
                    metadata=context or {},
                    created_at=now,
                )
                delivery = DeliveryModel(
                    organization_id=preference.organization_id,
                    trigger=trigger,
                    recipient_subject_type=preference.subject_type,
                    recipient_subject_id=preference.subject_id,
                    channel=channel.channel,
                    address=channel.address,
                    subject=message.subject,
                    body_text=message.body_text,
                    body_html=message.body_html,
                    delivery_metadata={"context": context or {}},
                    status=NotificationStatus.QUEUED,
                )
                self.session.add(delivery)
                await self.session.flush()

                try:
                    dispatch_result = await self.dispatcher.send(message)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("Notification dispatch failed: %s", exc)
                    dispatch_result = DispatchResult(
                        status=NotificationStatus.FAILED,
                        failure_reason=str(exc),
                    )

                delivery.status = dispatch_result.status
                delivery.last_attempt_at = now
                if dispatch_result.status == NotificationStatus.SENT:
                    delivery.sent_at = now
                    delivery.retry_count = 0
                    delivery.failure_reason = None
                else:
                    delivery.retry_count += 1
                    delivery.failure_reason = dispatch_result.failure_reason

                metadata = dispatch_result.metadata or {}
                delivery.delivery_metadata = {
                    **(delivery.delivery_metadata or {}),
                    **metadata,
                }

                await self.session.flush()
                deliveries.append(_delivery_to_schema(delivery, message))

        await self.session.commit()
        return deliveries

    async def retry_failed_deliveries(self, *, max_attempts: int = 3) -> int:
        now = datetime.now(tz=UTC)
        stmt: Select[tuple[DeliveryModel]] = select(DeliveryModel).where(
            DeliveryModel.status == NotificationStatus.FAILED,
            DeliveryModel.retry_count < max_attempts,
        )
        deliveries = (await self.session.execute(stmt)).scalars().all()
        if not deliveries:
            return 0

        processed = 0
        for delivery in deliveries:
            message = NotificationMessage(
                trigger=delivery.trigger,
                recipient_subject_type=NotificationSubjectType(delivery.recipient_subject_type),
                recipient_subject_id=delivery.recipient_subject_id,
                channel=NotificationChannel(delivery.channel),
                address=delivery.address,
                subject=delivery.subject,
                body_text=delivery.body_text,
                body_html=delivery.body_html,
                metadata=delivery.delivery_metadata or {},
                created_at=delivery.created_at,
            )
            try:
                result = await self.dispatcher.send(message)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Notification retry failed: %s", exc)
                result = DispatchResult(
                    status=NotificationStatus.FAILED,
                    failure_reason=str(exc),
                )

            delivery.last_attempt_at = now
            if result.status == NotificationStatus.SENT:
                delivery.status = NotificationStatus.SENT
                delivery.sent_at = now
                delivery.retry_count = 0
                delivery.failure_reason = None
            else:
                delivery.retry_count += 1
                if result.failure_reason:
                    delivery.failure_reason = result.failure_reason
            if result.metadata:
                delivery.delivery_metadata = {
                    **(delivery.delivery_metadata or {}),
                    **result.metadata,
                }
            processed += 1

        await self.session.commit()
        return processed


def _default_subject_for_trigger(trigger: EventTrigger) -> str:
    mapping = {
        "registration_confirmed": "Registration Confirmed",
        "round_pairings": "New Round Pairings Available",
        "round_locked": "Round Results Locked",
        "standings_published": "Standings Updated",
        "season_leaderboard": "Season Leaderboard Update",
    }
    return mapping.get(trigger, f"Notification: {trigger.replace('_', ' ').title()}")


def _default_body_for_trigger(
    trigger: EventTrigger,
    context: dict[str, Any] | None,
) -> str:
    base = _default_subject_for_trigger(trigger)
    if not context:
        return base
    return f"{base}\n\nContext:\n{json.dumps(context, indent=2, default=str)}"


__all__ = [
    "ConsoleNotificationDispatcher",
    "DispatchResult",
    "NotificationDispatcher",
    "NotificationService",
]
