import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.core.config import settings
from app.core.db import engine, Base, get_db

# Initialize DB tables if not using Alembic
# Base.metadata.create_all(bind=engine)

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level="DEBUG" if settings.DEBUG else "INFO",
    backtrace=True,
    diagnose=settings.DEBUG,
)

# Create FastAPI app
app = FastAPI(debug=settings.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import admin, sessions, selections, trades
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(selections.router, prefix="/selections", tags=["selections"])
app.include_router(trades.router, prefix="/trades", tags=["trades"])

@app.get("/health")
def health_check():
    return {"status": "ok"}