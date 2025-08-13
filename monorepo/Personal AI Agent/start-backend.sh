#!/bin/bash

# Personal AI Agent - Backend Startup Script

echo "🚀 Starting Personal AI Agent Backend..."

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Please run this script from the root directory of the Personal AI Agent repository"
    exit 1
fi

cd backend

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/quick-start.sh first"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if models exist
if [ ! -f "models/mistral-7b-instruct-v0.1.Q4_K_M.gguf" ]; then
    echo "⚠️  AI models not found. Run ./scripts/quick-start.sh to download them."
fi

# Start the backend
echo "🌟 Starting backend on http://localhost:8000"
echo "📝 API documentation: http://localhost:8000/docs"
echo "🔧 Health check: http://localhost:8000/api/health-check"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py