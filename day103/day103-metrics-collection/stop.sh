#!/bin/bash

echo "🛑 Stopping Metrics Collection System..."

# Kill backend if PID file exists
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "🔴 Stopped backend server"
    fi
    rm backend.pid
fi

# Kill frontend if PID file exists  
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "🔴 Stopped frontend server"
    fi
    rm frontend.pid
fi

# Stop any remaining processes on the ports
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true

echo "✅ System stopped successfully"
