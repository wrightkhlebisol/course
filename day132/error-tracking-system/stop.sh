#!/bin/bash

echo "🛑 Stopping Error Tracking System..."

if [ "$1" = "docker" ]; then
    docker-compose down
else
    # Kill processes by port
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

echo "✅ Services stopped!"
