# Admin Panel API Documentation

This document describes the comprehensive admin panel functionality for the Stock Roulette Game API.

## 🔐 Authentication

All admin endpoints require authentication via session cookies. 

### Login
```http
POST /api/admin/login
Content-Type: application/x-www-form-urlencoded

login=admin_username&password=admin_password
```

**Response:**
```json
{"message": "Logged in"}
```

Sets `admin_session` cookie for subsequent requests.

### Logout
```http
POST /api/admin/logout
```

**Response:**
```json
{"message": "Logged out successfully"}
```

## 📊 Dashboard & Overview

### Basic Dashboard
```http
GET /api/admin/dashboard
```

**Response:**
```json
{
  "players": [
    {"id": 1, "nickname": "TraderJoe"}
  ],
  "sessions": [
    {
      "id": "uuid-here",
      "player_id": 1,
      "status": "active",
      "balance": 10000.0
    }
  ]
}
```

## 🎮 Session Management

### Get Sessions with Filters
```http
GET /api/admin/sessions?player_id=1&status=active&start_date=2025-07-01&limit=50
```

**Query Parameters:**
- `player_id` (optional): Filter by player ID
- `status` (optional): Filter by session status
- `start_date` (optional): Filter sessions started from this date
- `end_date` (optional): Filter sessions started until this date  
- `limit` (optional): Maximum number of sessions (default: 100)
- `offset` (optional): Number of sessions to skip (default: 0)

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid-here",
      "player_id": 1,
      "player_nickname": "TraderJoe",
      "started_at": "2025-07-28T10:00:00",
      "ended_at": null,
      "status": "active",
      "balance": 9500.0,
      "total_score": 25.0,
      "total_profit": 150.0,
      "total_trades": 8
    }
  ],
  "count": 1
}
```

## 🏆 Leaderboard & Statistics

### Get Leaderboard
```http
GET /api/admin/leaderboard?top_n=10&sort_by=total_score
```

**Query Parameters:**
- `top_n` (optional): Number of top players (default: 10)
- `sort_by` (optional): Sort criteria - `total_score` or `total_profit` (default: total_score)

**Response:**
```json
{
  "leaderboard": [
    {
      "player_id": 1,
      "nickname": "TraderJoe",
      "total_score": 150.0,
      "total_profit": 2500.0,
      "total_trades": 45
    }
  ],
  "sort_by": "total_score",
  "top_n": 10
}
```

### Get Player Statistics
```http
GET /api/admin/player-stats
```

**Response:**
```json
{
  "player_statistics": {
    "total_players": 25,
    "total_sessions": 150,
    "total_trades": 3500,
    "active_players_30d": 18,
    "average_score_per_session": 32.5,
    "average_profit_per_session": 245.0,
    "average_trades_per_session": 23.3
  }
}
```

### Export Leaderboard CSV
```http
GET /api/admin/leaderboard/export?top_n=50&sort_by=total_score
```

**Response:** CSV file download with headers:
- Rank, Player ID, Nickname, Total Score, Total Profit, Total Trades, Sessions Played, Win Rate, Average Score

## 🤖 AI Agent Interactions

### Get All Agent Interactions
```http
GET /api/admin/interactions?session_id=uuid-here&limit=100
```

**Query Parameters:**
- `session_id` (optional): Filter by specific session
- `limit` (optional): Maximum interactions to return (default: 100)

**Response:**
```json
{
  "interactions": [
    {
      "id": 1,
      "session_id": "uuid-here",
      "timestamp": "2025-07-28T10:30:00",
      "type": "agent_suggestion",
      "content": "Consider buying AAPL based on current market trends",
      "metadata": {
        "confidence": 0.8,
        "suggested_stocks": ["AAPL"],
        "reasoning": "Strong quarterly earnings"
      }
    }
  ],
  "count": 1
}
```

### Get Session Chat Log
```http
GET /api/admin/sessions/{session_id}/chat
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "chat_log": [
    {
      "id": 1,
      "timestamp": "2025-07-28T10:30:00",
      "type": "user_message",
      "content": "What should I buy?",
      "metadata": null
    },
    {
      "id": 2,
      "timestamp": "2025-07-28T10:30:15",
      "type": "agent_response",
      "content": "I recommend AAPL based on recent trends",
      "metadata": {"confidence": 0.8}
    }
  ],
  "total_interactions": 2
}
```

## 🔧 Admin Actions

### Archive Session
```http
POST /api/admin/sessions/{session_id}/archive
```

Marks a session as archived and sets ended_at timestamp.

**Response:**
```json
{"message": "Session uuid-here archived successfully"}
```

### Delete Session
```http
DELETE /api/admin/sessions/{session_id}
```

⚠️ **Dangerous Operation** - Permanently deletes session and all related data (trades, scores, selections, unsold shares).

**Response:**
```json
{"message": "Session uuid-here deleted successfully"}
```

### Reset All Data
```http
POST /api/admin/data/reset?confirm=CONFIRM_RESET
```

⚠️ **EXTREMELY DANGEROUS** - Deletes ALL session data from the database.

**Query Parameters:**
- `confirm`: Must be exactly `CONFIRM_RESET`

**Response:**
```json
{"message": "All session data has been reset"}
```

### Export Database Snapshot
```http
GET /api/admin/data/export?include_tables=all
```

**Query Parameters:**
- `include_tables` (optional): Comma-separated table names or "all" (default: all)

**Response:**
```json
{
  "message": "Database export completed",
  "export_info": {
    "exported_tables": ["players", "sessions", "trades", "scores"],
    "table_counts": {
      "players": 25,
      "sessions": 150,
      "trades": 3500,
      "scores": 150
    },
    "export_timestamp": "2025-07-28T21:00:00.000000",
    "note": "This is a placeholder implementation..."
  }
}
```

## 📋 Audit Logging

### Get Audit Logs
```http
GET /api/admin/audit-logs?admin_login=testadmin&action=delete_session&limit=50
```

**Query Parameters:**
- `admin_login` (optional): Filter by admin user
- `action` (optional): Filter by action type
- `start_date` (optional): Filter from this date
- `end_date` (optional): Filter until this date
- `limit` (optional): Maximum logs to return (default: 100)
- `offset` (optional): Number of logs to skip (default: 0)

**Response:**
```json
{
  "audit_logs": [
    {
      "id": 1,
      "admin_login": "testadmin",
      "action": "delete_session",
      "target_id": "session-uuid-here",
      "details": null,
      "timestamp": "2025-07-28T21:00:00",
      "ip_address": "192.168.1.100"
    }
  ],
  "count": 1
}
```

## 🚨 Automatic Audit Logging

The following admin actions are automatically logged:
- `login` - Admin login
- `delete_session` - Session deletion
- `archive_session` - Session archival
- `reset_all_data` - Complete data reset
- `export_data` - Database export

Each log entry includes:
- Admin login name
- Action performed
- Target resource ID (when applicable)
- IP address
- Timestamp
- Additional details (when relevant)

## 🛡️ Security Features

1. **Session-based Authentication**: Secure HTTP-only cookies
2. **Audit Logging**: All admin actions are logged
3. **Confirmation Required**: Dangerous operations require explicit confirmation
4. **IP Address Tracking**: Admin actions include source IP
5. **Role-based Access**: Only authenticated admins can access endpoints

## 📝 Database Schema

### New Tables Added

#### `agent_interactions`
- `id` (Primary Key)
- `session_id` (Foreign Key to sessions)
- `timestamp`
- `interaction_type` (user_message, agent_response, agent_suggestion)
- `content` (The message/suggestion text)
- `metadata` (JSON - additional context)

#### `admin_audit_log`
- `id` (Primary Key)  
- `admin_login` (Admin username)
- `action` (Action performed)
- `target_id` (ID of affected resource)
- `details` (JSON - additional details)
- `timestamp`
- `ip_address`

## 🚀 Setup & Migration

1. **Run Migration:**
   ```bash
   uv run -- alembic upgrade head
   ```

2. **Create Admin User:**
   ```python
   # Add to your database initialization
   from app.models import AdminUser
   from app.core.auth import hash_password
   
   admin = AdminUser(
       login="admin",
       password_hash=hash_password("your_secure_password")
   )
   db.add(admin)
   db.commit()
   ```

3. **Test Admin Endpoints:**
   ```bash
   # Run tests
   uv run -- pytest tests/test_admin.py -v
   ```

## ✅ Implementation Status

### ✅ Completed Features:
- [x] Admin authentication with session cookies
- [x] Player & Session overview with filters
- [x] Scoreboard/leaderboard management
- [x] CSV export functionality
- [x] AI Agent interaction logs storage/retrieval
- [x] Admin actions (delete, archive, reset)
- [x] Database export (placeholder)
- [x] Comprehensive audit logging
- [x] Database migrations
- [x] Test coverage
- [x] API documentation

### 🔄 Future Enhancements:
- [ ] Full CSV/ZIP database export implementation
- [ ] Advanced analytics dashboard
- [ ] Real-time session monitoring
- [ ] Admin user management (CRUD)
- [ ] Role-based permissions (super admin, read-only admin)
- [ ] Email notifications for critical actions
- [ ] Data retention policies
- [ ] Session replay functionality
