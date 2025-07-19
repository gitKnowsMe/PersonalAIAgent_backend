#!/usr/bin/env python3
"""
Test Backend Connection
Tests if the backend is accessible and returns the expected responses.
"""

import requests
import json
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_backend_connection():
    """Test backend connection and responses."""
    base_url = "http://localhost:8000"
    
    tests = [
        {
            "name": "Root Endpoint",
            "url": f"{base_url}/",
            "expected_keys": ["name", "version", "backend_installed", "status"]
        },
        {
            "name": "Health Check",
            "url": f"{base_url}/api/health-check",
            "expected_keys": ["status", "version"]
        },
        {
            "name": "Backend Status",
            "url": f"{base_url}/api/backend-status",
            "expected_keys": ["backend_installed", "backend_running", "ready"]
        }
    ]
    
    logger.info("🔍 Testing backend connection...")
    
    all_passed = True
    
    for test in tests:
        try:
            logger.info(f"\nTesting {test['name']}...")
            response = requests.get(test['url'], timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {test['name']}: Status {response.status_code}")
                
                # Check expected keys
                missing_keys = [key for key in test['expected_keys'] if key not in data]
                if missing_keys:
                    logger.warning(f"⚠️  Missing keys: {missing_keys}")
                else:
                    logger.info(f"✅ All expected keys present")
                
                # Pretty print response
                logger.info(f"Response: {json.dumps(data, indent=2)}")
                
            else:
                logger.error(f"❌ {test['name']}: Status {response.status_code}")
                logger.error(f"Response: {response.text}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ {test['name']}: Connection refused - backend not running")
            all_passed = False
        except requests.exceptions.Timeout:
            logger.error(f"❌ {test['name']}: Timeout - backend not responding")
            all_passed = False
        except Exception as e:
            logger.error(f"❌ {test['name']}: Error - {e}")
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Backend is running correctly.")
        logger.info("Your frontend should now detect the backend.")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Backend may not be running correctly.")
        logger.error("Try running: python start_backend.py")
        return 1

if __name__ == "__main__":
    sys.exit(test_backend_connection())