"""Pydantic schema package for FastAPI endpoints and service layer contracts."""

from . import (
    auth,
    events,
    formats,
    maintenance,
    notifications,
    players,
    rounds,
    orchestrator,
    season,
    standings,
    structure,
)

__all__ = [
    "auth",
    "events",
    "formats",
    "maintenance",
    "notifications",
    "players",
    "rounds",
    "orchestrator",
    "season",
    "standings",
    "structure",
]
