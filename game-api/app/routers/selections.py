from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app import crud, schemas
from app.core.db import get_db

router = APIRouter()

@router.post("/{session_id}", response_model=schemas.Selection)
def create_selection(session_id: UUID, sel_in: schemas.SelectionCreate, db: Session = Depends(get_db)):
    return crud.set_selection(db, session_id, sel_in)