"""add player_id total_trades total_profit to scores

Revision ID: f2a3b4c5d6e7
Revises: e1861e2e3bf6
Create Date: 2025-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'e1861e2e3bf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to scores table
    op.add_column('scores', sa.Column('player_id', sa.Integer(), nullable=True))
    op.add_column('scores', sa.Column('total_trades', sa.Integer(), nullable=True))
    op.add_column('scores', sa.Column('total_profit', sa.Float(), nullable=True))
    
    # Create foreign key constraint for player_id
    op.create_foreign_key('fk_scores_player_id', 'scores', 'players', ['player_id'], ['id'])
    
    # Update existing records with player_id from sessions table
    op.execute("""
        UPDATE scores 
        SET player_id = sessions.player_id 
        FROM sessions 
        WHERE scores.session_id = sessions.session_id
    """)
    
    # Set default values for existing records
    op.execute("UPDATE scores SET total_trades = 0 WHERE total_trades IS NULL")
    op.execute("UPDATE scores SET total_profit = 0.0 WHERE total_profit IS NULL")
    
    # Make columns non-nullable after setting default values
    op.alter_column('scores', 'player_id', nullable=False)
    op.alter_column('scores', 'total_trades', nullable=False)
    op.alter_column('scores', 'total_profit', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint and columns
    op.drop_constraint('fk_scores_player_id', 'scores', type_='foreignkey')
    op.drop_column('scores', 'total_profit')
    op.drop_column('scores', 'total_trades')
    op.drop_column('scores', 'player_id')
