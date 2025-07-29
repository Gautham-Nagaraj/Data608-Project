from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.post("/sessions/", response_model=schemas.Session)
def start_session(session_in: schemas.SessionCreate, db: Session = Depends(get_db)):
    # Check if player exists
    player = crud.get_player(db, session_in.player_id)
    if not player:
        raise HTTPException(status_code=400, detail="Player does not exist")

    return crud.create_session(db, session_in)


@router.get("/sessions/{session_id}", response_model=schemas.Session)
def read_session(session_id: UUID, db: Session = Depends(get_db)):
    db_session = crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.patch("/sessions/{session_id}", response_model=schemas.Session)
def modify_session(session_id: UUID, session_upd: schemas.SessionUpdate, db: Session = Depends(get_db)):
    updated = crud.update_session(db, session_id, session_upd)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated

@router.post("/sessions/{session_id}/end", response_model=schemas.Score)
def end_session(session_id: UUID, db: Session = Depends(get_db)):
    """End a session by marking it as ended."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update the session status to ended
    session.status = "ended"
    
    # Set the ended timestamp
    from datetime import datetime, timezone
    session.ended_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(session)
    
    # Calculate and store the score
    db_score = crud.calculate_score(db, session_id)

    return db_score


@router.get("/sessions/{session_id}/summary", response_model=schemas.SessionSummary)
def get_session_summary(session_id: UUID, db: Session = Depends(get_db)):
    """Get comprehensive session summary with unsold shares and feedback."""
    summary = crud.get_session_summary(db, session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@router.get("/sessions/{session_id}/unsold-shares", response_model=list[schemas.UnsoldShare])
def get_unsold_shares(session_id: UUID, db: Session = Depends(get_db)):
    """Get all unsold shares for a session."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return crud.get_unsold_shares(db, session_id)


@router.get("/sessions/{session_id}/unsold-shares/summary")
def get_unsold_shares_summary(session_id: UUID, db: Session = Depends(get_db)):
    """Get aggregated summary of unsold shares by symbol."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return crud.get_unsold_shares_summary(db, session_id)