#!/bin/bash

echo "🚀 Starting Troubleshooting AI System..."

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $port is already in use. Please stop the service using port $port first."
        exit 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    
    if [ -f api.pid ]; then
        API_PID=$(cat api.pid)
        if kill -0 $API_PID 2>/dev/null; then
            kill $API_PID
            echo "   Stopped API service (PID: $API_PID)"
        fi
        rm -f api.pid
    fi
    
    if [ -f web.pid ]; then
        WEB_PID=$(cat web.pid)
        if kill -0 $WEB_PID 2>/dev/null; then
            kill $WEB_PID
            echo "   Stopped Web dashboard (PID: $WEB_PID)"
        fi
        rm -f web.pid
    fi
    
    echo "✅ Cleanup completed"
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGINT SIGTERM

# Check if required ports are available
echo "🔍 Checking port availability..."
check_port 8000
check_port 5000

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Consider activating it for better dependency management."
fi

# Start FastAPI backend
echo "🚀 Starting FastAPI recommendation service..."
uvicorn src.api.recommendation_service:app --host 0.0.0.0 --port 8000 --reload --log-level info &
API_PID=$!

# Save API PID
echo $API_PID > api.pid

# Wait for API to be ready
if ! wait_for_service "http://localhost:8000/health" "API Service"; then
    echo "❌ Failed to start API service"
    cleanup
fi

# Start Flask web dashboard
echo "🌐 Starting web dashboard..."
cd src/web
python dashboard.py &
WEB_PID=$!
cd ../..

# Save Web PID
echo $WEB_PID > web.pid

# Wait for web dashboard to be ready
if ! wait_for_service "http://localhost:5000" "Web Dashboard"; then
    echo "❌ Failed to start web dashboard"
    cleanup
fi

echo ""
echo "🎉 System started successfully!"
echo "=================================="
echo "📊 API Documentation: http://localhost:8000/docs"
echo "🌐 Web Dashboard: http://localhost:5000"
echo "🔍 Health Check: http://localhost:8000/health"
echo "🧪 Test Scripts:"
echo "   python test_functionality.py"
echo "   python demo_execute.py"
echo ""
echo "💡 Press Ctrl+C to stop all services"
echo "=================================="

# Keep script running and monitor services
while true; do
    # Check if services are still running
    if [ -f api.pid ] && ! kill -0 $(cat api.pid) 2>/dev/null; then
        echo "❌ API service has stopped unexpectedly"
        cleanup
    fi
    
    if [ -f web.pid ] && ! kill -0 $(cat web.pid) 2>/dev/null; then
        echo "❌ Web dashboard has stopped unexpectedly"
        cleanup
    fi
    
    sleep 10
done
