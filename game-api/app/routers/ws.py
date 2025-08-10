import asyncio
from typing import List, Optional
import uuid
from datetime import datetime, date
import calendar

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
async def safe_send_json(websocket: WebSocket, data: dict):
    try:
        await websocket.send_json(data)
    except RuntimeError as e:
        if 'Cannot call "send" once a close message has been sent.' in str(e):
            pass  # Ignore sending on closed websocket
        else:
            raise
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.db import AsyncSessionLocal

router = APIRouter()


@router.websocket("/prices/{session_id}")
async def stream_prices(websocket: WebSocket, session_id: str):
    """
    Stream historical stock prices for a given session.
    This endpoint provides real-time-like streaming of historical price data
    for the stocks selected in a session.
    """
    await websocket.accept()
    
    try:
        # Convert session_id string to UUID
        session_uuid = uuid.UUID(session_id)

        # Create async database session
        async with AsyncSessionLocal() as db:
            try:
                # Verify the session exists
                session = await crud.get_session(db, session_uuid)
                if not session:
                    await safe_send_json(websocket, {"error": "Session not found"})
                    return

                # Get the selected stocks for this session
                selection = await crud.get_selection(db, session_uuid)
                if not selection:
                    await safe_send_json(websocket, {"error": "No stock selection found for this session"})
                    return

                # Get the symbols to stream
                symbols = [
                    selection.popular_symbol,
                    selection.volatile_symbol,
                    selection.sector_symbol
                ]

                # Calculate the date range for the selected month and year
                month = selection.month
                year = selection.year

                # Get first and last day of the month
                first_day = date(year, month, 1)
                last_day_of_month = calendar.monthrange(year, month)[1]
                last_day = date(year, month, last_day_of_month)

                # Get all historical prices for the month for all symbols
                all_historical_data = {}
                available_dates = set()

                for symbol in symbols:
                    historical_prices = await crud.get_stock_prices(db, symbol, first_day, last_day)
                    if historical_prices:
                        # Convert to dict keyed by date for easy lookup
                        symbol_data = {}
                        for price in historical_prices:
                            price_date = price.date.date()  # Convert datetime to date
                            symbol_data[price_date] = price
                            available_dates.add(price_date)
                        all_historical_data[symbol] = symbol_data

                if not available_dates:
                    await safe_send_json(websocket, {
                        "error": f"No historical data available for {calendar.month_name[month]} {year}"
                    })
                    return

                # Sort available dates
                sorted_dates = sorted(available_dates)

                await safe_send_json(websocket, {
                    "message": f"Starting historical price stream for {calendar.month_name[month]} {year}",
                    "date_range": {
                        "start": first_day.isoformat(),
                        "end": last_day.isoformat()
                    },
                    "total_dates": len(sorted_dates),
                    "symbols": symbols
                })

                # Stream prices continuously, cycling through historical data
                for date_index in range(len(sorted_dates)):
                    try:
                        current_date = sorted_dates[date_index]

                        # Prepare price data for this date
                        date_prices = []
                        for symbol in symbols:
                            if symbol in all_historical_data and current_date in all_historical_data[symbol]:
                                price_info = all_historical_data[symbol][current_date]
                                date_prices.append({
                                    "symbol": symbol,
                                    "price": price_info.price,
                                    "date": current_date.isoformat(),
                                    "timestamp": price_info.date.isoformat()
                                })

                        if date_prices:
                            await safe_send_json(websocket, {
                                "session_id": session_id,
                                "current_date": current_date.isoformat(),
                                "prices": date_prices,
                                "stream_info": {
                                    "date_index": date_index + 1,
                                    "total_dates": len(sorted_dates),
                                    "month": calendar.month_name[month],
                                    "year": year
                                },
                                "timestamp": datetime.now().isoformat()
                            })

                        # Small delay to simulate real-time streaming
                        await asyncio.sleep(10.0)

                    except WebSocketDisconnect:
                        print(f"WebSocket disconnected during streaming for session {session_id}")
                        break
                    except Exception as e:
                        print(f"Error during streaming: {str(e)}")
                        await safe_send_json(websocket, {"error": f"Error during streaming: {str(e)}"})
                        break

                # Send completion message
                await safe_send_json(websocket, {
                    "type": "stream_complete",
                    "message": f"End of historical price stream for {calendar.month_name[month]} {year}",
                    "date_range": {
                        "start": first_day.isoformat(),
                        "end": last_day.isoformat()
                    },
                    "total_dates": len(sorted_dates),
                    "symbols": symbols
                })

            except Exception as e:
                print(f"Database error: {str(e)}")
                await safe_send_json(websocket, {"error": f"Database error: {str(e)}"})
                    
    except ValueError:
        await safe_send_json(websocket, {"error": "Invalid session ID format"})
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        await safe_send_json(websocket, {"error": f"Unexpected error: {str(e)}"})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass