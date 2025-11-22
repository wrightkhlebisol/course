#!/bin/bash

echo "🧪 Running Comprehensive Test Suite"
echo "===================================="

source venv/bin/activate
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "1️⃣  Running unit tests..."
python -m pytest tests/unit/ -v

echo ""
echo "2️⃣  Running integration tests..."
python -m pytest tests/integration/ -v

echo ""
echo "3️⃣  Running load tests..."
python -m pytest tests/load/ -v

echo ""
echo "4️⃣  Testing API endpoints..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Health endpoint working"
    curl -s http://localhost:8000/api/v1/health | python -m json.tool
else
    echo "❌ Health endpoint not accessible"
fi

echo ""
echo "5️⃣  Testing alert creation..."
TIMESTAMP=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat())")
curl -X POST http://localhost:8000/api/v1/alerts \
    -H "Content-Type: application/json" \
    -d "{
        \"title\": \"Test Alert from Script\",
        \"description\": \"Automated test alert\",
        \"source\": \"application\",
        \"severity\": \"medium\", 
        \"service_name\": \"test-service\",
        \"timestamp\": \"$TIMESTAMP\"
    }" | python -m json.tool

echo ""
echo "✅ All tests completed!"
