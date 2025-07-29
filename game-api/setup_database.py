#!/usr/bin/env python3
"""
Database Setup and Admin Initialization Script

This script:
1. Runs database migrations
2. Creates the default admin user (admin/data608)
3. Ensures the database is ready for use

Usage:
    python setup_database.py
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def run_migrations():
    """Run Alembic database migrations."""
    print("🔄 Running database migrations...")
    try:
        result = subprocess.run(
            ["uv", "run", "--", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def create_default_admin():
    """Create the default admin user."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models import AdminUser
        from app.core.auth import hash_password
        from app.core.config import settings
        
        print("👤 Creating default admin user...")
        
        # Create database engine
        engine = create_engine(str(settings.DATABASE_URL))
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if admin already exists
            existing_admin = db.query(AdminUser).filter(AdminUser.login == "admin").first()
            if existing_admin:
                print("⚠️  Admin user 'admin' already exists - skipping creation")
                return True
            
            # Create default admin user
            admin_user = AdminUser(
                login="admin",
                password_hash=hash_password("data608")
            )
            
            db.add(admin_user)
            db.commit()
            
            print("✅ Default admin user created successfully!")
            print("📝 Login credentials:")
            print("   Username: admin")
            print("   Password: data608")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: uv sync")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Stock Roulette Game Database...")
    print("=" * 50)
    
    # Step 1: Run migrations
    if not run_migrations():
        print("❌ Setup failed at migration step")
        return False
    
    # Step 2: Create admin user
    if not create_default_admin():
        print("❌ Setup failed at admin creation step")
        return False
    
    print("=" * 50)
    print("🎉 Database setup completed successfully!")
    print()
    print("🔐 Admin Panel Access:")
    print("   Login endpoint: POST /api/admin/login")
    print("   Dashboard: GET /api/admin/dashboard")
    print()
    print("⚠️  SECURITY NOTE:")
    print("   Remember to change the default password in production!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
