"""add admin features - agent interactions and audit log

Revision ID: h4i5j6k7l8m9
Revises: g3h4i5j6k7l8
Create Date: 2025-07-28 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'h4i5j6k7l8m9'
down_revision = 'g3h4i5j6k7l8'
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_interactions table
    op.create_table(
        'agent_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('interaction_type', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_interactions_id'), 'agent_interactions', ['id'], unique=False)
    
    # Create admin_audit_log table
    op.create_table(
        'admin_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_login', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_audit_log_id'), 'admin_audit_log', ['id'], unique=False)


def downgrade():
    # Drop admin_audit_log table
    op.drop_index(op.f('ix_admin_audit_log_id'), table_name='admin_audit_log')
    op.drop_table('admin_audit_log')
    
    # Drop agent_interactions table
    op.drop_index(op.f('ix_agent_interactions_id'), table_name='agent_interactions')
    op.drop_table('agent_interactions')
