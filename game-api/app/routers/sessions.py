from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import crud, schemas
from app.core.db import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Session)
def start_session(session_in: schemas.SessionCreate, db: Session = Depends(get_db)):
    return crud.create_session(db, session_in)

@router.get("/{session_id}", response_model=schemas.Session)
def read_session(session_id: UUID, db: Session = Depends(get_db)):
    db_session = crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@router.patch("/{session_id}", response_model=schemas.Session)
def modify_session(session_id: UUID, session_upd: schemas.SessionUpdate, db: Session = Depends(get_db)):
    updated = crud.update_session(db, session_id, session_upd)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated