from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.post("/player", response_model=schemas.Player)
def post_player(player_in: schemas.PlayerCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_player(db, player_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/players", response_model=List[schemas.Player])
def list_players(
    db: Session = Depends(get_db),
    nickname: Optional[str] = Query(None, description="Filter players by nickname (case-insensitive partial match)"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of players to return"),
    offset: int = Query(0, ge=0, description="Number of players to skip")
):
    """
    Get all players with optional filtering.
    
    - **nickname**: Filter by nickname (case-insensitive partial match)
    - **limit**: Maximum number of players to return (1-100)
    - **offset**: Number of players to skip for pagination
    """
    return crud.get_players(db, nickname=nickname, limit=limit, offset=offset)


@router.get("/player/{player_id}", response_model=schemas.Player)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """
    Get a specific player by ID.
    """
    player = crud.get_player(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
