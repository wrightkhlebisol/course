#!/bin/bash

set -e

echo "🔨 Building Day 124: Azure Monitor Integration"
echo "=============================================="

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Setting up Python 3.11 virtual environment..."
    python3.11 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running unit tests..."
python -m pytest tests/unit/ -v

echo "🔬 Running integration tests..."
python -m pytest tests/integration/ -v

# Test Azure connection
echo "🔍 Testing Azure Monitor connection..."
cd src && python main.py test
cd ..

echo "✅ Build completed successfully!"
echo ""
echo "🚀 Next steps:"
echo "  1. Start web dashboard: ./start.sh"
echo "  2. View dashboard: http://localhost:8000"
echo "  3. Run with Docker: docker-compose up --build"
echo ""
