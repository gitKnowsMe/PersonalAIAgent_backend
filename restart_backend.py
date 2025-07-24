#!/usr/bin/env python3
"""
Backend restart script to apply rate limiting fixes
"""

import subprocess
import sys
import time
import requests
import psutil

def find_backend_process():
    """Find running backend processes"""
    backend_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('main.py' in arg or 'start_backend.py' in arg for arg in cmdline):
                if any('Personal AI Agent' in arg for arg in cmdline):
                    backend_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return backend_processes

def stop_backend():
    """Stop running backend processes"""
    processes = find_backend_process()
    if not processes:
        print("ℹ️  No backend processes found running")
        return True
    
    print(f"🛑 Found {len(processes)} backend process(es). Stopping...")
    for proc in processes:
        try:
            proc.terminate()
            print(f"   Terminated PID {proc.pid}")
        except psutil.NoSuchProcess:
            print(f"   Process {proc.pid} already stopped")
    
    # Wait for graceful shutdown
    time.sleep(2)
    
    # Force kill if still running
    remaining = find_backend_process()
    if remaining:
        print("🔨 Force killing remaining processes...")
        for proc in remaining:
            try:
                proc.kill()
                print(f"   Killed PID {proc.pid}")
            except psutil.NoSuchProcess:
                pass
    
    return True

def start_backend():
    """Start the backend"""
    print("🚀 Starting backend with new rate limiting configuration...")
    try:
        # Start the backend
        process = subprocess.Popen([
            sys.executable, "start_backend.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give it time to start
        time.sleep(5)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Backend started successfully")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Backend failed to start")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return False

def test_health_check():
    """Test the health check endpoint"""
    print("🧪 Testing health check endpoint...")
    try:
        for i in range(5):
            response = requests.get("http://localhost:8000/api/health-check", timeout=3)
            print(f"   Request {i+1}: Status {response.status_code}")
            if response.status_code == 429:
                print(f"   ❌ Still rate limited: {response.text}")
                return False
            elif response.status_code == 200:
                print(f"   ✅ Success: {response.json()}")
            time.sleep(0.5)
        
        print("🎉 Health check is working without rate limiting!")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend")
        return False
    except Exception as e:
        print(f"❌ Error testing health check: {e}")
        return False

def main():
    print("🔄 Restarting Personal AI Agent Backend")
    print("=" * 50)
    
    # Stop existing backend
    if not stop_backend():
        print("❌ Failed to stop backend")
        return 1
    
    # Wait a moment
    time.sleep(1)
    
    # Start backend
    if not start_backend():
        print("❌ Failed to start backend")
        return 1
    
    # Test the fixes
    if not test_health_check():
        print("❌ Health check test failed")
        return 1
    
    print("\n🎉 Backend restart completed successfully!")
    print("Rate limiting issue has been resolved.")
    return 0

if __name__ == "__main__":
    sys.exit(main())