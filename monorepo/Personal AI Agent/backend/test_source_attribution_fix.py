#!/usr/bin/env python3
"""
Test script to verify the source attribution fix works correctly
"""
import asyncio
import sys
import os
import requests
import json

async def test_source_attribution_fix():
    """Test the fixed source attribution logic"""
    
    print("🧪 Testing Source Attribution Fix")
    print("=" * 50)
    
    # Test the problematic query via API
    test_queries = [
        "check emails how much was $8001.00 and $15,180.80?",
        "search emails Apple invoice amount",
        "find emails how much did I pay for Netflix?"
    ]
    
    # API endpoint
    base_url = "http://localhost:8000"
    
    # First, let's check if server is running
    try:
        response = requests.get(f"{base_url}/api/health-check", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running or health check failed")
            print("Please start the server with: python main.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server")
        print("Please start the server with: python main.py")
        return
    
    print("✅ Server is running")
    
    # Test login (assuming admin user exists)
    login_data = {
        "username": "admin",
        "password": "admin123"  # Default admin password
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/login", data=login_data, timeout=10)
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print("✅ Successfully logged in")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print("Please ensure admin user exists and password is correct")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test each query
    for i, test_query in enumerate(test_queries):
        print(f"\n🔍 Test {i+1}: {test_query}")
        print("-" * 60)
        
        # Prepare query payload for all sources
        query_payload = {
            "question": test_query,
            "source_type": "all",
            "source_id": None
        }
        
        try:
            # Send query
            response = requests.post(
                f"{base_url}/api/ask",
                headers=headers,
                json=query_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Query successful")
                print(f"Question: {result.get('question', '')}")
                print(f"Answer: {result.get('answer', '')[:200]}...")
                print(f"Response time: {result.get('response_time_ms', 0):.2f}ms")
                
                # Check sources
                sources = result.get('sources', [])
                if sources:
                    print(f"\n📋 Sources ({len(sources)}):")
                    for j, source in enumerate(sources):
                        source_type = source.get('type', 'unknown').upper()
                        source_label = source.get('label', 'Unknown')
                        print(f"  {j+1}. {source_type}: {source_label}")
                        
                        # Check if this is email-prioritized but document answers
                        if test_query.startswith(('check emails', 'search emails', 'find emails')):
                            if source_type == 'EMAIL':
                                print(f"     📧 Email source found (good if contains answer)")
                            elif source_type == 'DOCUMENT':
                                print(f"     📄 Document source found (good if actually contains answer)")
                else:
                    print("❌ No sources found")
                
                # Check for specific amounts in answer if it's the first query
                if i == 0 and ("$8001.00" in result.get('answer', '') or "$15,180.80" in result.get('answer', '')):
                    print("\n🎯 AMOUNT DETECTION:")
                    if any(source.get('type') == 'document' for source in sources):
                        print("✅ Fix working: Document sources attributed for amounts")
                    else:
                        print("⚠️  Only email sources, check if emails actually contain amounts")
                
            else:
                print(f"❌ Query failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    print("\n🏁 Test Summary:")
    print("- The fix should now show document sources when documents contain the actual answer")
    print("- Email prioritization still works for ordering, but source attribution is smarter")
    print("- Check the logs for detailed attribution decisions")

if __name__ == "__main__":
    asyncio.run(test_source_attribution_fix())