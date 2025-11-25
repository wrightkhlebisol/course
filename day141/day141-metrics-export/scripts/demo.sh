#!/bin/bash
set -e

echo "🎬 Day 141 Metrics Export - System Demonstration"
echo "================================================"

source venv/bin/activate

# Start application in background
python -m src.main &
APP_PID=$!

echo "⏳ Waiting for application to start..."
sleep 5

echo ""
echo "1️⃣ Testing Health Endpoint"
echo "============================="
curl -s http://localhost:8000/health | python -m json.tool

echo ""
echo "2️⃣ Fetching Current Statistics"
echo "================================"
curl -s http://localhost:8000/api/stats | python -m json.tool

echo ""
echo "3️⃣ Viewing Prometheus Metrics"
echo "==============================="
curl -s http://localhost:8000/metrics | head -n 30

echo ""
echo "4️⃣ Triggering Manual Export"
echo "============================"
curl -s -X POST http://localhost:8000/api/trigger-export | python -m json.tool

echo ""
echo "✅ Demonstration Complete!"
echo ""
echo "📊 View Dashboard: http://localhost:8000/dashboard"
echo "📈 View Metrics: http://localhost:8000/metrics"
echo ""

# Keep running for dashboard access
echo "Application running... Press Ctrl+C to stop"
trap "kill $APP_PID; exit" INT TERM
wait $APP_PID
