#!/bin/bash

echo "🔨 Building Error Tracking System..."

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install frontend dependencies (if Node.js available)
if command -v node &> /dev/null; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
else
    echo "⚠️ Node.js not found, skipping frontend dependencies"
fi

echo "✅ Build completed successfully!"
