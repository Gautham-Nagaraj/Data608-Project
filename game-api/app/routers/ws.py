import asyncio
from typing import List, Optional
import uuid
from datetime import datetime, date
import calendar

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.websocket("/prices/{session_id}")
async def stream_prices(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    try:
        # Convert session_id string to UUID
        session_uuid = uuid.UUID(session_id)
        
        # Get database session
        db = next(get_db())
        
        try:
            # Verify the session exists
            session = crud.get_session(db, session_uuid)
            if not session:
                await websocket.send_json({"error": "Session not found"})
                return
            
            # Get the selected stocks for this session
            selection = crud.get_selection(db, session_uuid)
            if not selection:
                await websocket.send_json({"error": "No stock selection found for this session"})
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
                historical_prices = crud.get_stock_prices(db, symbol, first_day, last_day)
                if historical_prices:
                    # Convert to dict keyed by date for easy lookup
                    symbol_data = {}
                    for price in historical_prices:
                        price_date = price.date.date()  # Convert datetime to date
                        symbol_data[price_date] = price
                        available_dates.add(price_date)
                    all_historical_data[symbol] = symbol_data
            
            if not available_dates:
                await websocket.send_json({
                    "error": f"No historical data available for {calendar.month_name[month]} {year}"
                })
                return
            
            # Sort available dates
            sorted_dates = sorted(available_dates)
            
            await websocket.send_json({
                "message": f"Starting historical price stream for {calendar.month_name[month]} {year}",
                "date_range": {
                    "start": first_day.isoformat(),
                    "end": last_day.isoformat()
                },
                "total_dates": len(sorted_dates),
                "symbols": symbols
            })
            
            # Stream prices continuously, cycling through historical data
            # Initialize streaming index
            for date_index in range(len(sorted_dates)):
                try:
                    current_date = sorted_dates[date_index]
                    
                    # Prepare the price data for the current date
                    price_data = []
                    for symbol in symbols:
                        if symbol in all_historical_data and current_date in all_historical_data[symbol]:
                            price_record = all_historical_data[symbol][current_date]
                            price_data.append({
                                "symbol": symbol,
                                "price": price_record.price,
                                "date": current_date.isoformat(),
                                "timestamp": price_record.date.isoformat()
                            })
                        else:
                            # If no data available for this symbol on this date, skip or use previous available price
                            continue
                    
                    # Send the price data if we have any
                    if price_data:
                        await websocket.send_json({
                            "session_id": session_id,
                            "current_date": current_date.isoformat(),
                            "prices": price_data,
                            "stream_info": {
                                "date_index": date_index + 1,
                                "total_dates": len(sorted_dates),
                                "month": calendar.month_name[month],
                                "year": year
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    # Move to next date, cycle back to beginning when reaching the end
                    date_index = (date_index + 1) % len(sorted_dates)
                    
                    # Wait 10 seconds before next update
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    await websocket.send_json({"error": f"Error streaming historical prices: {str(e)}"})
                    break
            
            await websocket.send_json({
                "message": f"End of historical price stream for {calendar.month_name[month]} {year}",
                "date_range": {
                    "start": first_day.isoformat(),
                    "end": last_day.isoformat()
                },
                "total_dates": len(sorted_dates),
                "symbols": symbols
            })

        finally:
            db.close()
                    
    except ValueError:
        await websocket.send_json({"error": "Invalid session ID format"})
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        await websocket.send_json({"error": f"Unexpected error: {str(e)}"})
    finally:
        await websocket.close()