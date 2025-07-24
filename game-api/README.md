# Stock Roulette API (game-api)

This service implements the backend for the Stock Roulette game, providing RESTful endpoints for game sessions, stock selections, trades, and an admin dashboard.

## Setup

1. **Clone repository**:
    ```bash
   git clone https://github.com/yourorg/stock-roulette-api.git
   cd stock-roulette-api
    ````

2. **Install dependencies**:

   ```bash
   uv install
   ```

3. **Configure environment**:

   * Copy `.env.example` to `.env`:

     ```bash
     cp .env.example .env
     ```
   * Fill in `DATABASE_URL`, `SECRET_KEY`, etc.

4. **Run migrations**:

   ```bash
   uv run migrate
   ```

5. **Start the server**:

   * Development (with hot reload):

     ```bash
     uv run dev
     ```
   * Production:

     ```bash
     uv run start
     ```

## Endpoints

* **Health check**: `GET /health`
* **Admin**:

  * `GET /admin/login`
  * `POST /admin/login`
  * `GET /admin/dashboard`
* **Sessions**:

  * `POST /sessions`
  * `GET /sessions/{session_id}`
  * `PATCH /sessions/{session_id}`
* **Selections**:

  * `POST /selections/{session_id}`
* **Trades**:

  * `POST /trades`
  * `GET /trades/session/{session_id}`

## Database

* Managed via Alembic migrations in `alembic/`.

## Seeding Admin User

To create an initial admin user, run a Python snippet:

```python
from app.core.db import SessionLocal
from app.core.auth import hash_password
from app import models

db = SessionLocal()
admin = models.AdminUser(login='admin', password_hash=hash_password('yourpassword'))
db.add(admin)
db.commit()
db.close()
```
