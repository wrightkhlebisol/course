#!/bin/bash

# Stop script for Spark Log Analytics

echo "🛑 Stopping Spark Log Analytics..."

if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    if ps -p $API_PID > /dev/null; then
        echo "Stopping API server (PID: $API_PID)..."
        kill $API_PID
    fi
    rm .api.pid
fi

echo "✓ Application stopped!"
