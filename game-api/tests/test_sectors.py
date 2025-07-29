#!/usr/bin/env python3
import pytest
from app import crud
from sqlalchemy import text


def test_get_stock_sectors(db_session):
    """Test the get_stock_sectors function with test data."""
    # Insert test data with sectors
    test_data_sql = """
    INSERT INTO stocks (symbol, company_name, sector, category) VALUES 
    ('TEST1', 'Test Company 1', 'Technology', 'popular'),
    ('TEST2', 'Test Company 2', 'Healthcare', 'volatile'),
    ('TEST3', 'Test Company 3', 'Technology', 'sector'),
    ('TEST4', 'Test Company 4', 'Finance', 'sector')
    """
    
    db_session.execute(text(test_data_sql))
    db_session.commit()
    
    # Test the get_stock_sectors function
    sectors = crud.get_stock_sectors(db_session)
    
    # Assertions
    assert len(sectors) == 3  # Should have 3 unique sectors: Technology, Healthcare, Finance
    assert 'Technology' in sectors
    assert 'Healthcare' in sectors
    assert 'Finance' in sectors
    
    print(f"Found {len(sectors)} sectors:")
    for sector in sectors:
        print(f"  - {sector}")
