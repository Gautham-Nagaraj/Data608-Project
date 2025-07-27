#!/usr/bin/env python3
import os
from app.core.db import get_db
from app import crud
from sqlalchemy import text

# Set the database URL
os.environ['DATABASE_URL'] = 'postgresql+psycopg://stockroulette_user:ChangeMe123!@localhost:5432/stockroulette'

# Get database session
db = next(get_db())

# Insert test data with sectors
test_data_sql = """
INSERT INTO stocks (symbol, company_name, sector, category) VALUES 
('TEST1', 'Test Company 1', 'Technology', 'popular'),
('TEST2', 'Test Company 2', 'Healthcare', 'volatile'),
('TEST3', 'Test Company 3', 'Technology', 'sector'),
('TEST4', 'Test Company 4', 'Finance', 'sector')
ON CONFLICT (symbol) DO UPDATE SET 
    sector = EXCLUDED.sector,
    company_name = EXCLUDED.company_name,
    category = EXCLUDED.category
"""

print("Inserting test data...")
db.execute(text(test_data_sql))
db.commit()

# Test the get_stock_sectors function
print("\nTesting get_stock_sectors function:")
sectors = crud.get_stock_sectors(db)
print(f"Found {len(sectors)} sectors:")
for sector in sectors:
    print(f"  - {sector}")

# Close the database session
db.close()
