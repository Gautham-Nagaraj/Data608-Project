"""
add stock_prices table and stock_sectors view

Revision ID: 0002_add_stock_prices_and_sectors_view
Revises: 0001_initial_schema
Create Date: 2025-07-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_stock_prices_sectors'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create stock_prices table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            symbol VARCHAR NOT NULL,
            date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            price FLOAT NOT NULL,
            PRIMARY KEY (symbol, date),
            FOREIGN KEY(symbol) REFERENCES stocks (symbol)
        )
    """)
    
    # Create stock_sectors view
    op.execute("CREATE VIEW stock_sectors AS SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL;")


def downgrade():
    # Drop stock_sectors view
    op.execute("DROP VIEW IF EXISTS stock_sectors;")
    
    # Drop stock_prices table
    op.execute("DROP TABLE IF EXISTS stock_prices;")
