#!/usr/bin/env python3
"""
Test script to make actual API queries to test email search functionality
"""

import requests
import json
import sys
import os

# API base URL
BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token for API requests"""
    # Login with test credentials
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/login", data=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_email_query(token, query_text):
    """Test email query through API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with all sources (documents and emails)
    query_data = {
        "question": query_text,
        "source_type": "all",
        "source_id": None
    }
    
    print(f"Testing query: '{query_text}'")
    print(f"Request data: {json.dumps(query_data, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/api/queries", json=query_data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result.get('answer', 'No answer')}")
        print(f"From cache: {result.get('from_cache', False)}")
        print(f"Response time: {result.get('response_time_ms', 0)}ms")
        print(f"Sources: {result.get('sources', [])}")
        
        return result
    else:
        print(f"Query failed: {response.text}")
        return None

def test_email_only_query(token, query_text):
    """Test email-only query"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with emails only
    query_data = {
        "question": query_text,
        "source_type": "emails",
        "source_id": None
    }
    
    print(f"Testing email-only query: '{query_text}'")
    print(f"Request data: {json.dumps(query_data, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/api/queries", json=query_data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result.get('answer', 'No answer')}")
        print(f"From cache: {result.get('from_cache', False)}")
        print(f"Response time: {result.get('response_time_ms', 0)}ms")
        print(f"Sources: {result.get('sources', [])}")
        
        return result
    else:
        print(f"Query failed: {response.text}")
        return None

def main():
    """Main test function"""
    print("=== Email Search API Test ===")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token")
        return
    
    print(f"Got auth token: {token[:20]}...")
    
    # Test queries
    test_queries = [
        "check the email how much was the Apple invoice?",
        "Apple receipt cost amount",
        "iCloud subscription price",
        "show me receipts from Apple"
    ]
    
    print("\n" + "="*60)
    print("Testing All Sources (Documents + Emails)")
    print("="*60)
    
    for query in test_queries:
        print(f"\n--- Testing: {query} ---")
        result = test_email_query(token, query)
        if result:
            print("✓ Query succeeded")
        else:
            print("✗ Query failed")
    
    print("\n" + "="*60)
    print("Testing Email-Only Sources")
    print("="*60)
    
    for query in test_queries:
        print(f"\n--- Testing: {query} ---")
        result = test_email_only_query(token, query)
        if result:
            print("✓ Query succeeded")
        else:
            print("✗ Query failed")

if __name__ == "__main__":
    main()