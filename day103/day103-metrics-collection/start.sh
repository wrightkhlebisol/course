#!/bin/bash

echo "🚀 Starting Day 103: Comprehensive Metrics Collection System"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/lib/python3.11/site-packages/fastapi/__init__.py" ]; then
    echo "📥 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start Redis if not running
if ! redis-cli ping >/dev/null 2>&1; then
    echo "🔴 Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
fi

# Install Node.js dependencies for frontend
if [ ! -d "frontend/node_modules" ]; then
    echo "🌐 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start frontend in background
echo "🖥️  Starting React dashboard..."
cd frontend && npm start &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 10

# Start the metrics collection system
echo "📊 Starting metrics collection system..."
PYTHONPATH=. python src/main.py &
BACKEND_PID=$!

echo "✅ System started successfully!"
echo "📊 Backend API: http://localhost:8000"
echo "🖥️  Frontend Dashboard: http://localhost:3000"
echo "📋 API Documentation: http://localhost:8000/docs"

# Save PIDs for cleanup
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

# Wait for user interrupt
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT TERM

wait
