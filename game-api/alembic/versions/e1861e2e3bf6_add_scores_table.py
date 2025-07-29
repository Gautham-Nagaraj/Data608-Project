"""add scores table

Revision ID: e1861e2e3bf6
Revises: 505801369983
Create Date: 2025-07-27 17:31:26.518497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e1861e2e3bf6'
down_revision: Union[str, Sequence[str], None] = '505801369983'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create scores table
    op.create_table('scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scores_id'), 'scores', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop scores table
    op.drop_index(op.f('ix_scores_id'), table_name='scores')
    op.drop_table('scores')
