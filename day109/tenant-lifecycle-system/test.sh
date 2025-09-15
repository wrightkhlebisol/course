#!/bin/bash
set -e

echo "🧪 Running Comprehensive Tests"
echo "============================="

# Activate virtual environment
source venv/bin/activate

# Run Python unit tests
echo "1. Running Python unit tests..."
python -m pytest tests/ -v --tb=short
echo "✅ Unit tests passed"

# Build frontend to check for errors
echo "2. Testing frontend build..."
cd frontend
npm run build
echo "✅ Frontend build successful"
cd ..

# Start services for integration testing
echo "3. Starting services for integration tests..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

sleep 5

# Test API endpoints
echo "4. Testing API endpoints..."

# Health check
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "   ✅ Health endpoint working"
else
    echo "   ❌ Health endpoint failed"
    kill $BACKEND_PID
    exit 1
fi

# Test tenant onboarding
echo "   🧪 Testing tenant onboarding..."
TENANT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/tenants/onboard \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Org","email":"test@example.com","plan":"basic"}')

if echo $TENANT_RESPONSE | grep -q "tenant_id"; then
    echo "   ✅ Tenant onboarding working"
    TENANT_ID=$(echo $TENANT_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['tenant_id'])")
else
    echo "   ❌ Tenant onboarding failed"
    kill $BACKEND_PID
    exit 1
fi

# Test tenant listing
echo "   🧪 Testing tenant listing..."
if curl -s http://localhost:8000/api/tenants | grep -q "$TENANT_ID"; then
    echo "   ✅ Tenant listing working"
else
    echo "   ❌ Tenant listing failed"
    kill $BACKEND_PID
    exit 1
fi

# Test dashboard stats
echo "   🧪 Testing dashboard stats..."
if curl -s http://localhost:8000/api/stats/dashboard | grep -q "total_tenants"; then
    echo "   ✅ Dashboard stats working"
else
    echo "   ❌ Dashboard stats failed"
    kill $BACKEND_PID
    exit 1
fi

# Cleanup
kill $BACKEND_PID
echo ""
echo "🎉 All tests passed successfully!"
echo "✅ System is ready for production use"
