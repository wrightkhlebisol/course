#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛑 Stopping Incident Management System..."

# Kill uvicorn process
if pgrep -f "uvicorn.*src.main:app" > /dev/null; then
    pkill -f "uvicorn.*src.main:app"
    echo "✅ FastAPI server stopped"
else
    echo "⚠️  No FastAPI server process found"
fi

# Stop Redis if it was started by us
if pgrep -x "redis-server" > /dev/null; then
    if command -v redis-cli &> /dev/null; then
        redis-cli shutdown 2>/dev/null || pkill -x redis-server
        echo "✅ Redis stopped"
    else
        pkill -x redis-server
        echo "✅ Redis stopped"
    fi
else
    echo "⚠️  Redis not running"
fi

echo "✅ All services stopped"
