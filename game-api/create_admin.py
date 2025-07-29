#!/usr/bin/env python3
"""
Admin User Setup Script
Creates an admin user for the Stock Roulette Game API.

Usage:
    python create_admin.py --login admin --password your_secure_password
"""

import argparse
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.db import get_db_engine, get_session
from app.models import AdminUser, Base
from app.core.auth import hash_password


def create_admin_user(login: str, password: str):
    """Create an admin user in the database."""
    
    # Create database session
    engine = get_db_engine()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = get_session(engine)
    
    try:
        # Check if admin already exists
        existing_admin = db.query(AdminUser).filter(AdminUser.login == login).first()
        if existing_admin:
            print(f"❌ Admin user '{login}' already exists!")
            return False
        
        # Create new admin user
        admin_user = AdminUser(
            login=login,
            password_hash=hash_password(password)
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ Admin user '{login}' created successfully!")
        print(f"🔐 You can now login at: POST /api/admin/login")
        print(f"📊 Access dashboard at: GET /api/admin/dashboard")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Create an admin user for the Stock Roulette Game API')
    parser.add_argument('--login', required=True, help='Admin login username')
    parser.add_argument('--password', required=True, help='Admin password')
    
    args = parser.parse_args()
    
    if len(args.password) < 8:
        print("❌ Password must be at least 8 characters long!")
        sys.exit(1)
    
    success = create_admin_user(args.login, args.password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
