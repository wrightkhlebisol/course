#!/bin/bash

echo "🎬 Distributed Tracing System Demo"
echo "============================="

# Check if services are running
if ! curl -s http://localhost:8001/ > /dev/null; then
    echo "❌ Services not running. Start with: ./start.sh"
    exit 1
fi

echo "🔍 Testing trace propagation through services..."

# Test 1: Simple user lookup
echo ""
echo "1️⃣  Testing user lookup with trace propagation:"
curl -s -H "X-Trace-Id: demo-trace-001" \
     -H "Content-Type: application/json" \
     http://localhost:8001/users/user123 | jq '.'

sleep 1

# Test 2: Order creation flow
echo ""
echo "2️⃣  Testing order creation flow across services:"
curl -s -X POST \
     -H "X-Trace-Id: demo-trace-002" \
     -H "Content-Type: application/json" \
     -d '{"items":[{"name":"Demo Item","price":19.99}],"total":19.99}' \
     http://localhost:8001/users/user123/orders | jq '.'

sleep 1

# Test 3: Error scenario
echo ""
echo "3️⃣  Testing error handling with trace context:"
curl -s -H "X-Trace-Id: demo-trace-003" \
     http://localhost:8001/users/nonexistent | jq '.'

sleep 1

# Test 4: Get trace data
echo ""
echo "4️⃣  Retrieving trace information:"
curl -s http://localhost:8000/api/traces | jq '.traces[0:3]'

echo ""
echo "✅ Demo completed!"
echo ""
echo "🌐 View real-time traces at: http://localhost:8000"
echo "📊 API Documentation: http://localhost:8001/docs"
