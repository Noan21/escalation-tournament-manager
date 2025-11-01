from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.agents.notification_agent import NotificationAgent
from api.app.core.database import get_db_session
from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_notification_service
from api.app.models.enums import NotificationSubjectType
from api.app.schemas.notifications import (
    NotificationDelivery,
    NotificationDispatchRequest,
    NotificationPreference,
    NotificationPreferenceUpsert,
)
from api.app.services.notifications import NotificationService


router = APIRouter(prefix="/api/notifications", tags=["notifications"])

DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/preferences", response_model=list[NotificationPreference])
async def list_preferences(
    organization_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    subject_type: NotificationSubjectType | None = Query(default=None),
    service: NotificationService = Depends(get_notification_service),
    current_user=Depends(require_roles("admin")),
) -> list[NotificationPreference]:
    return await service.list_preferences(
        organization_id=organization_id,
        subject_id=subject_id,
        subject_type=subject_type,
    )


@router.post("/preferences", response_model=NotificationPreference)
async def upsert_preference(
    payload: NotificationPreferenceUpsert,
    service: NotificationService = Depends(get_notification_service),
    current_user=Depends(require_roles("admin")),
) -> NotificationPreference:
    return await service.upsert_preference(
        preference_id=payload.id,
        organization_id=payload.organization_id,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        triggers=payload.triggers,
        channels=payload.channels,
        muted_until=payload.muted_until,
    )


@router.post("/dispatch", response_model=list[NotificationDelivery])
async def dispatch_notifications(
    payload: NotificationDispatchRequest,
    session: DbSessionDep,
    current_user=Depends(require_roles("admin")),
) -> list[NotificationDelivery]:
    agent = NotificationAgent(session)
    return await agent.notify(
        payload.trigger,
        stage_id=payload.stage_id,
        round_id=payload.round_id,
        season_id=payload.season_id,
        organization_id=payload.organization_id,
        recipient_subject_type=payload.recipient_subject_type,
        recipient_subject_ids=payload.recipient_subject_ids,
        subject=payload.subject,
        body_text=payload.body_text,
        body_html=payload.body_html,
        context=payload.context,
    )


__all__ = ["router"]
