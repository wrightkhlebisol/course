#!/bin/bash

echo "🔍 Troubleshooting AI System Status"
echo "=================================="

# Check if PID files exist
echo "📋 Process Status:"
if [ -f api.pid ]; then
    API_PID=$(cat api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "   ✅ API Service: Running (PID: $API_PID)"
    else
        echo "   ❌ API Service: Not running (stale PID file)"
    fi
else
    echo "   ⚠️  API Service: No PID file found"
fi

if [ -f web.pid ]; then
    WEB_PID=$(cat web.pid)
    if kill -0 $WEB_PID 2>/dev/null; then
        echo "   ✅ Web Dashboard: Running (PID: $WEB_PID)"
    else
        echo "   ❌ Web Dashboard: Not running (stale PID file)"
    fi
else
    echo "   ⚠️  Web Dashboard: No PID file found"
fi

# Check port availability
echo ""
echo "🌐 Port Status:"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ✅ Port 8000: In use (API Service)"
else
    echo "   ❌ Port 8000: Not in use"
fi

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ✅ Port 5000: In use (Web Dashboard)"
else
    echo "   ❌ Port 5000: Not in use"
fi

# Test API endpoints
echo ""
echo "🔗 API Health Check:"
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "   ✅ API Health: OK"
    
    # Test stats endpoint
    if curl -s http://localhost:8000/api/stats >/dev/null 2>&1; then
        echo "   ✅ API Stats: OK"
    else
        echo "   ❌ API Stats: Failed"
    fi
else
    echo "   ❌ API Health: Failed"
fi

# Test web dashboard
echo ""
echo "🌐 Web Dashboard Check:"
if curl -s http://localhost:5000 >/dev/null 2>&1; then
    echo "   ✅ Web Dashboard: Accessible"
else
    echo "   ❌ Web Dashboard: Not accessible"
fi

# Show access URLs
echo ""
echo "🔗 Access URLs:"
echo "   📊 API Documentation: http://localhost:8000/docs"
echo "   🌐 Web Dashboard: http://localhost:5000"
echo "   🔍 Health Check: http://localhost:8000/health"

# Show test commands
echo ""
echo "🧪 Test Commands:"
echo "   python test_functionality.py"
echo "   python demo_execute.py"

echo ""
echo "==================================" 