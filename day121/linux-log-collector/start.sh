#!/bin/bash
set -e

# Kill any existing collector/receiver processes
pkill -f "python -m src.collector.main" 2>/dev/null || true
pkill -f "python mock-server/server.py" 2>/dev/null || true
pkill -f "uvicorn.*dashboard" 2>/dev/null || true
sleep 1

echo "🚀 Starting Linux Log Collector..."

# Check if running in Docker
if [ "$1" == "docker" ]; then
    echo "Starting with Docker Compose..."
    docker-compose up -d
    echo "✅ Collector started!"
    echo "📊 Dashboard: http://localhost:8000"
    echo "📈 Metrics: http://localhost:9090"
    echo ""
    echo "View logs with: docker-compose logs -f collector"
else
    echo "Starting with Python..."
    if [ ! -d "venv" ]; then
        echo "❌ Virtual environment not found. Run ./build.sh first"
        exit 1
    fi
    
    source venv/bin/activate
    export PYTHONPATH="${PYTHONPATH}:$PWD/src"
    
    # Start mock log receiver in background  
    echo "Starting Mock Log Receiver on port 8080..."
    nohup python mock-server/server.py > /tmp/receiver.log 2>&1 &
    RECEIVER_PID=$!
    
    # Give receiver time to start
    sleep 3
    
    # Check if receiver is actually running and responding
    if ! ps -p $RECEIVER_PID > /dev/null 2>&1; then
        echo "❌ Mock receiver failed to start"
        cat /tmp/receiver.log
        exit 1
    fi
    
    # Test that receiver is responding
    if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "❌ Mock receiver not responding on port 8080"
        cat /tmp/receiver.log
        kill $RECEIVER_PID 2>/dev/null || true
        exit 1
    fi
    
    # Start collector in foreground so we can monitor it
    echo "✅ Mock Receiver started (PID: $RECEIVER_PID)"
    echo "✅ Starting collector..."
    echo "📊 Dashboard: http://localhost:8000"
    echo "📥 Receiver API: http://localhost:8080"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""
    
    
    # Cleanup function
    cleanup() {
        echo ""
        echo "Shutting down..."
        if [ -f /tmp/receiver.pid ]; then
            RECEIVER_PID=$(cat /tmp/receiver.pid)
            kill $RECEIVER_PID 2>/dev/null || true
            rm -f /tmp/receiver.pid
        fi
        exit 0
    }
    
    # Set trap to cleanup on exit
    trap cleanup SIGINT SIGTERM
    
    # Start collector - this will run in foreground
    python -m src.collector.main
fi
