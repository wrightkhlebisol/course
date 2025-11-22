#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "🚀 Starting Incident Management System..."
echo "Working directory: $SCRIPT_DIR"

# Check if Redis is already running
if pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis is already running"
else
    # Start Redis in background
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes
        echo "✅ Redis started"
    else
        echo "⚠️  Redis not found, continuing without it"
    fi
fi

# Check if uvicorn is already running
if pgrep -f "uvicorn.*src.main:app" > /dev/null; then
    echo "⚠️  Application is already running (PID: $(pgrep -f 'uvicorn.*src.main:app'))"
    echo "   Use ./stop.sh to stop it first"
    exit 1
fi

# Activate virtual environment and start FastAPI
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
    exit 1
fi

source "$SCRIPT_DIR/venv/bin/activate"
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Start FastAPI server
echo "Starting FastAPI server..."
cd "$SCRIPT_DIR" || exit 1
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > "$SCRIPT_DIR/logs/server.log" 2>&1 &
SERVER_PID=$!

echo "⏳ Waiting for services to start..."
sleep 5

# Check if server started successfully
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Services started successfully! (PID: $SERVER_PID)"
    echo ""
    echo "🌐 Dashboard: http://localhost:8000"
    echo "📊 Health Check: http://localhost:8000/api/v1/health"
    echo "📋 Metrics: http://localhost:8000/api/v1/metrics"
    echo ""
    echo "Stop with: ./stop.sh"
    echo "View logs: tail -f $SCRIPT_DIR/logs/server.log"
else
    echo "❌ Failed to start server. Check logs: $SCRIPT_DIR/logs/server.log"
    exit 1
fi
