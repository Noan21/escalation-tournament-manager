from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core.database import get_db_session
from api.app.services.maintenance import MaintenanceService
from api.app.services.notifications import NotificationService
from api.app.services.pairings import PairingService
from api.app.services.registrations import RegistrationService
from api.app.services.scoring import ScoringService
from api.app.services.season import SeasonService
from api.app.services.standings import StandingsService


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_registration_service(session: DbSessionDep) -> RegistrationService:
    return RegistrationService(session)


def get_pairing_service(session: DbSessionDep) -> PairingService:
    return PairingService(session)


def get_scoring_service(session: DbSessionDep) -> ScoringService:
    return ScoringService(session)


def get_standings_service(session: DbSessionDep) -> StandingsService:
    return StandingsService(session)


def get_season_service(session: DbSessionDep) -> SeasonService:
    return SeasonService(session)


def get_notification_service(session: DbSessionDep) -> NotificationService:
    return NotificationService(session)


def get_maintenance_service(session: DbSessionDep) -> MaintenanceService:
    return MaintenanceService(session)


__all__ = [
    "get_maintenance_service",
    "get_notification_service",
    "get_pairing_service",
    "get_registration_service",
    "get_scoring_service",
    "get_season_service",
    "get_standings_service",
]
