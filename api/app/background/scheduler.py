from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:  # pragma: no cover - scheduler optional in some contexts
    AsyncIOScheduler = None  # type: ignore
    CronTrigger = None  # type: ignore

from sqlalchemy import select

from api.app.agents.maintenance_agent import MaintenanceAgent
from api.app.agents.season_agent import SeasonAgent
from api.app.core.database import async_session_factory
from api.app.models.structure import Season
from api.app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def session_scope():
    async with async_session_factory() as session:
        yield session


async def run_cleanup_job() -> None:
    async with session_scope() as session:
        agent = MaintenanceAgent(session)
        summary = await agent.run_cleanup()
        logger.info("Maintenance cleanup run: %s", summary.summary)


async def run_season_recompute(season_id: str) -> None:
    async with session_scope() as session:
        agent = SeasonAgent(session)
        result = await agent.recompute(UUID(season_id))
        logger.info("Season %s recomputed at %s", season_id, datetime.now())


async def run_failed_notification_retry() -> None:
    async with session_scope() as session:
        service = NotificationService(session)
        processed = await service.retry_failed_deliveries()
        if processed:
            logger.info("Retried %s failed notifications", processed)


async def run_current_season_recompute() -> None:
    async with session_scope() as session:
        result = await session.execute(
            select(Season.id).where(Season.is_current.is_(True))
        )
        season_id = result.scalar_one_or_none()
        if not season_id:
            logger.info("No active season to recompute")
            return
        agent = SeasonAgent(session)
        await agent.recompute(season_id)
        logger.info("Nightly season recompute complete for %s", season_id)


def start_scheduler() -> AsyncIOScheduler:
    if AsyncIOScheduler is None or CronTrigger is None:
        logger.warning("APScheduler not installed; background jobs disabled")
        return None  # type: ignore

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_cleanup_job, CronTrigger.from_crontab("0 3 * * *"), id="cleanup-nightly")
    scheduler.add_job(
        run_failed_notification_retry,
        CronTrigger.from_crontab("*/5 * * * *"),
        id="notifications-retry",
    )
    scheduler.add_job(
        run_current_season_recompute,
        CronTrigger.from_crontab("15 2 * * *"),
        id="season-recompute-nightly",
    )
    return scheduler


__all__ = [
    "run_cleanup_job",
    "run_current_season_recompute",
    "run_failed_notification_retry",
    "run_season_recompute",
    "start_scheduler",
]
