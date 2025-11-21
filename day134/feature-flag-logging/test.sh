#!/bin/bash

set -e

echo "🧪 Running Feature Flag Status Logging System Tests"
echo "=================================================="

# Activate virtual environment
source venv/bin/activate

# Run backend tests
echo "🐍 Running backend unit tests..."
cd backend
python -m pytest tests/ -v --tb=short
cd ..

# Run integration tests (if backend is running)
echo "🔗 Checking if backend is running for integration tests..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running, running integration tests..."
    cd backend
    python -m pytest tests/test_integration.py -v
    cd ..
else
    echo "⚠️  Backend not running, skipping integration tests"
fi

# Test frontend build
echo "⚛️  Testing frontend build..."
cd frontend
npm run build
echo "✅ Frontend builds successfully"
cd ..

echo ""
echo "✅ All tests completed successfully!"
