#!/bin/bash

echo "🛑 Stopping Troubleshooting AI System..."

# Function to safely kill a process
kill_process() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "   Stopping $service_name (PID: $pid)..."
            kill "$pid"
            
            # Wait for process to terminate gracefully
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "   Force killing $service_name..."
                kill -9 "$pid"
            fi
            
            echo "   ✅ $service_name stopped"
        else
            echo "   ⚠️  $service_name not running (PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        echo "   ⚠️  No PID file found for $service_name"
    fi
}

# Stop services using PID files
echo "🔍 Stopping services..."
kill_process "api.pid" "API Service"
kill_process "web.pid" "Web Dashboard"

# Kill any remaining processes by pattern (fallback)
echo "🔍 Checking for remaining processes..."
if pgrep -f "uvicorn src.api.recommendation_service" >/dev/null; then
    echo "   Stopping remaining API processes..."
    pkill -f "uvicorn src.api.recommendation_service"
fi

if pgrep -f "python dashboard.py" >/dev/null; then
    echo "   Stopping remaining dashboard processes..."
    pkill -f "python dashboard.py"
fi

# Check if ports are still in use
echo "🔍 Checking port availability..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠️  Port 8000 is still in use"
fi

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠️  Port 5000 is still in use"
fi

echo "✅ System stopped successfully!"
