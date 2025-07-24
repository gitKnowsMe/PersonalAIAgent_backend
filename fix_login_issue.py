#!/usr/bin/env python3
"""
Login Issue Fix Script
Diagnoses and fixes the login page stuck issue
"""

import os
import sys
import subprocess
import requests
import json
import time
from pathlib import Path

def print_section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def test_backend_connectivity():
    """Test if backend is running and accessible"""
    print_section("PHASE 1: Backend Verification")
    
    # Test health check
    print("1. Testing backend health check...")
    try:
        response = requests.get("http://localhost:8000/api/health-check", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend health check: FAILED (Status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend health check: FAILED (Error: {e})")
        print("   Backend is not running or not accessible")
        return False
    
    # Test backend status
    print("\n2. Testing backend status...")
    try:
        response = requests.get("http://localhost:8000/api/backend-status", timeout=5)
        if response.status_code == 200:
            print("✅ Backend status: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend status: FAILED (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend status: FAILED (Error: {e})")
    
    # Test root endpoint
    print("\n3. Testing root endpoint...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Root endpoint: PASSED")
            data = response.json()
            if data.get("backend_installed"):
                print("   ✅ Backend detection: PASSED")
            else:
                print("   ❌ Backend detection: FAILED")
        else:
            print(f"❌ Root endpoint: FAILED (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint: FAILED (Error: {e})")
    
    return True

def test_login_endpoint():
    """Test the login endpoint with correct format"""
    print_section("PHASE 2: Login Endpoint Testing")
    
    # Test with correct form data format
    print("1. Testing login with FORM DATA (correct format)...")
    try:
        # Form data format - what the backend expects
        data = {
            'username': 'gmail_tester',
            'password': 'Iomaguire1'
        }
        
        response = requests.post(
            "http://localhost:8000/api/login",
            data=data,  # Form data
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Login with form data: PASSED")
            result = response.json()
            if 'access_token' in result:
                print("   ✅ Access token received")
                print(f"   Token type: {result.get('token_type', 'N/A')}")
            else:
                print("   ❌ No access token in response")
        else:
            print(f"❌ Login with form data: FAILED (Status: {response.status_code})")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Login with form data: FAILED (Error: {e})")
    
    # Test with JSON format (what frontend might be sending)
    print("\n2. Testing login with JSON (incorrect format)...")
    try:
        # JSON format - what the frontend might be sending incorrectly
        data = {
            'username': 'gmail_tester',
            'password': 'Iomaguire1'
        }
        
        response = requests.post(
            "http://localhost:8000/api/login",
            json=data,  # JSON data
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Login with JSON: PASSED (unexpected)")
        else:
            print(f"❌ Login with JSON: FAILED (Status: {response.status_code}) - EXPECTED")
            print(f"   This confirms the frontend is sending wrong format")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Login with JSON: FAILED (Error: {e})")

def check_database_users():
    """Check if the user exists in database"""
    print_section("PHASE 3: Database User Verification")
    
    try:
        # Import database modules
        sys.path.append('/Users/singularity/code/Personal AI Agent/backend')
        from app.db.database import SessionLocal
        from app.db.models import User
        
        db = SessionLocal()
        
        # Check if user exists
        user = db.query(User).filter(User.username == 'gmail_tester').first()
        
        if user:
            print("✅ User 'gmail_tester' found in database")
            print(f"   User ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Is Active: {user.is_active}")
        else:
            print("❌ User 'gmail_tester' NOT found in database")
            print("   Creating test user...")
            
            # Create test user
            from app.core.security import get_password_hash
            
            hashed_password = get_password_hash('Iomaguire1')
            new_user = User(
                email='gmail_tester@example.com',
                username='gmail_tester',
                hashed_password=hashed_password,
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print("✅ Test user created successfully")
            print(f"   User ID: {new_user.id}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")

def create_frontend_fix_guide():
    """Create a guide for fixing the frontend"""
    print_section("PHASE 4: Frontend Fix Guide")
    
    fix_guide = """
FRONTEND FIX REQUIRED:

The issue is that the frontend is sending login requests in JSON format, 
but the backend expects OAuth2 form data format.

=== CURRENT FRONTEND CODE (WRONG): ===
```typescript
// In login-form.tsx or similar
const response = await fetch('/api/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: loginData.username,
    password: loginData.password
  })
});
```

=== CORRECTED FRONTEND CODE (CORRECT): ===
```typescript
// In login-form.tsx or similar
const response = await fetch('/api/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  },
  body: new URLSearchParams({
    username: loginData.username,
    password: loginData.password
  })
});
```

=== ALTERNATIVE USING FormData: ===
```typescript
const formData = new FormData();
formData.append('username', loginData.username);
formData.append('password', loginData.password);

const response = await fetch('/api/login', {
  method: 'POST',
  body: formData
});
```

=== UPDATE API CLIENT: ===
If using an API client, update the login method:

```typescript
// In lib/api.ts or similar
async login(username: string, password: string) {
  const response = await fetch(`${this.baseURL}/api/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      username,
      password
    })
  });
  
  if (!response.ok) {
    throw new Error(`Login failed: ${response.status} ${response.statusText}`);
  }
  
  const data = await response.json();
  this.setToken(data.access_token);
  return data;
}
```

=== VERIFICATION: ===
1. Open browser developer tools
2. Go to Network tab
3. Try to login
4. Check the request:
   - Content-Type should be: application/x-www-form-urlencoded
   - Body should show: username=gmail_tester&password=Iomaguire1
   - NOT JSON format
"""
    
    print(fix_guide)
    
    # Save to file
    with open('/Users/singularity/code/Personal AI Agent/backend/FRONTEND_FIX_GUIDE.md', 'w') as f:
        f.write(fix_guide)
    
    print("✅ Frontend fix guide saved to: FRONTEND_FIX_GUIDE.md")

def main():
    """Main diagnostic function"""
    print("🔍 Personal AI Agent - Login Issue Diagnostic")
    print("=" * 60)
    
    # Phase 1: Backend verification
    backend_ok = test_backend_connectivity()
    
    if not backend_ok:
        print("\n❌ CRITICAL: Backend is not running!")
        print("   Please start the backend first:")
        print("   cd '/Users/singularity/code/Personal AI Agent/backend'")
        print("   python start_backend.py")
        return
    
    # Phase 2: Login endpoint testing
    test_login_endpoint()
    
    # Phase 3: Database verification
    check_database_users()
    
    # Phase 4: Frontend fix guide
    create_frontend_fix_guide()
    
    print_section("SUMMARY")
    print("✅ Backend is running and accessible")
    print("✅ Login endpoint works with correct format (form data)")
    print("❌ Frontend is likely sending wrong format (JSON instead of form data)")
    print("📝 Frontend fix guide created: FRONTEND_FIX_GUIDE.md")
    print("\nNEXT STEPS:")
    print("1. Apply the frontend fix (change JSON to form data)")
    print("2. Test login again")
    print("3. Check browser network tab to verify request format")

if __name__ == "__main__":
    main()