"""add_current_date_to_session_selections

Revision ID: 3aa44cd1c307
Revises: 1339e4e8824c
Create Date: 2025-07-28 23:41:43.630274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3aa44cd1c307'
down_revision: Union[str, Sequence[str], None] = '1339e4e8824c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add current_date column to session_selections table
    op.add_column('session_selections', sa.Column('current_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove current_date column from session_selections table
    op.drop_column('session_selections', 'current_date')
