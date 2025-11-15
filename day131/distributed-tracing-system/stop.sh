#!/bin/bash

echo "🛑 Stopping Distributed Tracing System"
echo "================================="

# Kill any running Python processes for this app
pkill -f "src/main.py" || true
pkill -f "api_gateway" || true
pkill -f "user_service" || true
pkill -f "database_service" || true
pkill -f "dashboard" || true

# Stop Redis container if running
docker stop redis-tracing 2>/dev/null || true
docker rm redis-tracing 2>/dev/null || true

echo "✅ All services stopped"
