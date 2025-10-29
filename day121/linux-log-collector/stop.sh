#!/bin/bash

echo "🛑 Stopping Linux Log Collector..."

# Stop Docker containers
docker-compose down

# Kill any running Python processes
pkill -f "src.collector.main" || true

echo "✅ Collector stopped"
