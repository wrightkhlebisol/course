#!/bin/bash

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "🏗️  Building Day 135: Slack Integration System"
echo "=============================================="

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv || python3.11 -m venv venv || python -m venv venv

# Install Python dependencies
echo "📥 Installing Python dependencies..."
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt

# Install Node.js dependencies for frontend
echo "📥 Installing Node.js dependencies..."
if command -v npm &> /dev/null; then
    npm install
else
    echo "⚠️  Node.js not found. Frontend will not be built."
fi

# Run tests
echo "🧪 Running tests..."
./venv/bin/python -m pytest tests/ -v

# Check syntax
echo "🔍 Checking Python syntax..."
./venv/bin/python -m py_compile src/backend/main.py
./venv/bin/python -m py_compile src/backend/services/slack_service.py

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure Slack credentials in .env file"
echo "2. Run: ./start.sh"
echo "3. Open: http://localhost:8000"
