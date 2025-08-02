import asyncio
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.post("/", response_model=schemas.Stock)
async def create_stock(stock_in: schemas.StockCreate, db: AsyncSession = Depends(get_db)):
    """Create a new stock."""
    # Check if stock already exists
    existing_stock = await crud.get_stock_by_symbol(db, stock_in.symbol)
    if existing_stock:
        raise HTTPException(status_code=400, detail="Stock symbol already exists")
    
    return await crud.create_stock(db, stock_in)


@router.get("/", response_model=List[schemas.Stock])
async def list_stocks(
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    sector: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
):
    """
    Get all stocks with optional filtering.
    
    - **category**: Filter by category (popular, volatile, sector)
    - **sector**: Filter by sector
    - **limit**: Maximum number of stocks to return
    - **offset**: Number of stocks to skip for pagination
    """
    return await crud.get_stocks(db, category=category, sector=sector, limit=limit, offset=offset)


@router.get("/sectors", response_model=List[str])
async def get_stock_sectors(db: AsyncSession = Depends(get_db)):
    """Get a list of unique stock sectors."""
    return await crud.get_stock_sectors(db)


@router.get("/eligible_dates", response_model=List[Tuple[int, int]])
async def get_eligible_dates(db: AsyncSession = Depends(get_db)):
    """Get a list of eligible month and years for stock trading."""
    return await crud.get_eligible_dates(db)

@router.get("/eligible_dates/roulette", response_model=Optional[dict[str, int]])
async def get_eligible_dates_roulette(db: AsyncSession = Depends(get_db)):
    """Get a random eligible month and year for roulette selections."""
    return await crud.get_eligible_dates_roulette(db)


@router.get("/prices/{symbol}", response_model=List[schemas.StockPrice])
async def get_stock_prices(symbol: str, start_date: str, end_date: str, db: AsyncSession = Depends(get_db)):
    """Get stock prices for a specific symbol within a date range."""
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    return await crud.get_stock_prices(db, symbol=symbol, start_date=start_date, end_date=end_date)


@router.get("/{symbol}", response_model=schemas.Stock)
async def get_stock(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get a specific stock by symbol."""
    stock = await crud.get_stock_by_symbol(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.post("/bulk", response_model=List[schemas.Stock])
async def create_stocks_bulk(stocks_in: List[schemas.StockCreate], db: AsyncSession = Depends(get_db)):
    """Create multiple stocks at once."""
    created_stocks = []
    for stock_data in stocks_in:
        # Skip if stock already exists
        existing_stock = await crud.get_stock_by_symbol(db, stock_data.symbol)
        if not existing_stock:
            created_stock = await crud.create_stock(db, stock_data)
            created_stocks.append(created_stock)
        else:
            created_stocks.append(existing_stock)
    
    return created_stocks
