from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.post("/selections/{session_id}", response_model=schemas.Selection)
def create_selection(session_id: UUID, sel_in: schemas.SelectionCreate, db: Session = Depends(get_db)):
    # Check if session exists
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return crud.set_selection(db, session_id, sel_in)

@router.get("/selections/roulette", response_model=schemas.Selection)
def get_roulette_selection(month: int, year: int, db: Session = Depends(get_db)):
    """Get the roulette selection for a specific month and year."""
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    if year < 1900 or year > 2100:
        raise HTTPException(status_code=400, detail="Year must be between 1900 and 2100")
    
    selection = crud.get_roulette_selection(db, month, year)
    if not selection:
        raise HTTPException(status_code=404, detail="Roulette selection not found for the specified month and year")
    return selection

@router.get("/selections/{session_id}", response_model=schemas.Selection)
def get_selection(session_id: UUID, db: Session = Depends(get_db)):
    """Get the selection for a specific session."""
    selection = crud.get_selection(db, session_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    return selection
