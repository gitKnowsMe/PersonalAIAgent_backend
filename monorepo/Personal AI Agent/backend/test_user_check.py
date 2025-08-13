#!/usr/bin/env python3
"""
Test script to check if the user 'gmail_tester' exists in the database
and test basic backend connectivity
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.models import User
from app.core.config import settings

def test_database_connection():
    """Test basic database connection"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # Test basic connection
            result = db.execute(text("SELECT 1")).scalar()
            print(f"✓ Database connection successful: {result}")
            
            # Check if users table exists
            users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            print(f"✓ Users table exists with {users_count} users")
            
            # Look for gmail_tester specifically
            user = db.query(User).filter(User.username == "gmail_tester").first()
            if user:
                print(f"✓ Found user: {user.username} (ID: {user.id}, Email: {user.email}, Active: {user.is_active})")
                return True
            else:
                print("✗ User 'gmail_tester' not found")
                
                # Show all users
                all_users = db.query(User).all()
                print(f"Available users ({len(all_users)}):")
                for u in all_users:
                    print(f"  - {u.username} (ID: {u.id}, Email: {u.email}, Active: {u.is_active})")
                return False
            
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        return False

def test_api_connectivity():
    """Test API connectivity"""
    import requests
    
    try:
        # Test root endpoint
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✓ Backend server is running on localhost:8000")
            data = response.json()
            print(f"  - Status: {data.get('status')}")
            print(f"  - Version: {data.get('version')}")
            return True
        else:
            print(f"✗ Backend server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend server on localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("✗ Timeout connecting to backend server")
        return False
    except Exception as e:
        print(f"✗ API connectivity error: {str(e)}")
        return False

def test_login_endpoint():
    """Test login endpoint with gmail_tester credentials"""
    import requests
    
    try:
        # Test login endpoint
        login_data = {
            "username": "gmail_tester",
            "password": "test123"  # Common test password
        }
        
        response = requests.post("http://localhost:8000/api/login", json=login_data, timeout=10)
        print(f"Login attempt result: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Login successful")
            data = response.json()
            print(f"  - Access token received: {bool(data.get('access_token'))}")
            return True
        elif response.status_code == 401:
            print("✗ Login failed: Invalid credentials")
            print(f"  - Response: {response.text}")
        else:
            print(f"✗ Login failed with status {response.status_code}")
            print(f"  - Response: {response.text}")
            
        return False
    except Exception as e:
        print(f"✗ Login test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Backend Login Issue Investigation ===\n")
    
    print("1. Testing database connection and user existence:")
    db_ok = test_database_connection()
    
    print("\n2. Testing API connectivity:")
    api_ok = test_api_connectivity()
    
    print("\n3. Testing login endpoint:")
    login_ok = test_login_endpoint()
    
    print("\n=== Summary ===")
    print(f"Database OK: {db_ok}")
    print(f"API OK: {api_ok}")
    print(f"Login OK: {login_ok}")
    
    if not db_ok:
        print("\nRecommendation: User 'gmail_tester' may not exist. Run create_admin.py to create it.")
    elif not api_ok:
        print("\nRecommendation: Backend server is not running. Run 'python start_backend.py' to start it.")
    elif not login_ok:
        print("\nRecommendation: Check password or authentication logic.")
    else:
        print("\nAll tests passed! The issue may be on the frontend side.")