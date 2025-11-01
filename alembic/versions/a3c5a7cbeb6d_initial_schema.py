"""Initial schema

Revision ID: a3c5a7cbeb6d
Revises: 
Create Date: 2025-11-01 01:37:11.119279

"""
from collections.abc import Sequence

from alembic import op
from api.app.models import Base

# revision identifiers, used by Alembic.
revision: str = 'a3c5a7cbeb6d'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables defined in the SQLAlchemy metadata."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop all tables for a clean rollback."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
