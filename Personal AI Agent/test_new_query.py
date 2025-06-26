#!/usr/bin/env python3
import requests
import json
import time
import sys
import statistics

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "Iomaguire1"

# Test queries with timestamps to prevent caching
TEST_QUERIES = [
    f"What programming languages do I know? (t={time.time()})"
]

def login():
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/api/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code != 200:
        print(f"Login failed with status code {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    return response.json()["access_token"]

def run_query(token, query):
    """Run a query and measure performance"""
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/queries",
        headers=headers,
        json={"question": query}
    )
    end_time = time.time()
    
    if response.status_code != 200:
        print(f"Query failed with status code {response.status_code}")
        print(response.text)
        return None
    
    return {
        "query": query,
        "response": response.json().get("answer", ""),
        "time": end_time - start_time
    }

def main():
    print("Performance Test for Personal AI Agent (New Queries)")
    print("==================================================")
    
    # Login
    print("Logging in...")
    token = login()
    print("Login successful!")
    
    # Run tests
    print("\nRunning performance tests...")
    results = []
    
    for query in TEST_QUERIES:
        print(f"\nTesting query: '{query}'")
        
        # Run the query multiple times to get average performance
        times = []
        for i in range(3):
            # Add timestamp to query to prevent caching
            timestamped_query = f"{query} (run {i+1})"
            print(f"  Run {i+1}...")
            result = run_query(token, timestamped_query)
            if result:
                times.append(result["time"])
                print(f"  Time: {result['time']:.2f}s")
            
            # Wait a bit between queries
            if i < 2:
                time.sleep(1)
        
        # Calculate statistics
        if times:
            avg_time = statistics.mean(times)
            results.append({
                "query": query,
                "avg_time": avg_time,
                "min_time": min(times),
                "max_time": max(times)
            })
            print(f"  Average time: {avg_time:.2f}s")
    
    # Print summary
    print("\nPerformance Summary")
    print("==================")
    for result in results:
        print(f"Query: '{result['query']}'")
        print(f"  Avg: {result['avg_time']:.2f}s, Min: {result['min_time']:.2f}s, Max: {result['max_time']:.2f}s")
    
    # Calculate overall average
    if results:
        overall_avg = statistics.mean([r["avg_time"] for r in results])
        print(f"\nOverall average response time: {overall_avg:.2f}s")

if __name__ == "__main__":
    main() 