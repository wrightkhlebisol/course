#!/bin/bash

set -e

echo "🚀 Building Feature Flag Status Logging System"
echo "=============================================="

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Verify Python version
python_version=$(python --version 2>&1)
echo "✅ Using $python_version"

# Install backend dependencies
echo "📥 Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run: ./start.sh (to start all services)"
echo "2. Open: http://localhost:3000 (frontend)"
echo "3. API: http://localhost:8000 (backend)"
echo "4. Run: ./test.sh (to run tests)"
