#!/bin/bash

# Start script for Spark Log Analytics

set -e

echo "🚀 Starting Spark Log Analytics..."

# Activate virtual environment
source venv/bin/activate

# Set Spark to use localhost for UI
export SPARK_LOCAL_IP=localhost

# Start API server in background
echo "Starting API server..."
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 &
API_PID=$!
echo $API_PID > .api.pid

# Wait for server to start
sleep 5

# Open dashboard
echo "Opening dashboard..."
if command -v open &> /dev/null; then
    open src/dashboard/index.html
elif command -v xdg-open &> /dev/null; then
    xdg-open src/dashboard/index.html
fi

echo ""
echo "✓ Application started!"
echo ""
echo "API Server: http://localhost:8000"
echo "Dashboard: http://localhost:8000/dashboard"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Run './stop.sh' to stop the application"
