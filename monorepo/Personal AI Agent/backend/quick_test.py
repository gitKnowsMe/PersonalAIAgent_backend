#!/usr/bin/env python3
"""Quick backend connectivity test"""

import requests
import json

def test_backend():
    """Test backend connectivity"""
    print("Testing backend connectivity...")
    
    endpoints = [
        ("Health Check", "http://localhost:8000/api/health-check"),
        ("Backend Status", "http://localhost:8000/api/backend-status"),
        ("Root Endpoint", "http://localhost:8000/")
    ]
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: PASSED")
            else:
                print(f"❌ {name}: FAILED (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: FAILED (Error: {e})")
    
    # Test login endpoint
    print("\nTesting login endpoint...")
    try:
        data = {'username': 'gmail_tester', 'password': 'Iomaguire1'}
        response = requests.post(
            "http://localhost:8000/api/login",
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'access_token' in result:
                print("✅ Login endpoint: PASSED - Token received")
            else:
                print("❌ Login endpoint: FAILED - No token")
        else:
            print(f"❌ Login endpoint: FAILED (Status: {response.status_code})")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Login endpoint: FAILED (Error: {e})")

if __name__ == "__main__":
    test_backend()