from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.post("/session", response_model=schemas.Session)
def start_session(session_in: schemas.SessionCreate, db: Session = Depends(get_db)):
    # Check if player exists
    player = crud.get_player(db, session_in.player_id)
    if not player:
        raise HTTPException(status_code=400, detail="Player does not exist")

    return crud.create_session(db, session_in)


@router.get("/session/{session_id}", response_model=schemas.Session)
def read_session(session_id: UUID, db: Session = Depends(get_db)):
    db_session = crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.patch("/session/{session_id}", response_model=schemas.Session)
def modify_session(session_id: UUID, session_upd: schemas.SessionUpdate, db: Session = Depends(get_db)):
    updated = crud.update_session(db, session_id, session_upd)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated
