#!/usr/bin/env python3
"""
Initialize Default Admin User
Creates the default admin user for the Stock Roulette Game API.

Default credentials:
- Username: admin
- Password: data608
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, AdminUser
    from app.core.auth import hash_password
    from app.core.config import settings
    
    def init_default_admin():
        """Initialize default admin user in the database."""
        
        print("🚀 Initializing default admin user...")
        
        # Create database engine
        engine = create_engine(str(settings.DATABASE_URL))
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if admin already exists
            existing_admin = db.query(AdminUser).filter(AdminUser.login == "admin").first()
            if existing_admin:
                print("⚠️  Admin user 'admin' already exists!")
                print("   Current admin will NOT be modified.")
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
            print()
            print("🔐 You can now login at:")
            print("   POST /api/admin/login")
            print("📊 Access dashboard at:")
            print("   GET /api/admin/dashboard")
            print()
            print("⚠️  SECURITY WARNING:")
            print("   Please change the default password in production!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    if __name__ == "__main__":
        success = init_default_admin()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    print("and all dependencies are installed:")
    print("  uv sync")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
