#!/bin/bash

echo "🛑 Stopping Feature Flag Status Logging System"
echo "============================================="

# Stop backend process
if [ -f ".backend_pid" ]; then
    BACKEND_PID=$(cat .backend_pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🔌 Stopping backend server..."
        kill $BACKEND_PID
    fi
    rm .backend_pid
fi

# Stop frontend process
if [ -f ".frontend_pid" ]; then
    FRONTEND_PID=$(cat .frontend_pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "⚛️  Stopping frontend server..."
        kill $FRONTEND_PID
    fi
    rm .frontend_pid
fi

# Stop Docker services
echo "🐳 Stopping Docker services..."
docker-compose down

echo "✅ All services stopped successfully!"
