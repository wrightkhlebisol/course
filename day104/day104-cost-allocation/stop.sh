#!/bin/bash

echo "🛑 Stopping Cost Allocation System..."

# Kill API server
if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    kill $API_PID 2>/dev/null
    rm .api.pid
fi

# Kill frontend server
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
fi

# Stop Redis
redis-cli shutdown 2>/dev/null

echo "✅ All services stopped"
