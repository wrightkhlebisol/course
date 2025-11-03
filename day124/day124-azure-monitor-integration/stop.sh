#!/bin/bash

echo "⏹️ Stopping Azure Monitor Integration"
echo "===================================="

# Kill any running processes
pkill -f "python.*main.py web" || true
pkill -f "uvicorn" || true

# Stop Docker containers
docker-compose down 2>/dev/null || true

echo "✅ All services stopped"
