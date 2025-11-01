from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    auth as auth_router,
    maintenance as maintenance_router,
    notifications as notifications_router,
    orchestrator as orchestrator_router,
    pairings as pairings_router,
    registrations as registrations_router,
    scoring as scoring_router,
    seasons as seasons_router,
    standings as standings_router,
)
from .background.scheduler import start_scheduler
from .core.config import settings
from .core.database import get_db_session, shutdown_database

app = FastAPI(title="Escalation Tournament Manager API")

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

scheduler = None
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(notifications_router.router)
app.include_router(registrations_router.router)
app.include_router(pairings_router.router)
app.include_router(scoring_router.router)
app.include_router(standings_router.router)
app.include_router(seasons_router.router)
app.include_router(orchestrator_router.router)
app.include_router(maintenance_router.router)

@app.on_event("startup")
async def on_startup() -> None:
    global scheduler
    scheduler = start_scheduler()
    if scheduler:
        scheduler.start()


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/db-check", dependencies=[Depends(get_db_session)], tags=["debug"])
async def debug_db_check() -> dict[str, bool]:
    """Endpoint used by tests once dependency overrides are in place."""
    return {"database": True}


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if scheduler:
        scheduler.shutdown(wait=False)
    await shutdown_database()


__all__ = ["app", "get_db_session"]
