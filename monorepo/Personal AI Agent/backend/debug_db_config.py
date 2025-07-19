#!/usr/bin/env python3
"""Debug database configuration"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Database Configuration Debug ===")
print(f"Current working directory: {os.getcwd()}")
print(f"BASE_DIR: {Path(__file__).resolve().parent}")

# Check environment variables
print("\n=== Environment Variables ===")
print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL')}")
print(f"DATABASE_TIMEOUT from env: {os.getenv('DATABASE_TIMEOUT')}")

# Check .env file content
print("\n=== .env File Content ===")
try:
    with open('.env', 'r') as f:
        for line_num, line in enumerate(f, 1):
            if 'DATABASE' in line:
                print(f"Line {line_num}: {line.strip()}")
except FileNotFoundError:
    print(".env file not found")

# Test settings loading
print("\n=== Settings Loading Test ===")
try:
    from app.core.config import settings
    print(f"settings.DATABASE_URL: {settings.DATABASE_URL}")
    print(f"settings.DATABASE_TIMEOUT: {settings.DATABASE_TIMEOUT}")
    print(f"Database URL starts with 'sqlite': {settings.DATABASE_URL.startswith('sqlite')}")
except Exception as e:
    print(f"Error loading settings: {e}")

# Test database connection logic
print("\n=== Connection Args Test ===")
try:
    from app.core.config import settings
    from app.core.constants import SQLITE_THREAD_CHECK
    
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": SQLITE_THREAD_CHECK}
        print(f"SQLite connection args: {connect_args}")
    else:
        connect_args = {"connect_timeout": settings.DATABASE_TIMEOUT}
        print(f"PostgreSQL connection args: {connect_args}")
        
except Exception as e:
    print(f"Error testing connection args: {e}")

# Test actual database connection
print("\n=== Database Connection Test ===")
try:
    from sqlalchemy import create_engine
    from app.core.config import settings
    from app.core.constants import SQLITE_THREAD_CHECK
    
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": SQLITE_THREAD_CHECK}
    else:
        connect_args = {"connect_timeout": settings.DATABASE_TIMEOUT}
    
    print(f"Creating engine with URL: {settings.DATABASE_URL}")
    print(f"Connection args: {connect_args}")
    
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args
    )
    
    connection = engine.connect()
    connection.close()
    print("✅ Database connection successful!")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc()