#!/bin/bash

echo "🛑 Stopping Day 146 services..."

if command -v docker &> /dev/null; then
    docker-compose down
else
    # Kill processes by port
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

echo "✅ Services stopped!"
