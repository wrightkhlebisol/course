#!/bin/bash

echo "🛑 Stopping Slack Integration System"
echo "===================================="

# Kill backend processes
pkill -f "python -m src.backend.main" || pkill -f "uvicorn" || true

# Kill frontend processes  
pkill -f "npx serve" || pkill -f "serve -s" || true

# Stop Redis if running
redis-cli shutdown 2>/dev/null || true

echo "✅ All services stopped"
