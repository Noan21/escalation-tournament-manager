from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(title="Escalation Tournament Manager API")


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Placeholder dependency until the real session wiring is implemented."""
    raise RuntimeError("Database session dependency has not been configured.")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/db-check", dependencies=[Depends(get_db_session)], tags=["debug"])
async def debug_db_check() -> dict[str, bool]:
    """Endpoint used by tests once dependency overrides are in place."""
    return {"database": True}


__all__ = ["app", "get_db_session"]

