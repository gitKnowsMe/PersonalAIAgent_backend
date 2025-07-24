#!/usr/bin/env python3
"""
Create test user for login testing
"""

import sys
import os
sys.path.append('/Users/singularity/code/Personal AI Agent/backend')

from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def create_test_user():
    """Create the test user gmail_tester"""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == 'gmail_tester').first()
        
        if existing_user:
            print(f"✅ User 'gmail_tester' already exists (ID: {existing_user.id})")
            print(f"   Email: {existing_user.email}")
            print(f"   Active: {existing_user.is_active}")
            print(f"   Created: {existing_user.created_at}")
            return existing_user
        
        # Create new test user
        print("Creating test user 'gmail_tester'...")
        
        hashed_password = get_password_hash('Iomaguire1')
        test_user = User(
            email='gmail_tester@example.com',
            username='gmail_tester',
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Test user created successfully!")
        print(f"   User ID: {test_user.id}")
        print(f"   Username: {test_user.username}")
        print(f"   Email: {test_user.email}")
        print(f"   Password: Iomaguire1")
        print(f"   Active: {test_user.is_active}")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def test_user_login():
    """Test user login with backend API"""
    import requests
    
    print("\n🧪 Testing user login with backend API...")
    
    try:
        # Test login endpoint
        data = {
            'username': 'gmail_tester',
            'password': 'Iomaguire1'
        }
        
        response = requests.post(
            'http://localhost:8000/api/login',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login test successful!")
            print(f"   Access token received: {result.get('access_token', 'N/A')[:50]}...")
            print(f"   Token type: {result.get('token_type', 'N/A')}")
            print(f"   Expires in: {result.get('expires_in', 'N/A')} seconds")
        else:
            print(f"❌ Login test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Login test error: {e}")

if __name__ == "__main__":
    print("🔧 Personal AI Agent - Test User Creation")
    print("=" * 50)
    
    # Create test user
    user = create_test_user()
    
    if user:
        # Test login
        test_user_login()
        
        print("\n✅ Test user setup complete!")
        print("You can now login with:")
        print("   Username: gmail_tester")
        print("   Password: Iomaguire1")
    else:
        print("\n❌ Test user creation failed!")
        sys.exit(1)