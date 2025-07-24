#!/usr/bin/env python3
"""
Test both frontend and backend rate limiting
"""

import requests
import time

def test_both_frontend_backend():
    print('🔍 Checking BOTH Frontend and Backend Rate Limiting')
    print('=' * 60)

    # Test both frontend and backend endpoints
    endpoints = [
        ('Backend Health Check', 'http://localhost:8000/api/health-check'),
        ('Backend Status', 'http://localhost:8000/api/backend-status'),
        ('Frontend Health Check', 'http://localhost:3000/api/health-check'),
        ('Frontend Status', 'http://localhost:3000/api/backend-status')
    ]

    results = {}

    for name, url in endpoints:
        print(f'\n📡 Testing {name}:')
        print(f'   URL: {url}')
        
        try:
            # Test 3 rapid requests
            success_count = 0
            for i in range(3):
                response = requests.get(url, timeout=3)
                status_icon = '✅' if response.status_code == 200 else '❌'
                print(f'   {status_icon} Request {i+1}: {response.status_code}')
                
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    print(f'      Rate limited: {response.text}')
                    break
                elif response.status_code != 200:
                    print(f'      Error: {response.text}')
                    break
                    
                time.sleep(0.1)
            
            results[name] = {'success': success_count, 'total': 3, 'status': 'working' if success_count >= 2 else 'limited'}
        
        except requests.exceptions.ConnectionError:
            print(f'   🔌 Connection failed - service not running')
            results[name] = {'status': 'offline'}
        except requests.exceptions.Timeout:
            print(f'   ⏱️  Request timed out')
            results[name] = {'status': 'timeout'}
        except Exception as e:
            print(f'   ❌ Error: {e}')
            results[name] = {'status': 'error'}

    print('\n📊 Summary:')
    for name, result in results.items():
        status = result.get('status', 'unknown')
        if status == 'working':
            print(f'   ✅ {name}: Working ({result["success"]}/{result["total"]})')
        elif status == 'limited':
            print(f'   ⚠️  {name}: Rate limited ({result["success"]}/{result["total"]})')
        elif status == 'offline':
            print(f'   🔌 {name}: Service offline')
        else:
            print(f'   ❌ {name}: {status}')

    print('\n💡 Next Steps:')
    print('   1. If backend is rate limited: Cache needs to expire or restart backend')
    print('   2. If frontend is offline: Frontend may not be running on port 3000')
    print('   3. Rate limiting fix is implemented but cached limits may persist')

if __name__ == "__main__":
    test_both_frontend_backend()