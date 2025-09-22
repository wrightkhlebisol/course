#!/bin/bash
set -e

echo "🎬 Data Lifecycle Policy Engine Demo"
echo "=================================="

# Activate virtual environment
source venv/bin/activate

# Start backend
echo "Starting backend..."
python -m src.backend.api.main &
BACKEND_PID=$!

sleep 5

# Generate demo data
echo "Generating sample log data..."
curl -s -X POST "http://localhost:8000/api/generate-logs?count=100" | jq

# Show tier statistics
echo -e "\n📊 Current tier statistics:"
curl -s http://localhost:8000/api/tier-stats | jq

# Show active policies
echo -e "\n📋 Active policies:"
curl -s http://localhost:8000/api/policies | jq '[.[] | {name: .name, log_type: .log_type, enabled: .enabled}]'

# Show compliance report
echo -e "\n📈 Compliance report:"
curl -s http://localhost:8000/api/compliance-report | jq

echo -e "\n✅ Demo completed!"
echo "🌐 Open http://localhost:8000 in your browser to see the dashboard"
echo "Press Ctrl+C to stop the demo"

wait $BACKEND_PID
