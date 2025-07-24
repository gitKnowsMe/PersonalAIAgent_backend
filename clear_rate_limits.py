#!/usr/bin/env python3
"""
Simple script to test if rate limiting fixes work
"""

import requests
import time

def test_rate_limits():
    print("🧪 Testing rate limiting fixes...")
    
    base_url = "http://localhost:8000"
    health_url = f"{base_url}/api/health-check"
    status_url = f"{base_url}/api/backend-status"
    
    try:
        print(f"Testing {health_url}")
        success_count = 0
        
        # Test rapid requests
        for i in range(10):
            response = requests.get(health_url, timeout=2)
            print(f"  Request {i+1}: {response.status_code}")
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                print(f"  Rate limited: {response.text}")
                break
            
            time.sleep(0.1)  # 100ms between requests
        
        print(f"\nHealth check success: {success_count}/10")
        
        # Test backend status
        print(f"\nTesting {status_url}")
        status_response = requests.get(status_url, timeout=2)
        print(f"  Backend status: {status_response.status_code}")
        
        if success_count >= 8:
            print("\n🎉 SUCCESS: Rate limiting issue appears to be resolved!")
        else:
            print("\n⚠️  Rate limiting may still be active - backend needs restart")
            print("\nTo fix this issue:")
            print("1. Stop the current backend process")
            print("2. Run: python start_backend.py")
            print("3. The new configuration will disable rate limiting for health checks")
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running")
        print("Please start the backend with: python start_backend.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_rate_limits()