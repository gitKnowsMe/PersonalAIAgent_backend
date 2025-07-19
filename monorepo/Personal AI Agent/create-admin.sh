#!/bin/bash

# Personal AI Agent - Create Admin User Script

echo "👤 Creating Admin User for Personal AI Agent..."

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

# Create admin user
echo "📝 You'll be prompted to create an admin account..."
echo ""
python create_admin.py