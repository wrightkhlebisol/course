#!/bin/bash

echo "🧪 Running Compliance Reports Tests"
echo "==================================="

# Backend tests
echo "🔍 Running backend tests..."
cd backend
source venv/bin/activate
python -m pytest tests/ -v --tb=short
BACKEND_TEST_RESULT=$?

if [ $BACKEND_TEST_RESULT -eq 0 ]; then
    echo "✅ Backend tests passed"
else
    echo "❌ Backend tests failed"
    exit 1
fi

# Frontend tests (if available)
echo "🔍 Checking frontend..."
cd ../frontend
if [ -f "package.json" ]; then
    echo "✅ Frontend setup verified"
else
    echo "❌ Frontend package.json missing"
    exit 1
fi

# API endpoint tests
echo "🔍 Testing API endpoints..."
cd ..

# Start backend for testing
python backend/app/main.py &
BACKEND_PID=$!
sleep 10

# Test endpoints
echo "Testing root endpoint..."
curl -f http://localhost:8000/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Root endpoint working"
else
    echo "❌ Root endpoint failed"
    kill $BACKEND_PID
    exit 1
fi

echo "Testing frameworks endpoint..."
curl -f http://localhost:8000/frameworks > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Frameworks endpoint working"
else
    echo "❌ Frameworks endpoint failed"
    kill $BACKEND_PID
    exit 1
fi

# Cleanup
kill $BACKEND_PID
sleep 2

echo "🎉 All tests passed!"
