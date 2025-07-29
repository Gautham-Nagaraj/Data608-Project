from fastapi import APIRouter, Depends, Request, Form, Response, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date
import csv
import io
import uuid

from app import crud, schemas
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
def login(request: Request, response: Response, login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        # Get admin user from database
        admin = crud.get_admin_user(db, login)
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
        crud.create_audit_log(
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
def dashboard(request: Request, db: Session = Depends(get_db), admin_auth = Depends(require_admin_auth)):
    try:
        players = db.query(crud.models.Player).all()
        sessions = db.query(crud.models.Session).all()
        
        return {
            "players": [{"id": p.id, "nickname": p.nickname} for p in players],
            "sessions": [{"id": s.session_id, "player_id": s.player_id, "status": s.status, "balance": s.balance} for s in sessions]
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error in a real application
        raise HTTPException(status_code=500, detail="Internal server error")


# 1. Player & Session Overview
@router.get("/sessions")
def get_sessions_with_filters(
    db: Session = Depends(get_db),
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
        sessions = crud.get_sessions_with_filters(
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


# 2. Scoreboard Management
@router.get("/leaderboard")
def get_leaderboard(
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    top_n: int = Query(10, description="Number of top players to return"),
    sort_by: str = Query("total_score", description="Sort by: total_score, total_profit"),
):
    """Get top N players sorted by specified metric"""
    try:
        leaderboard = crud.get_leaderboard(db=db, top_n=top_n, sort_by=sort_by)
        return {"leaderboard": leaderboard, "sort_by": sort_by, "top_n": top_n}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")


@router.get("/player-stats")
def get_player_statistics(
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth)
):
    """Get comprehensive player statistics including average scores"""
    try:
        stats = crud.get_player_statistics(db=db)
        return {"player_statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch player statistics")


@router.get("/leaderboard/export")
def export_leaderboard_csv(
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    top_n: int = Query(50, description="Number of top players to export"),
    sort_by: str = Query("total_score", description="Sort by: total_score, total_profit"),
):
    """Export leaderboard as CSV file"""
    try:
        leaderboard = crud.get_leaderboard(db=db, top_n=top_n, sort_by=sort_by)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Rank", "Player ID", "Nickname", "Total Score", "Total Profit", 
            "Total Trades"
        ])
        
        # Write data
        for rank, player in enumerate(leaderboard, 1):
            writer.writerow([
                rank,
                player.get("player_id", ""),
                player.get("nickname", ""),
                player.get("total_score", 0),
                player.get("total_profit", 0),
                player.get("total_trades", 0)
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=leaderboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to export leaderboard")


# 8. Admin Actions
@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth)
):
    """Delete a specific session and all related data"""
    try:
        session_uuid = uuid.UUID(session_id)
        success = crud.delete_session_data(db=db, session_id=session_uuid)
        if success:
            # Log the deletion
            ip_address = request.client.host if request.client else None
            crud.create_audit_log(
                db=db,
                admin_login=admin_auth.get("login"),
                action="delete_session",
                target_id=session_id,
                ip_address=ip_address
            )
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.post("/sessions/{session_id}/archive")
def archive_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth)
):
    """Archive a session (mark as archived)"""
    try:
        session_uuid = uuid.UUID(session_id)
        success = crud.archive_session(db=db, session_id=session_uuid)
        if success:
            # Log the archival
            ip_address = request.client.host if request.client else None
            crud.create_audit_log(
                db=db,
                admin_login=admin_auth.get("login"),
                action="archive_session",
                target_id=session_id,
                ip_address=ip_address
            )
            return {"message": f"Session {session_id} archived successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to archive session")


@router.post("/data/reset")
def reset_all_data(
    confirm: str = Query(..., description="Type 'CONFIRM_RESET' to proceed"),
    request: Request = None,
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth)
):
    """Reset all session data - DANGEROUS OPERATION"""
    if confirm != "CONFIRM_RESET":
        raise HTTPException(status_code=400, detail="Confirmation required. Use 'CONFIRM_RESET'")
    
    try:
        crud.reset_all_session_data(db=db)
        
        # Log the data reset
        ip_address = request.client.host if request.client else None
        crud.create_audit_log(
            db=db,
            admin_login=admin_auth.get("login"),
            action="reset_all_data",
            details={"confirmation": confirm},
            ip_address=ip_address
        )
        
        return {"message": "All session data has been reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reset data")


@router.get("/data/export")
def export_database_snapshot(
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    include_tables: Optional[str] = Query("all", description="Comma-separated table names or 'all'")
):
    """Export database snapshot as CSV files in a ZIP"""
    try:
        # This is a placeholder - would need proper implementation
        # depending on requirements for database backup
        tables = include_tables.split(",") if include_tables != "all" else None
        export_data = crud.export_database_snapshot(db=db, tables=tables)
        
        return {"message": "Database export completed", "export_info": export_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to export database")


# 5. AI Agent Interaction Logs
@router.get("/interactions")
def get_agent_interactions(
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(100, description="Maximum number of interactions to return")
):
    """Get all agent interactions, optionally filtered by session"""
    try:
        session_uuid = None
        if session_id:
            session_uuid = uuid.UUID(session_id)
        
        interactions = crud.get_agent_interactions(db=db, session_id=session_uuid, limit=limit)
        
        return {
            "interactions": [
                {
                    "id": interaction.id,
                    "session_id": str(interaction.session_id),
                    "timestamp": interaction.timestamp,
                    "type": interaction.interaction_type,
                    "content": interaction.content,
                    "metadata": interaction.interaction_metadata
                }
                for interaction in interactions
            ],
            "count": len(interactions)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch interactions")


@router.get("/sessions/{session_id}/chat")
def get_session_chat_log(
    session_id: str,
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth)
):
    """Get complete chat log for a specific session"""
    try:
        session_uuid = uuid.UUID(session_id)
        chat_log = crud.get_session_chat_log(db=db, session_id=session_uuid)
        
        return {
            "session_id": session_id,
            "chat_log": chat_log,
            "total_interactions": len(chat_log)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch chat log")


# Admin Audit Logs
@router.get("/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    admin_auth = Depends(require_admin_auth),
    admin_login: Optional[str] = Query(None, description="Filter by admin login"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip")
):
    """Get admin audit logs with optional filters"""
    try:
        logs = crud.get_audit_logs(
            db=db,
            admin_login=admin_login,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return {
            "audit_logs": [
                {
                    "id": log.id,
                    "admin_login": log.admin_login,
                    "action": log.action,
                    "target_id": log.target_id,
                    "details": log.details,
                    "timestamp": log.timestamp,
                    "ip_address": log.ip_address
                }
                for log in logs
            ],
            "count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")


@router.post("/logout")
def logout(response: Response, admin_auth = Depends(require_admin_auth)):
    """Logout admin user"""
    response.delete_cookie("admin_session")
    return {"message": "Logged out successfully"}
