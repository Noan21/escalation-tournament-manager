from __future__ import annotations

from fastapi import Depends, FastAPI

from .api import auth as auth_router
from .core.database import get_db_session, shutdown_database

app = FastAPI(title="Escalation Tournament Manager API")
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/db-check", dependencies=[Depends(get_db_session)], tags=["debug"])
async def debug_db_check() -> dict[str, bool]:
    """Endpoint used by tests once dependency overrides are in place."""
    return {"database": True}


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await shutdown_database()


__all__ = ["app", "get_db_session"]

