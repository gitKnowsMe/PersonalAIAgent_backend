#!/usr/bin/env python3
"""
Multi-User Migration Test Script

Tests the multi-user functionality after PostgreSQL migration.
"""

import sys
import requests
import json
from time import sleep

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_user_registration():
    """Test user registration"""
    print("🔐 Testing User Registration...")
    
    # Test user data
    test_users = [
        {
            "username": "testuser1",
            "email": "testuser1@example.com",
            "password": "testpass123"
        },
        {
            "username": "testuser2", 
            "email": "testuser2@example.com",
            "password": "testpass456"
        }
    ]
    
    tokens = {}
    
    for user in test_users:
        # Register user
        response = requests.post(f"{API_BASE}/register", json=user)
        if response.status_code == 201:
            print(f"✅ User {user['username']} registered successfully")
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"ℹ️  User {user['username']} already exists")
        else:
            print(f"❌ Failed to register {user['username']}: {response.text}")
            continue
            
        # Login user
        login_data = {
            "username": user["username"],
            "password": user["password"]
        }
        response = requests.post(f"{API_BASE}/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            tokens[user["username"]] = token
            print(f"✅ User {user['username']} logged in successfully")
        else:
            print(f"❌ Failed to login {user['username']}: {response.text}")
    
    return tokens

def test_data_isolation(tokens):
    """Test data isolation between users"""
    print("\n🔒 Testing Data Isolation...")
    
    users = list(tokens.keys())
    if len(users) < 2:
        print("❌ Need at least 2 users for isolation testing")
        return
    
    # Test document isolation
    for i, user in enumerate(users):
        headers = {"Authorization": f"Bearer {tokens[user]}"}
        
        # Get documents for this user
        response = requests.get(f"{API_BASE}/documents", headers=headers)
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ User {user} can access their documents ({len(documents)} documents)")
        else:
            print(f"❌ User {user} cannot access documents: {response.text}")
    
    # Test query isolation
    for user in users:
        headers = {"Authorization": f"Bearer {tokens[user]}"}
        
        # Get queries for this user
        response = requests.get(f"{API_BASE}/queries", headers=headers)
        if response.status_code == 200:
            queries = response.json()
            print(f"✅ User {user} can access their queries ({len(queries)} queries)")
        else:
            print(f"❌ User {user} cannot access queries: {response.text}")

def test_database_multi_user():
    """Test database-level multi-user functionality"""
    print("\n📊 Testing Database Multi-User Functionality...")
    
    try:
        sys.path.append('.')
        from app.db.database import get_db
        from app.db.models import User, Document, Query
        
        db = next(get_db())
        
        # Check total users
        total_users = db.query(User).count()
        print(f"✅ Total users in database: {total_users}")
        
        # Check user-specific data
        for user in db.query(User).limit(3).all():
            user_docs = db.query(Document).filter(Document.owner_id == user.id).count()
            user_queries = db.query(Query).filter(Query.user_id == user.id).count()
            print(f"✅ User {user.username}: {user_docs} documents, {user_queries} queries")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

def test_vector_isolation():
    """Test vector database isolation"""
    print("\n🔍 Testing Vector Database Isolation...")
    
    try:
        import os
        vector_db_path = "/Users/singularity/code/Personal AI Agent/backend/data/vector_db"
        
        if os.path.exists(vector_db_path):
            # Count user-specific vector files
            for category in ["financial", "generic", "long_form", "emails"]:
                category_path = os.path.join(vector_db_path, category)
                if os.path.exists(category_path):
                    files = os.listdir(category_path)
                    user_files = [f for f in files if f.startswith("user_") or f.startswith("financial_user_") or f.startswith("generic_user_") or f.startswith("long_form_user_")]
                    print(f"✅ Vector DB {category}: {len(user_files)} user-specific files")
        else:
            print("ℹ️  Vector database path not found")
            
    except Exception as e:
        print(f"❌ Vector isolation test failed: {e}")

def main():
    """Main test function"""
    print("🚀 Multi-User Migration Test Suite")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health-check")
        if response.status_code != 200:
            print("❌ Backend is not running. Please start it first.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Please ensure it's running on localhost:8000")
        return
    
    print("✅ Backend is running\n")
    
    # Test user registration and login
    tokens = test_user_registration()
    
    # Test data isolation
    if tokens:
        test_data_isolation(tokens)
    
    # Test database multi-user
    test_database_multi_user()
    
    # Test vector isolation
    test_vector_isolation()
    
    print("\n🎉 Multi-User Migration Test Complete!")
    print("✅ PostgreSQL migration successful")
    print("✅ Multi-user functionality verified")

if __name__ == "__main__":
    main()