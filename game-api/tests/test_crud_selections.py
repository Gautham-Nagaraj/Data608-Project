import uuid
from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models import Stock, SessionSelection, Player, Session as SessionModel


class TestSelectionsCRUD:
    """Test cases for selections CRUD operations."""

    def test_get_selection_success(self, db_session: Session):
        """Test get_selection returns selection for existing session."""
        # Create test player and session
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)

        session_id = uuid.uuid4()
        session = SessionModel(
            session_id=session_id,
            player_id=player.id,
            started_at=date.today(),
            status="active",
            balance=10000.0,
            unsold_stocks=[]
        )
        db_session.add(session)

        # Create selection
        selection = SessionSelection(
            session_id=session_id,
            popular_symbol="AAPL",
            volatile_symbol="TSLA",
            sector_symbol="MSFT"
        )
        db_session.add(selection)
        db_session.commit()

        # Test get_selection
        result = crud.get_selection(db_session, session_id)
        assert result is not None
        assert result.session_id == session_id
        assert result.popular_symbol == "AAPL"
        assert result.volatile_symbol == "TSLA"
        assert result.sector_symbol == "MSFT"

    def test_get_selection_not_found(self, db_session: Session):
        """Test get_selection returns None for non-existent session."""
        non_existent_session = uuid.uuid4()
        result = crud.get_selection(db_session, non_existent_session)
        assert result is None

    def test_get_roulette_selection_success(self, db_session: Session):
        """Test get_roulette_selection returns valid selection."""
        # Create test stocks available for July 2025
        stocks = [
            Stock(
                symbol="AAPL", 
                company_name="Apple Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 6, 1),
                available_to=date(2025, 8, 31)
            ),
            Stock(
                symbol="GOOGL", 
                company_name="Alphabet Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 1, 1),
                available_to=None
            ),
            Stock(
                symbol="TSLA", 
                company_name="Tesla Inc.", 
                category="volatile",
                sector="Automotive",
                available_from=date(2025, 7, 1),
                available_to=date(2025, 12, 31)
            ),
            Stock(
                symbol="GME", 
                company_name="GameStop Corp.", 
                category="volatile",
                sector="Retail",
                available_from=date(2025, 5, 1),
                available_to=date(2025, 9, 30)
            ),
            Stock(
                symbol="MSFT", 
                company_name="Microsoft Corp.", 
                category="sector",
                sector="Technology",
                available_from=date(2025, 1, 1),
                available_to=None
            ),
            Stock(
                symbol="JNJ", 
                company_name="Johnson & Johnson", 
                category="sector",
                sector="Healthcare",
                available_from=date(2025, 6, 15),
                available_to=date(2025, 8, 15)
            )
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        # Test get_roulette_selection
        result = crud.get_roulette_selection(db_session, 7, 2025)
        assert result is not None
        assert hasattr(result, 'popular_symbol')
        assert hasattr(result, 'volatile_symbol')
        assert hasattr(result, 'sector_symbol')
        assert result.popular_symbol in ["AAPL", "GOOGL"]
        assert result.volatile_symbol in ["TSLA", "GME"]
        assert result.sector_symbol in ["MSFT", "JNJ"]

    def test_get_roulette_selection_no_stocks(self, db_session: Session):
        """Test get_roulette_selection returns None when no stocks available."""
        result = crud.get_roulette_selection(db_session, 7, 2025)
        assert result is None

    def test_get_roulette_selection_missing_category(self, db_session: Session):
        """Test get_roulette_selection returns None when missing a category."""
        # Create stocks but missing 'sector' category
        stocks = [
            Stock(
                symbol="AAPL", 
                company_name="Apple Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 1, 1),
                available_to=None
            ),
            Stock(
                symbol="TSLA", 
                company_name="Tesla Inc.", 
                category="volatile",
                sector="Automotive",
                available_from=date(2025, 1, 1),
                available_to=None
            )
            # Missing 'sector' category stocks
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        result = crud.get_roulette_selection(db_session, 7, 2025)
        assert result is None

    def test_get_roulette_selection_stocks_not_available_in_month(self, db_session: Session):
        """Test get_roulette_selection with stocks not available in target month."""
        # Create stocks that are not available in July 2025
        stocks = [
            Stock(
                symbol="AAPL", 
                company_name="Apple Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 8, 1),  # Starts after July
                available_to=date(2025, 12, 31)
            ),
            Stock(
                symbol="TSLA", 
                company_name="Tesla Inc.", 
                category="volatile",
                sector="Automotive",
                available_from=date(2025, 1, 1),
                available_to=date(2025, 6, 30)  # Ends before July
            ),
            Stock(
                symbol="MSFT", 
                company_name="Microsoft Corp.", 
                category="sector",
                sector="Technology",
                available_from=date(2025, 9, 1),  # Starts after July
                available_to=date(2025, 12, 31)
            )
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        result = crud.get_roulette_selection(db_session, 7, 2025)
        assert result is None

    def test_get_roulette_selection_random_selection(self, db_session: Session):
        """Test that get_roulette_selection uses random selection."""
        # Create multiple stocks in each category
        stocks = [
            # Multiple popular stocks
            Stock(symbol="AAPL", company_name="Apple Inc.", category="popular", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="GOOGL", company_name="Alphabet Inc.", category="popular", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="AMZN", company_name="Amazon.com Inc.", category="popular", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            
            # Multiple volatile stocks
            Stock(symbol="TSLA", company_name="Tesla Inc.", category="volatile", sector="Automotive", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="GME", company_name="GameStop Corp.", category="volatile", sector="Retail", 
                  available_from=date(2025, 1, 1), available_to=None),
            
            # Multiple sector stocks in different sectors
            Stock(symbol="MSFT", company_name="Microsoft Corp.", category="sector", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="JNJ", company_name="Johnson & Johnson", category="sector", sector="Healthcare", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="JPM", company_name="JPMorgan Chase & Co.", category="sector", sector="Finance", 
                  available_from=date(2025, 1, 1), available_to=None)
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        # Call the function multiple times to check for randomness
        results = []
        for _ in range(10):
            result = crud.get_roulette_selection(db_session, 7, 2025)
            assert result is not None
            results.append((result.popular_symbol, result.volatile_symbol, result.sector_symbol))

        # Check that we get valid selections
        valid_popular = ["AAPL", "GOOGL", "AMZN"]
        valid_volatile = ["TSLA", "GME"]
        valid_sector = ["MSFT", "JNJ", "JPM"]
        
        for popular, volatile, sector in results:
            assert popular in valid_popular
            assert volatile in valid_volatile
            assert sector in valid_sector

        # Note: We can't easily test true randomness without mocking random.choice
        # but the structure ensures different combinations are possible

    def test_get_roulette_selection_sector_logic(self, db_session: Session):
        """Test that sector selection works correctly."""
        # Create stocks in different sectors
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", category="popular", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="TSLA", company_name="Tesla Inc.", category="volatile", sector="Automotive", 
                  available_from=date(2025, 1, 1), available_to=None),
            
            # Sector stocks in different sectors
            Stock(symbol="MSFT", company_name="Microsoft Corp.", category="sector", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="NVDA", company_name="NVIDIA Corp.", category="sector", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="JNJ", company_name="Johnson & Johnson", category="sector", sector="Healthcare", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="PFE", company_name="Pfizer Inc.", category="sector", sector="Healthcare", 
                  available_from=date(2025, 1, 1), available_to=None),
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        # Test multiple calls to see sector-based selection
        results = []
        for _ in range(20):
            result = crud.get_roulette_selection(db_session, 7, 2025)
            assert result is not None
            results.append(result.sector_symbol)

        # Should only get stocks from sector category
        valid_sector_symbols = ["MSFT", "NVDA", "JNJ", "PFE"]
        for sector_symbol in results:
            assert sector_symbol in valid_sector_symbols

    @patch('random.choice')
    def test_get_roulette_selection_mocked_random(self, mock_random_choice, db_session: Session):
        """Test get_roulette_selection with mocked random selection."""
        # Set up stocks
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", category="popular", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="TSLA", company_name="Tesla Inc.", category="volatile", sector="Automotive", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="MSFT", company_name="Microsoft Corp.", category="sector", sector="Technology", 
                  available_from=date(2025, 1, 1), available_to=None),
            Stock(symbol="JNJ", company_name="Johnson & Johnson", category="sector", sector="Healthcare", 
                  available_from=date(2025, 1, 1), available_to=None),
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        # Mock random.choice to return predictable results
        def mock_choice_side_effect(sequence):
            if hasattr(sequence[0], 'symbol'):  # It's a stock list
                return sequence[0]  # Always return first stock
            else:  # It's a sector list
                return sequence[0]  # Always return first sector
        
        mock_random_choice.side_effect = mock_choice_side_effect

        result = crud.get_roulette_selection(db_session, 7, 2025)
        assert result is not None
        assert result.popular_symbol == "AAPL"
        assert result.volatile_symbol == "TSLA"
        # The sector_symbol will depend on which sector is chosen first and which stock in that sector
        assert result.sector_symbol in ["MSFT", "JNJ"]

    def test_get_roulette_selection_edge_months(self, db_session: Session):
        """Test get_roulette_selection for edge case months (January, December, February)."""
        # Create stocks for different edge case scenarios
        stocks = [
            # Available for the entire year 2024
            Stock(symbol="AAPL", company_name="Apple Inc.", category="popular", sector="Technology", 
                  available_from=date(2024, 1, 1), available_to=date(2024, 12, 31)),
            Stock(symbol="TSLA", company_name="Tesla Inc.", category="volatile", sector="Automotive", 
                  available_from=date(2024, 1, 1), available_to=date(2024, 12, 31)),  # Available all year
            Stock(symbol="MSFT", company_name="Microsoft Corp.", category="sector", sector="Technology", 
                  available_from=date(2024, 1, 1), available_to=date(2024, 12, 31)),
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        # Test February in leap year (29 days)
        result = crud.get_roulette_selection(db_session, 2, 2024)
        assert result is not None
        assert result.popular_symbol == "AAPL"
        assert result.volatile_symbol == "TSLA"
        assert result.sector_symbol == "MSFT"

        # Test January
        result = crud.get_roulette_selection(db_session, 1, 2024)
        assert result is not None

        # Test December
        result = crud.get_roulette_selection(db_session, 12, 2024)
        assert result is not None
