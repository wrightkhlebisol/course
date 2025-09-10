#!/bin/bash

echo "🛑 Stopping Multi-Tenant Log Platform"
echo "===================================="

if command -v docker-compose &> /dev/null; then
    echo "🐳 Stopping Docker services..."
    docker-compose down
else
    echo "📦 Stopping individual services..."
    # Kill processes by port
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

echo "✅ All services stopped"
