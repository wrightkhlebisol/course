#!/bin/bash

echo "🎬 Database Audit Collection System Demo"
echo "======================================="

# Activate virtual environment
source venv/bin/activate

echo "1. 🧪 Running unit tests..."
python -m pytest tests/ -v --tb=short

echo ""
echo "2. 🔍 Starting audit collection service..."
python -m uvicorn src.dashboard.dashboard:app --host 0.0.0.0 --port 8080 &
DASHBOARD_PID=$!

echo "⏳ Waiting for dashboard to start..."
sleep 5

echo ""
echo "3. 📊 Testing API endpoints..."
echo "Stats endpoint:"
curl -s http://localhost:8080/api/stats | python -m json.tool

echo ""
echo "Logs endpoint:"
curl -s http://localhost:8080/api/logs | python -m json.tool

echo ""
echo "Threats endpoint:"
curl -s http://localhost:8080/api/threats | python -m json.tool

echo ""
echo "✅ Demo completed successfully!"
echo ""
echo "🌐 Dashboard running at: http://localhost:8080"
echo "🛑 Stop with: kill $DASHBOARD_PID"

# Save PID for cleanup
echo $DASHBOARD_PID > .demo.pid

echo ""
echo "Press Ctrl+C to stop demo..."
wait
