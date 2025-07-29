"""rename_metadata_to_interaction_metadata

Revision ID: 1339e4e8824c
Revises: h4i5j6k7l8m9
Create Date: 2025-07-28 21:06:04.692975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1339e4e8824c'
down_revision: Union[str, Sequence[str], None] = 'h4i5j6k7l8m9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename metadata column to interaction_metadata in agent_interactions table
    op.alter_column('agent_interactions', 'metadata', new_column_name='interaction_metadata')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename interaction_metadata column back to metadata in agent_interactions table
    op.alter_column('agent_interactions', 'interaction_metadata', new_column_name='metadata')
