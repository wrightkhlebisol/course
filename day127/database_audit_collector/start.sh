#!/bin/bash

echo "🚀 Starting Database Audit Collection System"
echo "============================================"

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to project root for imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start dashboard in background
echo "🌐 Starting web dashboard..."
python -m uvicorn src.dashboard.dashboard:app --host 0.0.0.0 --port 8080 &
DASHBOARD_PID=$!

# Start main collector service
echo "🔍 Starting audit collector..."
python src/main.py &
COLLECTOR_PID=$!

echo "✅ Services started successfully!"
echo ""
echo "📊 Dashboard: http://localhost:8080"
echo "🛑 Stop with: ./stop.sh"
echo ""

# Save PIDs for stop script
echo $DASHBOARD_PID > .dashboard.pid
echo $COLLECTOR_PID > .collector.pid

wait
