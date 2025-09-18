#!/bin/bash

echo "🛑 Stopping Enterprise Authentication System"

if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    echo "🐳 Stopping Docker services..."
    docker-compose down
else
    echo "🔧 Stopping development services..."
    
    if [ -f .api.pid ]; then
        PID=$(cat .api.pid)
        kill $PID 2>/dev/null || echo "Process $PID not found"
        rm .api.pid
    fi
fi

echo "✅ System stopped"
