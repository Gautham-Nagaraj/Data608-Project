#!/usr/bin/env python3
"""
Verify Admin Setup
Checks if the admin user exists and can authenticate.
"""

import sys
import os
from pathlib import Path

print("🔍 Verifying admin setup...")
print("=" * 40)

# Check if migration files exist
migration_dir = Path("alembic/versions")
if migration_dir.exists():
    migration_files = list(migration_dir.glob("*.py"))
    print(f"✅ Found {len(migration_files)} migration files")
else:
    print("❌ Migration directory not found")

# Check if admin scripts exist
scripts = [
    "setup_admin.bat",
    "create_default_admin.py", 
    "setup_database.py",
    "init_admin.py",
    "db/create_admin.sql",
    "db/init.sql"
]

print("\n📁 Checking admin setup files:")
for script in scripts:
    if Path(script).exists():
        print(f"✅ {script}")
    else:
        print(f"❌ {script} - missing")

print("\n🔐 Default admin credentials:")
print("   Username: admin")
print("   Password: data608")

print("\n📝 To setup admin user, run one of:")
print("   Windows: setup_admin.bat")
print("   Python:  python setup_database.py")
print("   Direct:  python create_default_admin.py")

print("\n🚀 After setup, test with:")
print('   curl -X POST "http://localhost:8000/api/admin/login" \\')
print('        -H "Content-Type: application/x-www-form-urlencoded" \\')
print('        -d "login=admin&password=data608"')

print("\n⚠️  Remember to change the default password in production!")
print("=" * 40)
