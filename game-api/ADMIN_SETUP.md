# Admin User Setup Guide

This guide explains how to create the default admin user for the Stock Roulette Game API.

## Default Credentials
- **Username:** `admin`
- **Password:** `data608`

⚠️ **Important:** Change these credentials in production!

## Setup Methods

### Method 1: Automatic Setup (Recommended)

**For Windows:**
```bash
setup_admin.bat
```

**For Linux/Mac:**
```bash
python setup_database.py
```

This will:
1. Run database migrations
2. Create the default admin user
3. Verify setup

### Method 2: Manual Database Setup

1. **Run migrations first:**
   ```bash
   uv run -- alembic upgrade head
   ```

2. **Create admin user:**
   ```bash
   python create_default_admin.py
   ```

### Method 3: Using Docker

The admin user is automatically created when using Docker Compose, as the `db/init.sql` file includes the admin user creation.

1. **Start with Docker:**
   ```bash
   docker-compose up -d
   ```

2. **The admin user will be created automatically**

### Method 4: Direct SQL

If you prefer to create the admin user manually via SQL:

```sql
-- Run this SQL after migrations are complete
INSERT INTO admin_users (login, password_hash) VALUES (
    'admin',
    '$2b$12$L8gwIfmvPQnfrfJ9if0uSe2FM/uGH.SsTjpNgUG6jhfLMDRhqQZBG'
) ON CONFLICT (login) DO NOTHING;
```

### Method 5: Custom Credentials

To create an admin user with custom credentials:

```bash
python create_admin.py --login your_username --password your_password
```

## Verification

After creating the admin user, you can test the login:

### Using curl:
```bash
curl -X POST "http://localhost:8000/api/admin/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "login=admin&password=data608"
```

### Expected Response:
```json
{"message": "Logged in"}
```

### Access Dashboard:
```bash
curl -X GET "http://localhost:8000/api/admin/dashboard" \
     -H "Cookie: admin_session=your_session_cookie"
```

## Security Notes

1. **Change Default Password:** The default password `data608` should be changed immediately in production
2. **Use HTTPS:** Always use HTTPS in production for admin endpoints
3. **Session Security:** Admin sessions use HTTP-only cookies for security
4. **Audit Logging:** All admin actions are automatically logged

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check DATABASE_URL environment variable
- Verify database credentials

### Migration Issues
```bash
# Check migration status
uv run -- alembic current

# View migration history
uv run -- alembic history

# Reset migrations (careful!)
uv run -- alembic downgrade base
uv run -- alembic upgrade head
```

### Admin User Already Exists
If the admin user already exists, the scripts will skip creation and notify you.

### Permission Issues
Make sure the database user has appropriate permissions:
```sql
GRANT ALL PRIVILEGES ON DATABASE stockroulette TO stockroulette_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO stockroulette_user;
```

## Files Overview

- `setup_admin.bat` - Windows batch script for complete setup
- `setup_database.py` - Python script for migrations + admin creation
- `create_default_admin.py` - Simple admin user creation
- `create_admin.py` - Custom admin user creation
- `init_admin.py` - Alternative admin creation method
- `db/init.sql` - SQL initialization including admin user
- `db/create_admin.sql` - Standalone SQL for admin creation

## Production Deployment

For production deployment:

1. **Use environment variables for credentials:**
   ```bash
   export ADMIN_USERNAME="your_secure_username"
   export ADMIN_PASSWORD="your_secure_password"
   ```

2. **Run setup with custom credentials:**
   ```bash
   python create_admin.py --login $ADMIN_USERNAME --password $ADMIN_PASSWORD
   ```

3. **Enable HTTPS and secure cookies**
4. **Set up proper firewall rules for admin endpoints**
5. **Consider IP whitelisting for admin access**

## Quick Start

For immediate setup with default credentials:

```bash
# Clone and setup
cd game-api

# Install dependencies
uv sync

# Setup database and admin
setup_admin.bat  # Windows
# OR
python setup_database.py  # Linux/Mac

# Start the server
uv run -- uvicorn app.main:app --reload

# Test admin login
curl -X POST "http://localhost:8000/api/admin/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "login=admin&password=data608"
```

The admin panel will be available at the `/api/admin/` endpoints!
