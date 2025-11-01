"""Initial schema - existing database state

Revision ID: dad4e4a50d02
Revises: 
Create Date: 2025-10-16 23:32:01.813862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dad4e4a50d02'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - initial migration captures existing database state.

    This is a no-op migration that records the existing schema.
    The database was created before migrations were introduced.

    Note: FTS5 tables (events_fts*) are managed by SQLite triggers,
    not by SQLAlchemy models, so they're excluded from migrations.
    """
    # No operations needed - database already exists with correct schema
    pass


def downgrade() -> None:
    """Downgrade schema - not supported for initial migration.

    Since this is the initial migration capturing an existing database,
    there is no previous state to downgrade to.
    """
    # Cannot downgrade from initial state
    raise NotImplementedError(
        "Cannot downgrade from initial migration. "
        "To reset database, delete unified_research.db and restart server."
    )
