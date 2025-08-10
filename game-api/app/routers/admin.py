from fastapi import APIRouter, Depends, Request, Form, Response, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, date
import csv
import io
import uuid

from app import crud, schemas, models
from app.core.auth import verify_password, create_signed_cookie, validate_signed_cookie
from app.core.db import get_db

router = APIRouter()


def require_admin_auth(request: Request):
    """Dependency to require admin authentication"""
    # Check for cookie authentication first (existing method)
    cookie = request.cookies.get("admin_session")
    if cookie:
        cookie_data = validate_signed_cookie(cookie)
        if cookie_data:
            return cookie_data
    
    # Check for Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_data = validate_signed_cookie(token)
        if token_data:
            return token_data
    
    raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/login")
async def login(request: Request, response: Response, login: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    try:
        # Get admin user from database
        admin = await crud.get_admin_user(db, login)
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password with enhanced error handling
        try:
            password_valid = verify_password(password, admin.password_hash)
        except Exception as auth_error:
            # Log the authentication error but don't expose details
            print(f"Authentication error for user {login}: {auth_error}")
            raise HTTPException(status_code=500, detail="Authentication service error")
        
        if not password_valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create session cookie and token
        cookie = create_signed_cookie({"login": login})
        response.set_cookie(key="admin_session", value=cookie, httponly=True)
        
        # Log successful login
        ip_address = request.client.host if request.client else None
        await crud.create_audit_log(
            db=db,
            admin_login=login,
            action="login",
            ip_address=ip_address
        )
        
        # Return both message and token for frontend compatibility
        return {
            "message": "Logged in",
            "token": cookie,
            "token_type": "bearer"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error in a real application
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db), admin_auth = Depends(require_admin_auth)):
    try:
        # Get players and sessions
        players_result = await db.execute(select(models.Player))
        players = players_result.scalars().all()
        
        sessions_result = await db.execute(select(models.Session))
        sessions = sessions_result.scalars().all()
        
        return {
            "players": [{"id": p.id, "nickname": p.nickname} for p in players],
            "sessions": [{"id": str(s.session_id), "player_id": s.player_id, "status": s.status, "balance": s.balance} for s in sessions]
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error in a real application
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions")
async def get_sessions_with_filters(
    db: AsyncSession = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    player_id: Optional[int] = Query(None, description="Filter by player ID"),
    status: Optional[str] = Query(None, description="Filter by session status"),
    start_date: Optional[date] = Query(None, description="Filter sessions started from this date"),
    end_date: Optional[date] = Query(None, description="Filter sessions started until this date"),
    limit: Optional[int] = Query(100, description="Maximum number of sessions to return"),
    offset: Optional[int] = Query(0, description="Number of sessions to skip")
):
    """Get all sessions with optional filters for admin dashboard"""
    try:
        sessions = await crud.get_sessions_with_filters(
            db=db,
            player_id=player_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")


@router.get("/leaderboard")
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    top_n: int = Query(500, description="Number of top players to return"),
    sort_by: str = Query("total_score", description="Sort by: total_score, total_profit"),
):
    """Get top N players sorted by specified metric"""
    try:
        leaderboard = await crud.get_leaderboard(db=db, top_n=top_n, sort_by=sort_by)
        return {"leaderboard": leaderboard, "sort_by": sort_by, "top_n": top_n}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")


@router.get("/player-stats")
async def get_player_statistics(
    db: AsyncSession = Depends(get_db),
    admin_auth = Depends(require_admin_auth)
):
    """Get comprehensive player statistics including average scores"""
    try:
        # Simple implementation for now
        result = await db.execute(select(func.count(models.Player.id)))
        player_count = result.scalar()
        
        result = await db.execute(select(func.count(models.Session.session_id)))
        session_count = result.scalar()
        
        stats = {
            "total_players": player_count,
            "total_sessions": session_count,
            "average_score": 0.0,  # Placeholder
            "total_trades": 0  # Placeholder
        }
        return {"player_statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch player statistics")


@router.get("/leaderboard/export")
async def export_leaderboard_csv(
    db: AsyncSession = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    top_n: int = Query(50, description="Number of top players to export"),
    sort_by: str = Query("total_score", description="Sort by: total_score, total_profit"),
):
    """Export leaderboard as CSV file"""
    try:
        leaderboard = await crud.get_leaderboard(db=db, top_n=top_n, sort_by=sort_by)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Rank", "Player ID", "Nickname", "Total Score", "Total Profit", "Total Trades"])
        
        # Write data
        for i, player in enumerate(leaderboard, 1):
            writer.writerow([
                i,
                player["player_id"],
                player["nickname"],
                player["total_score"],
                player["total_profit"],
                player["total_trades"]
            ])
        
        output.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=leaderboard_top_{top_n}_{sort_by}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to export leaderboard")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_auth = Depends(require_admin_auth)
):
    """Delete a specific session and all related data"""
    try:
        session_uuid = uuid.UUID(session_id)
        
        # Simple implementation - just delete the session
        result = await db.execute(select(models.Session).filter(models.Session.session_id == session_uuid))
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await db.delete(session)
        await db.commit()
        
        # Log the deletion
        ip_address = request.client.host if request.client else None
        await crud.create_audit_log(
            db=db,
            admin_login=admin_auth["login"],
            action="delete_session",
            target_id=session_id,
            ip_address=ip_address
        )
        
        return {"message": f"Session {session_id} deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.post("/logout")
async def logout(response: Response):
    """Logout admin user by clearing session cookie"""
    response.delete_cookie(key="admin_session")
    return {"message": "Logged out successfully"}
