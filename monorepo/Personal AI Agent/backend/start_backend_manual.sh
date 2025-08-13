#!/bin/bash
# Manual Backend Startup Script

echo "🔧 Personal AI Agent - Manual Backend Startup"
echo "=============================================="

# Change to backend directory
cd "/Users/singularity/code/Personal AI Agent/backend"

# Kill existing processes
echo "🔄 Stopping existing backend processes..."
pkill -f "uvicorn.*main" 2>/dev/null || true
pkill -f "python.*main" 2>/dev/null || true
sleep 2

# Check if port 8000 is available
echo "🔍 Checking port 8000..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is still in use. Trying to kill process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start the backend
echo "🚀 Starting backend server..."
echo "📍 Backend will be available at: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/api/health-check"
echo "⚡ Backend status: http://localhost:8000/api/backend-status"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start with Python
python start_backend.py