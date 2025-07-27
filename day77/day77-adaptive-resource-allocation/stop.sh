#!/bin/bash

echo "🛑 Stopping Adaptive Resource Allocation System"

# Kill processes
pkill -f "python src/main.py"
pkill -f "python scripts/demo.py"

# Stop Docker containers if running
docker-compose down 2>/dev/null || true

echo "✅ System stopped"
