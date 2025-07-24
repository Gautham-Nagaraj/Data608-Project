from sqlalchemy.orm import Session
import uuid
from app import models, schemas

# Players

def get_player(db: Session, player_id: int):
    return db.query(models.Player).filter(models.Player.id == player_id).first()

def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = models.Player(nickname=player.nickname)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

# Admin Users

def get_admin_user(db: Session, login: str):
    return db.query(models.AdminUser).filter(models.AdminUser.login == login).first()

# Sessions

def create_session(db: Session, session: schemas.SessionCreate):
    db_session = models.Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

# Helper to fetch a session by ID

def get_session(db: Session, session_id: uuid.UUID):
    return db.query(models.Session).filter(models.Session.session_id == session_id).first()


def update_session(db: Session, session_id: uuid.UUID, session_update: schemas.SessionUpdate):
    db_session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not db_session:
        return None
    for field, value in session_update.dict(exclude_unset=True).items():
        setattr(db_session, field, value)
    db.commit()
    db.refresh(db_session)
    return db_session

# Selections

def set_selection(db: Session, session_id: uuid.UUID, selection: schemas.SelectionCreate):
    db_sel = models.SessionSelection(session_id=session_id, **selection.dict())
    db.add(db_sel)
    db.commit()
    db.refresh(db_sel)
    return db_sel

# Trades

def record_trade(db: Session, trade: schemas.TradeCreate):
    db_trade = models.Trade(**trade.dict())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def get_trades(db: Session, session_id: uuid.UUID):
    return db.query(models.Trade).filter(models.Trade.session_id == session_id).all()