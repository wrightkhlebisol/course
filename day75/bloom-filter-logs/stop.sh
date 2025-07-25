#!/bin/bash

echo "🛑 Stopping Bloom Filter Log Processing System"
echo "=============================================="

# Stop API server
if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "🌐 Stopping API server (PID: $API_PID)..."
        kill $API_PID
        rm .api.pid
    fi
fi

# Stop dashboard
if [ -f .dashboard.pid ]; then
    DASHBOARD_PID=$(cat .dashboard.pid)
    if kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo "📊 Stopping dashboard (PID: $DASHBOARD_PID)..."
        kill $DASHBOARD_PID
        rm .dashboard.pid
    fi
fi

# Kill any remaining processes on our ports
echo "🧹 Cleaning up any remaining processes..."
pkill -f "uvicorn.*8001" 2>/dev/null || true
pkill -f "dashboard.py" 2>/dev/null || true

if [[ "$1" == "--docker" ]]; then
    echo "🐳 Stopping Docker Compose services..."
    docker-compose down
    echo "✅ All Docker services stopped"
    exit 0
fi

echo "✅ All services stopped"
