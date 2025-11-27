#!/bin/bash

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "🚀 Starting Slack Integration System"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Running build first..."
    "$SCRIPT_DIR/build.sh"
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start Redis if not running (using Docker if available, otherwise try system Redis)
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    if ! docker ps | grep -q redis; then
        echo "🔴 Starting Redis server with Docker..."
        docker-compose up -d redis 2>/dev/null || docker run -d --name redis -p 6379:6379 redis:7-alpine 2>/dev/null || true
        sleep 2
    fi
elif command -v redis-cli &> /dev/null; then
    if ! redis-cli ping &> /dev/null; then
        echo "🔴 Starting Redis server..."
        redis-server --daemonize yes
        sleep 2
    fi
else
    echo "⚠️  Redis not found. Install Redis or Docker to enable full functionality."
fi

# Start backend
echo "🔵 Starting backend server..."
cd "$SCRIPT_DIR" || exit 1
python -m src.backend.main &
BACKEND_PID=$!

# Build and serve frontend if npm is available
if command -v npm &> /dev/null; then
    echo "🟢 Building and starting frontend..."
    cd "$SCRIPT_DIR" || exit 1
    npm run build
    npx serve -s build -l 3000 &
    FRONTEND_PID=$!
fi

echo ""
echo "🎉 System started successfully!"
echo ""
echo "🔗 Backend API: http://localhost:8000"
echo "🔗 Frontend Dashboard: http://localhost:3000"
echo "🔗 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; exit 0' INT
wait
