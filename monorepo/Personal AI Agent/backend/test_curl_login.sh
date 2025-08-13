#!/bin/bash

# Test script to verify login endpoint with curl
echo "=== Testing Login Endpoint with curl ==="

# Test 1: Health check
echo "1. Testing health check..."
curl -s http://localhost:8000/api/health-check | jq '.' || echo "Backend not running or jq not available"

# Test 2: Backend status
echo -e "\n2. Testing backend status..."
curl -s http://localhost:8000/api/backend-status | jq '.' || echo "Backend not running or jq not available"

# Test 3: Login with correct OAuth2 form data
echo -e "\n3. Testing login with correct credentials..."
curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=gmail_tester&password=Iomaguire1" | jq '.' || echo "Login failed"

# Test 4: Login with wrong credentials
echo -e "\n4. Testing login with wrong credentials..."
curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=gmail_tester&password=wrongpassword" | jq '.' || echo "Expected failure"

# Test 5: Get token and test protected endpoint
echo -e "\n5. Testing protected endpoint with token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=gmail_tester&password=Iomaguire1" | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
  echo "Token obtained: ${TOKEN:0:20}..."
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/documents | jq '.' || echo "Protected endpoint test"
else
  echo "Failed to get token"
fi

echo -e "\n=== Test Complete ==="