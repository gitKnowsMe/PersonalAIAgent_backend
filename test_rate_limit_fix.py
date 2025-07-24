#!/usr/bin/env python3
"""
Test script to verify health check rate limiting fix
"""

import requests
import time

def test_rate_limits():
    print('🧪 Testing health check rate limits...')
    
    # Test multiple rapid requests to health check
    base_url = 'http://localhost:8000'
    health_url = f'{base_url}/api/health-check'
    backend_status_url = f'{base_url}/api/backend-status'
    
    print(f'Testing {health_url}')
    
    try:
        # Make 15 rapid requests to test the 1000/minute limit
        success_count = 0
        for i in range(15):
            response = requests.get(health_url, timeout=2)
            print(f'Request {i+1}: Status {response.status_code}')
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                print(f'Rate limited: {response.text}')
                break
            time.sleep(0.05)  # 50ms between requests (1200/minute rate)
        
        print(f'\nHealth check success: {success_count}/15')
        
        print(f'\nTesting {backend_status_url}')
        
        # Test backend status endpoint
        backend_success = 0
        for i in range(10):
            response = requests.get(backend_status_url, timeout=2)
            print(f'Backend Status {i+1}: Status {response.status_code}')
            if response.status_code == 200:
                backend_success += 1
            elif response.status_code == 429:
                print(f'Rate limited: {response.text}')
                break
            time.sleep(0.05)
        
        print(f'\nBackend status success: {backend_success}/10')
        
        if success_count >= 10 and backend_success >= 8:
            print('\n🎉 SUCCESS: Rate limit fix is working!')
            print('Health check endpoints now allow frequent polling')
        else:
            print('\n⚠️  Rate limiting may still be too restrictive')
        
    except requests.exceptions.ConnectionError:
        print('❌ Backend not running - please start it first')
        print('Run: python start_backend.py')
    except Exception as e:
        print(f'❌ Error testing: {e}')

if __name__ == "__main__":
    test_rate_limits()