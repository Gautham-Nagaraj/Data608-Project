import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings

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
    allow_origins=["*"],  # Allow all origins
    # allow_origins=["http://192.168.100.143:5173", "http://localhost:5173"],  # Vite dev server and IP access
    # allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import admin, players, sessions, selections, stocks, trades, ws

app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(players.router, prefix="/api", tags=["players"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(selections.router, prefix="/api", tags=["selections"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(trades.router, prefix="/api", tags=["trades"])
app.include_router(ws.router, prefix="/ws", tags=["ws"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
