#!/usr/bin/env python3
"""
Simple Admin User Creator
Creates admin user directly via SQL without importing app modules.

Usage: python create_default_admin.py
"""

import os
import sys
import psycopg

def create_admin_user():
    """Create admin user using direct database connection."""
    
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://stockroulette_user:ChangeMe123!@localhost:5432/stockroulette')
    
    # Convert psycopg format to standard if needed
    if database_url.startswith('postgresql+psycopg://'):
        database_url = database_url.replace('postgresql+psycopg://', 'postgresql://')
    
    try:
        print("🔌 Connecting to database...")
        
        # Connect to database
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                print("✅ Connected to database")
                
                # Check if admin user already exists
                cur.execute("SELECT login FROM admin_users WHERE login = %s", ('admin',))
                existing = cur.fetchone()
                
                if existing:
                    print("⚠️  Admin user 'admin' already exists!")
                    return True
                
                # Insert admin user with hashed password
                print("👤 Creating admin user...")
                cur.execute("""
                    INSERT INTO admin_users (login, password_hash) 
                    VALUES (%s, %s)
                """, (
                    'admin',
                    '$2b$12$L8gwIfmvPQnfrfJ9if0uSe2FM/uGH.SsTjpNgUG6jhfLMDRhqQZBG'
                ))
                
                conn.commit()
                
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
                
    except psycopg.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure PostgreSQL is running and the database exists")
        return False
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Creating default admin user...")
    print("=" * 50)
    
    success = create_admin_user()
    
    if success:
        print("=" * 50)
        print("🎉 Admin user creation completed!")
    else:
        print("=" * 50)
        print("❌ Admin user creation failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
