"""add unsold shares table

Revision ID: g3h4i5j6k7l8
Revises: f2a3b4c5d6e7
Create Date: 2025-07-28 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'g3h4i5j6k7l8'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None


def upgrade():
    # Create unsold_shares table
    op.create_table(
        'unsold_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('purchase_price', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], ),
        sa.ForeignKeyConstraint(['symbol'], ['stocks.symbol'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unsold_shares_id'), 'unsold_shares', ['id'], unique=False)


def downgrade():
    # Drop unsold_shares table
    op.drop_index(op.f('ix_unsold_shares_id'), table_name='unsold_shares')
    op.drop_table('unsold_shares')
