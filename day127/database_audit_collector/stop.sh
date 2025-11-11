#!/bin/bash

echo "🛑 Stopping Database Audit Collection System"
echo "============================================"

# Kill processes if PID files exist
if [ -f .dashboard.pid ]; then
    DASHBOARD_PID=$(cat .dashboard.pid)
    echo "Stopping dashboard (PID: $DASHBOARD_PID)..."
    kill $DASHBOARD_PID 2>/dev/null
    rm .dashboard.pid
fi

if [ -f .collector.pid ]; then
    COLLECTOR_PID=$(cat .collector.pid)
    echo "Stopping collector (PID: $COLLECTOR_PID)..."
    kill $COLLECTOR_PID 2>/dev/null
    rm .collector.pid
fi

# Also kill any remaining processes
pkill -f "uvicorn src.dashboard.dashboard:app"
pkill -f "python src/main.py"

echo "✅ All services stopped"
