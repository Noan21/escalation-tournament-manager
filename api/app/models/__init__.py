"""
SQLAlchemy models package. Importing this module exposes the Base metadata
and ensures all model definitions are registered for Alembic autogenerate.
"""

from . import (
    auth,
    events,
    maintenance,
    notifications,
    participants,
    standings,
    structure,
)
from .base import Base

__all__ = [
    "Base",
    "auth",
    "events",
    "maintenance",
    "notifications",
    "participants",
    "standings",
    "structure",
]

