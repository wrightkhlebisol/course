#!/bin/bash

echo "🛑 Stopping S3 Export System"

# Kill Python processes
pkill -f "python src/main.py" || true

# Stop Docker if running
docker-compose down 2>/dev/null || true

echo "✅ System stopped"
