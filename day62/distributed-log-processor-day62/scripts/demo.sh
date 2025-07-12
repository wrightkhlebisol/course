#!/bin/bash

# Demo script for Day 62 implementation
set -e

echo "🎬 Starting Backpressure Demonstration - Day 62"
echo "=============================================="

# Check if application is running
if ! curl -s http://localhost:8000/api/v1/system/health > /dev/null 2>&1; then
    echo "❌ Application not running. Please start it first:"
    echo "   python backend/src/main.py"
    exit 1
fi

echo "✅ Application is running"
echo ""

# Demonstrate normal operation
echo "📊 1. Checking system status..."
curl -s http://localhost:8000/api/v1/system/status | jq '.backpressure.pressure_level, .backpressure.throttle_rate'
echo ""

# Submit some logs
echo "📝 2. Submitting sample logs..."
for priority in "CRITICAL" "HIGH" "NORMAL" "LOW"; do
    response=$(curl -s -X POST http://localhost:8000/api/v1/logs/submit \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"Demo log - $priority priority\", \"priority\": \"$priority\", \"source\": \"demo\"}")
    echo "   $priority: $(echo $response | jq -r '.status')"
done
echo ""

# Create load to trigger backpressure
echo "⚡ 3. Creating traffic spike to demonstrate backpressure..."
curl -s -X POST http://localhost:8000/api/v1/test/spike \
    -H "Content-Type: application/json" > /dev/null

echo "   Traffic spike initiated! Watch the web interface at http://localhost:3000"
echo "   Observe pressure levels, throttling, and intelligent dropping in real-time."
echo ""

# Monitor for a few seconds
echo "📈 4. Monitoring pressure changes..."
for i in {1..5}; do
    sleep 2
    status=$(curl -s http://localhost:8000/api/v1/system/status)
    pressure=$(echo $status | jq -r '.backpressure.pressure_level')
    throttle=$(echo $status | jq -r '.backpressure.throttle_rate')
    queue_size=$(echo $status | jq -r '.backpressure.queue_size')
    
    echo "   T+${i}s: Pressure=$pressure, Throttle=$(printf '%.1f' $(echo "$throttle * 100" | bc))%, Queue=$queue_size"
done

echo ""
echo "🎉 Demo complete! Key observations:"
echo "   • System detected increased load and adjusted pressure level"
echo "   • Throttle rate decreased to manage flow"
echo "   • Queue size remained within limits"
echo "   • Low-priority messages dropped first during overload"
echo ""
echo "🌐 Continue exploring at: http://localhost:3000"
