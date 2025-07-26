from fastapi import APIRouter, Depends, Request, Form, Response, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.core.auth import verify_password, create_signed_cookie, validate_signed_cookie
from app.core.db import get_db

router = APIRouter()


@router.post("/login")
def login(response: Response, login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = crud.get_admin_user(db, login)
    if not admin or not verify_password(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    cookie = create_signed_cookie({"login": login})
    response.set_cookie(key="admin_session", value=cookie, httponly=True)
    return {"message": "Logged in"}


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get("admin_session")
    if not cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # validate_signed_cookie now returns None for invalid cookies
    cookie_data = validate_signed_cookie(cookie)
    if not cookie_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    players = db.query(crud.models.Player).all()
    sessions = db.query(crud.models.Session).all()
    
    return {
        "players": [{"id": p.id, "name": p.name, "email": p.email} for p in players],
        "sessions": [{"id": s.id, "name": s.name, "status": s.status} for s in sessions]
    }
