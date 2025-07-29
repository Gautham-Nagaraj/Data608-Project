#!/usr/bin/env python3
"""
Generate password hash for admin user
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.core.auth import hash_password
    
    password = "data608"
    hashed = hash_password(password)
    
    print("Password hash for 'data608':")
    print(hashed)
    print()
    print("SQL Insert statement:")
    print(f"INSERT INTO admin_users (login, password_hash) VALUES ('admin', '{hashed}') ON CONFLICT (login) DO NOTHING;")
    
except ImportError as e:
    print(f"Error importing auth module: {e}")
    # Fallback using bcrypt directly
    try:
        import bcrypt
        password = "data608".encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        print("Password hash for 'data608':")
        print(hashed)
    except ImportError:
        print("Neither app.core.auth nor bcrypt available")
        sys.exit(1)
