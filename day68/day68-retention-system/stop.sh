#!/bin/bash

echo "🛑 Stopping Day 68: Data Retention System"
echo "========================================="

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🛑 Stopping $service_name (PID: $pid)..."
            kill -TERM "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "⚠️ Force killing $service_name..."
                kill -KILL "$pid"
            fi
            
            echo "✅ $service_name stopped"
        else
            echo "ℹ️ $service_name not running"
        fi
        rm -f "$pid_file"
    else
        echo "ℹ️ No PID file found for $service_name"
    fi
}

# Stop backend
stop_service "Backend API" "logs/backend.pid"

# Stop frontend
stop_service "Frontend" "logs/frontend.pid"

# Clean up any remaining processes
echo "🧹 Cleaning up any remaining processes..."
pkill -f "python src/main.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

echo ""
echo "✅ All services stopped successfully!"
echo "=====================================" 