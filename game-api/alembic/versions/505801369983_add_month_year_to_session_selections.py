"""add_month_year_to_session_selections

Revision ID: 505801369983
Revises: 6737ca3a3851
Create Date: 2025-07-27 13:42:09.652583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '505801369983'
down_revision: Union[str, Sequence[str], None] = '6737ca3a3851'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add month and year columns to session_selections table
    op.add_column('session_selections', sa.Column('month', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('session_selections', sa.Column('year', sa.Integer(), nullable=False, server_default='2025'))
    
    # Remove the server_default after adding the columns
    op.alter_column('session_selections', 'month', server_default=None)
    op.alter_column('session_selections', 'year', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove month and year columns from session_selections table
    op.drop_column('session_selections', 'year')
    op.drop_column('session_selections', 'month')
