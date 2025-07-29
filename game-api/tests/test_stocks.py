import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.models import Stock, StockPrice


class TestStocksRouter:
    """Test cases for stocks router endpoints."""

    def test_get_stock_sectors_empty(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/sectors returns empty list when no stocks with sectors exist."""
        response = client.get("/api/stocks/sectors")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_stock_sectors_with_data(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/sectors returns unique sectors."""
        # Create test stocks with sectors
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular"),
            Stock(symbol="MSFT", company_name="Microsoft Corp.", sector="Technology", category="popular"),
            Stock(symbol="JNJ", company_name="Johnson & Johnson", sector="Healthcare", category="sector"),
            Stock(symbol="JPM", company_name="JPMorgan Chase", sector="Finance", category="sector"),
            Stock(symbol="TSLA", company_name="Tesla Inc.", sector="Technology", category="volatile"),
            Stock(symbol="AMC", company_name="AMC Entertainment", sector=None, category="volatile"),  # No sector
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/sectors")
        assert response.status_code == 200
        sectors = response.json()
        
        # Should return sorted unique sectors, excluding None values
        expected_sectors = ["Finance", "Healthcare", "Technology"]
        assert sectors == expected_sectors

    def test_create_stock_success(self, client: TestClient, db_session: Session):
        """Test POST /api/stocks creates a new stock."""
        stock_data = {
            "symbol": "NVDA",
            "company_name": "NVIDIA Corporation",
            "sector": "Technology",
            "category": "popular"
        }
        
        response = client.post("/api/stocks/", json=stock_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "NVDA"
        assert data["company_name"] == "NVIDIA Corporation"
        assert data["sector"] == "Technology"
        assert data["category"] == "popular"

    def test_create_stock_duplicate(self, client: TestClient, db_session: Session):
        """Test POST /api/stocks fails when stock symbol already exists."""
        # Create initial stock
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular")
        db_session.add(stock)
        db_session.commit()

        # Try to create duplicate
        stock_data = {
            "symbol": "AAPL",
            "company_name": "Apple Inc. Duplicate",
            "sector": "Technology",
            "category": "popular"
        }
        
        response = client.post("/api/stocks/", json=stock_data)
        assert response.status_code == 400
        assert "Stock symbol already exists" in response.json()["detail"]

    def test_list_stocks_no_filters(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks returns all stocks without filters."""
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular"),
            Stock(symbol="TSLA", company_name="Tesla Inc.", sector="Technology", category="volatile"),
            Stock(symbol="JNJ", company_name="Johnson & Johnson", sector="Healthcare", category="sector"),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert {stock["symbol"] for stock in data} == {"AAPL", "TSLA", "JNJ"}

    def test_list_stocks_with_category_filter(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks with category filter."""
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular"),
            Stock(symbol="TSLA", company_name="Tesla Inc.", sector="Technology", category="volatile"),
            Stock(symbol="JNJ", company_name="Johnson & Johnson", sector="Healthcare", category="sector"),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/?category=popular")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["category"] == "popular"

    def test_list_stocks_with_sector_filter(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks with sector filter."""
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular"),
            Stock(symbol="MSFT", company_name="Microsoft Corp.", sector="Technology", category="popular"),
            Stock(symbol="JNJ", company_name="Johnson & Johnson", sector="Healthcare", category="sector"),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/?sector=Technology")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert {stock["symbol"] for stock in data} == {"AAPL", "MSFT"}

    def test_list_stocks_with_pagination(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks with pagination."""
        stocks = [
            Stock(symbol=f"STOCK{i}", company_name=f"Company {i}", sector="Technology", category="popular")
            for i in range(1, 6)  # Create 5 stocks
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        # Test limit
        response = client.get("/api/stocks/?limit=3")
        assert response.status_code == 200
        assert len(response.json()) == 3

        # Test offset
        response = client.get("/api/stocks/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_stock_by_symbol_success(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/{symbol} returns specific stock."""
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular")
        db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/AAPL")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["company_name"] == "Apple Inc."
        assert data["sector"] == "Technology"

    def test_get_stock_by_symbol_not_found(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/{symbol} returns 404 for non-existent stock."""
        response = client.get("/api/stocks/NONEXISTENT")
        assert response.status_code == 404
        assert "Stock not found" in response.json()["detail"]

    def test_create_stocks_bulk_success(self, client: TestClient, db_session: Session):
        """Test POST /api/stocks/bulk creates multiple stocks."""
        stocks_data = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "category": "popular"
            },
            {
                "symbol": "MSFT",
                "company_name": "Microsoft Corp.",
                "sector": "Technology",
                "category": "popular"
            }
        ]
        
        response = client.post("/api/stocks/bulk", json=stocks_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert {stock["symbol"] for stock in data} == {"AAPL", "MSFT"}

    def test_create_stocks_bulk_with_duplicates(self, client: TestClient, db_session: Session):
        """Test POST /api/stocks/bulk handles existing stocks."""
        # Create existing stock
        existing_stock = Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular")
        db_session.add(existing_stock)
        db_session.commit()

        stocks_data = [
            {
                "symbol": "AAPL",  # This already exists
                "company_name": "Apple Inc. Updated",
                "sector": "Technology",
                "category": "popular"
            },
            {
                "symbol": "MSFT",  # This is new
                "company_name": "Microsoft Corp.",
                "sector": "Technology",
                "category": "popular"
            }
        ]
        
        response = client.post("/api/stocks/bulk", json=stocks_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Should return existing stock for AAPL and new stock for MSFT
        symbols = {stock["symbol"] for stock in data}
        assert symbols == {"AAPL", "MSFT"}

    def test_get_eligible_dates(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/eligible_dates returns available trading dates."""
        # Create stocks with different available_from dates
        stocks = [
            Stock(
                symbol="STOCK1", 
                company_name="Company 1", 
                sector="Technology", 
                category="popular",
                available_from=date(2024, 1, 1)
            ),
            Stock(
                symbol="STOCK2", 
                company_name="Company 2", 
                sector="Healthcare", 
                category="volatile",
                available_from=date(2024, 6, 1)
            ),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/eligible_dates")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Each item should be a tuple/list of [month, year]
        for date_tuple in data:
            assert len(date_tuple) == 2
            assert isinstance(date_tuple[0], int)  # month
            assert isinstance(date_tuple[1], int)  # year

    def test_get_stock_prices(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/prices/{symbol} returns stock prices."""
        # Create stock and stock prices
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", sector="Technology", category="popular")
        db_session.add(stock)
        db_session.commit()

        prices = [
            StockPrice(symbol="AAPL", date=datetime(2019, 1, 1), price=150.0),
            StockPrice(symbol="AAPL", date=datetime(2019, 1, 2), price=152.0),
            StockPrice(symbol="AAPL", date=datetime(2019, 1, 3), price=148.0),
        ]
        for price in prices:
            db_session.add(price)
        db_session.commit()

        response = client.get("/api/stocks/prices/AAPL?start_date=2019-01-01&end_date=2019-01-03")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert all(price_data["symbol"] == "AAPL" for price_data in data)
        assert all(isinstance(price_data["price"], (int, float)) for price_data in data)

    def test_route_priority_sectors_vs_symbol(self, client: TestClient, db_session: Session):
        """Test that /sectors route has priority over /{symbol} route."""
        # Create a stock with symbol "sectors" to test route conflict resolution
        stock = Stock(symbol="sectors", company_name="Sectors Company", sector="Technology", category="popular")
        db_session.add(stock)
        db_session.commit()

        # Test that /sectors endpoint returns sectors, not the stock
        response = client.get("/api/stocks/sectors")
        assert response.status_code == 200
        
        # Should return list of sectors, not stock details
        data = response.json()
        assert isinstance(data, list)
        # If there are sectors, they should be strings
        if data:
            assert all(isinstance(sector, str) for sector in data)

        # Test that we can still access the stock with symbol "sectors" via a different approach
        # This would require a different endpoint or parameter to avoid route conflict

    def test_get_eligible_dates_roulette_no_stocks(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/eligible_dates/roulette returns null when no stocks exist."""
        response = client.get("/api/stocks/eligible_dates/roulette")
        assert response.status_code == 200
        assert response.json() is None

    def test_get_eligible_dates_roulette_insufficient_categories(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/eligible_dates/roulette returns null when not all categories are available."""
        # Create stocks but only from 2 categories (missing 'sector' category)
        stocks = [
            Stock(
                symbol="POPULAR1", 
                company_name="Popular Company 1", 
                sector="Technology", 
                category="popular",
                available_from=date(2024, 1, 1)
            ),
            Stock(
                symbol="VOLATILE1", 
                company_name="Volatile Company 1", 
                sector="Technology", 
                category="volatile",
                available_from=date(2024, 1, 1)
            ),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/eligible_dates/roulette")
        assert response.status_code == 200
        assert response.json() is None

    def test_get_eligible_dates_roulette_valid_selection(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/eligible_dates/roulette returns a valid date when all categories are available."""
        # Create stocks from all three categories available in the same month
        stocks = [
            Stock(
                symbol="POPULAR1", 
                company_name="Popular Company 1", 
                sector="Technology", 
                category="popular",
                available_from=date(2024, 1, 1)
            ),
            Stock(
                symbol="VOLATILE1", 
                company_name="Volatile Company 1", 
                sector="Finance", 
                category="volatile",
                available_from=date(2024, 1, 1)
            ),
            Stock(
                symbol="SECTOR1", 
                company_name="Sector Company 1", 
                sector="Healthcare", 
                category="sector",
                available_from=date(2024, 1, 1)
            ),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/eligible_dates/roulette")
        assert response.status_code == 200
        
        data = response.json()
        assert data is not None
        assert isinstance(data, dict)
        assert "month" in data
        assert "year" in data
        assert isinstance(data["month"], int)  # month
        assert isinstance(data["year"], int)  # year
        assert 1 <= data["month"] <= 12  # Valid month
        assert data["year"] > 0  # Valid year

    def test_get_eligible_dates_roulette_multiple_dates_returns_one(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/eligible_dates/roulette returns exactly one date even when multiple valid dates exist."""
        # Create stocks from all three categories available in different months
        stocks = [
            # January 2024 stocks
            Stock(
                symbol="POPULAR1", 
                company_name="Popular Company 1", 
                sector="Technology", 
                category="popular",
                available_from=date(2024, 1, 1)
            ),
            Stock(
                symbol="VOLATILE1", 
                company_name="Volatile Company 1", 
                sector="Finance", 
                category="volatile",
                available_from=date(2024, 1, 1)
            ),
            Stock(
                symbol="SECTOR1", 
                company_name="Sector Company 1", 
                sector="Healthcare", 
                category="sector",
                available_from=date(2024, 1, 1)
            ),
            # March 2024 stocks
            Stock(
                symbol="POPULAR2", 
                company_name="Popular Company 2", 
                sector="Technology", 
                category="popular",
                available_from=date(2024, 3, 1)
            ),
            Stock(
                symbol="VOLATILE2", 
                company_name="Volatile Company 2", 
                sector="Finance", 
                category="volatile",
                available_from=date(2024, 3, 1)
            ),
            Stock(
                symbol="SECTOR2", 
                company_name="Sector Company 2", 
                sector="Healthcare", 
                category="sector",
                available_from=date(2024, 3, 1)
            ),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/eligible_dates/roulette")
        assert response.status_code == 200
        
        data = response.json()
        assert data is not None
        assert isinstance(data, dict)
        assert "month" in data
        assert "year" in data
        assert isinstance(data["month"], int)  # month
        assert isinstance(data["year"], int)  # year
        # Should be one of the valid dates (January or March 2024)
        assert (data["month"], data["year"]) in [(1, 2024), (3, 2024)]

    def test_get_eligible_dates_roulette_respects_availability_periods(self, client: TestClient, db_session: Session):
        """Test GET /api/stocks/eligible_dates/roulette respects available_to dates."""
        # Create stocks where some expire before others become available
        stocks = [
            # Available only in January 2024
            Stock(
                symbol="POPULAR1", 
                company_name="Popular Company 1", 
                sector="Technology", 
                category="popular",
                available_from=date(2024, 1, 1),
                available_to=date(2024, 1, 31)
            ),
            Stock(
                symbol="VOLATILE1", 
                company_name="Volatile Company 1", 
                sector="Finance", 
                category="volatile",
                available_from=date(2024, 1, 1),
                available_to=date(2024, 1, 31)
            ),
            Stock(
                symbol="SECTOR1", 
                company_name="Sector Company 1", 
                sector="Healthcare", 
                category="sector",
                available_from=date(2024, 1, 1),
                available_to=date(2024, 1, 31)
            ),
            # Available from March 2024 onwards (no end date)
            Stock(
                symbol="POPULAR2", 
                company_name="Popular Company 2", 
                sector="Technology", 
                category="popular",
                available_from=date(2024, 3, 1)
            ),
            Stock(
                symbol="VOLATILE2", 
                company_name="Volatile Company 2", 
                sector="Finance", 
                category="volatile",
                available_from=date(2024, 3, 1)
            ),
            Stock(
                symbol="SECTOR2", 
                company_name="Sector Company 2", 
                sector="Healthcare", 
                category="sector",
                available_from=date(2024, 3, 1)
            ),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/stocks/eligible_dates/roulette")
        assert response.status_code == 200
        
        data = response.json()
        assert data is not None
        assert isinstance(data, dict)
        assert "month" in data
        assert "year" in data
        # Should be either January 2024 or March 2024 (or later)
        # February 2024 should not be valid since some stocks expired and others haven't started
        assert (data["month"], data["year"]) in [(1, 2024)] or (data["year"] == 2024 and data["month"] >= 3) or data["year"] > 2024
