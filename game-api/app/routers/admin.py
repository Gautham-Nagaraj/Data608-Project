from fastapi import APIRouter, Depends, Request, Form, Response, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import crud
from app.core.config import settings
from app.core.db import get_db
from app.core.auth import verify_password, create_signed_cookie, validate_signed_cookie

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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
    if not cookie or not validate_signed_cookie(cookie):
        raise HTTPException(status_code=401, detail="Not authenticated")
    players = db.query(crud.models.Player).all()
    sessions = db.query(crud.models.Session).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "players": players, "sessions": sessions})