# WebSocket Historical Price Streaming Implementation

## Overview

The `stream_prices` WebSocket endpoint has been enhanced to stream historical stock prices for a specific month and year, as defined in the session's selection data. Instead of streaming real-time prices, it now cycles through historical data from the first day to the last day of the specified month.

## Changes Made

### 1. Updated WebSocket Endpoint (`app/routers/ws.py`)

The `stream_prices` function now:
- Retrieves the `month` and `year` from the session's selection
- Calculates the date range for the entire month
- Fetches all historical stock prices for the selected symbols within that month
- Cycles through the available historical data every 10 seconds
- Provides detailed streaming information in each message

### 2. Key Features

- **Historical Data Streaming**: Instead of real-time prices, streams historical data for the specified month/year
- **Continuous Cycling**: When it reaches the end of the month's data, it cycles back to the beginning
- **10-Second Intervals**: Sends a new data point every 10 seconds as requested
- **Comprehensive Error Handling**: Handles missing data, invalid sessions, and database errors gracefully
- **Detailed Metadata**: Each message includes streaming progress information

### 3. Message Format

The WebSocket now sends messages in this format:

```json
{
    "session_id": "4f78dbef-74e4-4930-84c1-738663e12cbc",
    "current_date": "2025-07-01",
    "prices": [
        {
            "symbol": "DEMO1",
            "price": 100.0,
            "date": "2025-07-01",
            "timestamp": "2025-07-01T00:00:00"
        },
        {
            "symbol": "DEMO2", 
            "price": 200.0,
            "date": "2025-07-01",
            "timestamp": "2025-07-01T00:00:00"
        },
        {
            "symbol": "DEMO3",
            "price": 300.0,
            "date": "2025-07-01",
            "timestamp": "2025-07-01T00:00:00"
        }
    ],
    "stream_info": {
        "date_index": 1,
        "total_dates": 5,
        "month": "July",
        "year": 2025
    },
    "timestamp": "2025-07-27T13:45:30.123456"
}
```

### 4. Database Schema Updates

- Added `month` and `year` fields to the `SessionSelection` model
- Created Alembic migration `505801369983_add_month_year_to_session_selections.py`
- Updated schemas to include validation for month (1-12) and year (1900-2100)

### 5. Updated Dependencies

The WebSocket now uses:
- `crud.get_stock_prices()` to fetch historical data for date ranges
- `calendar` module to determine month boundaries
- Enhanced error handling for missing historical data

## Usage

1. **Create a session with month/year selection**:
   ```python
   selection = {
       "popular_symbol": "AAPL",
       "volatile_symbol": "TSLA",
       "sector_symbol": "MSFT",
       "month": 7,
       "year": 2025
   }
   ```

2. **Connect to WebSocket**:
   ```
   ws://localhost:8000/ws/prices/{session_id}
   ```

3. **Receive streaming data**:
   - Historical prices for the specified month/year
   - Updates every 10 seconds
   - Cycles through all available dates in the month
   - Includes progress information and metadata

## Error Handling

The WebSocket handles several error scenarios:
- **Invalid Session ID**: Returns error message and closes connection
- **Missing Selection**: Returns error if no selection exists for the session
- **No Historical Data**: Returns error if no price data exists for the specified month/year
- **Database Errors**: Catches and reports database connection issues

## Testing

- Created comprehensive tests in `test_websocket_historical.py`
- Tests cover successful streaming, error handling, and edge cases
- Demo script (`demo_websocket.py`) creates sample data for manual testing

## Backwards Compatibility

The changes maintain backwards compatibility:
- Existing API endpoints still work
- Old selection records can be migrated with default month/year values
- Error handling ensures graceful degradation

## Performance Considerations

- Historical data is loaded once at connection time, not on every message
- Database connection is managed efficiently
- Memory usage is optimized by using date-indexed lookups
- 10-second intervals prevent overwhelming the client or server

## Example Output

When connected to the WebSocket, you'll see a continuous stream of historical prices cycling through the month's data, allowing visualization of how stock prices changed throughout the specified time period.
