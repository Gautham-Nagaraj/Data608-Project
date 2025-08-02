import pytest

# Minimal conftest.py for basic async testing
# This avoids importing the full app which has missing dependencies

@pytest.fixture
def sample_data():
    """Sample data for basic testing"""
    return {"test": "data"}
