from fastapi import FastAPI

from app.api.routes import api_router
from app.core.plugins import builtin  # noqa: F401  Ensure default strategies registered

app = FastAPI(
    title="Escalation Tournament Platform API",
    version="0.1.0",
    description=(
        "Async FastAPI service powering the Escalation tournament platform. "
        "Formats, scoring profiles, and workflows are all pluggable."
    ),
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Simple health probe for orchestration."""
    return {"status": "ok"}
