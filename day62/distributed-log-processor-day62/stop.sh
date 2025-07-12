#!/bin/bash

# Stop script for Distributed Log Processing System - Day 62
set -e

echo "🛑 Stopping Distributed Log Processing System - Day 62"
echo "================================================="

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🔄 Stopping $service_name (PID: $PID)..."
            kill -TERM "$PID" 2>/dev/null || true
            
            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$PID" 2>/dev/null; then
                    echo "✅ $service_name stopped gracefully"
                    break
                fi
                sleep 1
                if [ $i -eq 10 ]; then
                    echo "⚠️  Force stopping $service_name..."
                    kill -KILL "$PID" 2>/dev/null || true
                fi
            done
        else
            echo "⚠️  $service_name PID file exists but process not running"
        fi
        rm -f "$pid_file"
    else
        echo "ℹ️  $service_name PID file not found"
    fi
}

# Function to kill processes on specific ports
kill_port_processes() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Checking for processes on port $port ($service_name)..."
    
    # Find processes using the port
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "🔄 Killing processes on port $port: $pids"
        for pid in $pids; do
            kill -TERM "$pid" 2>/dev/null || true
            sleep 1
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
        echo "✅ Cleaned up port $port"
    else
        echo "ℹ️  No processes found on port $port"
    fi
}

# Stop backend
stop_service "Backend" "backend.pid"

# Stop frontend
stop_service "Frontend" "frontend.pid"

# Kill processes on common ports used by the application
echo ""
echo "🧹 Cleaning up processes on common ports..."
kill_port_processes 3000 "Frontend (React)"
kill_port_processes 8000 "Backend (FastAPI)"
kill_port_processes 5000 "Backend (Flask)"
kill_port_processes 8080 "Alternative Backend"
kill_port_processes 3001 "Alternative Frontend"
kill_port_processes 9000 "Monitoring/Metrics"

# Also kill any remaining processes by name (backup cleanup)
echo ""
echo "🧹 Cleaning up any remaining processes..."

# Kill any remaining backend processes
if pgrep -f "python3.*main.py" > /dev/null; then
    echo "🔄 Cleaning up remaining backend processes..."
    pkill -f "python3.*main.py" 2>/dev/null || true
fi

# Kill any remaining frontend processes
if pgrep -f "serve.*build" > /dev/null; then
    echo "🔄 Cleaning up remaining frontend processes..."
    pkill -f "serve.*build" 2>/dev/null || true
fi

# Kill any npm/node processes related to the project
if pgrep -f "npm.*start\|node.*start\|react-scripts" > /dev/null; then
    echo "🔄 Cleaning up remaining npm/node processes..."
    pkill -f "npm.*start\|node.*start\|react-scripts" 2>/dev/null || true
fi

# Kill any uvicorn processes
if pgrep -f "uvicorn" > /dev/null; then
    echo "🔄 Cleaning up remaining uvicorn processes..."
    pkill -f "uvicorn" 2>/dev/null || true
fi

# Stop Docker containers if any are running
echo ""
echo "🐳 Cleaning up Docker containers..."
if command -v docker &> /dev/null; then
    # Stop containers from docker-compose
    if [ -f "docker-compose.yml" ]; then
        echo "🔄 Stopping docker-compose services..."
        docker-compose down 2>/dev/null || true
    fi
    
    # Stop any containers that might be running from this project
    containers=$(docker ps -q --filter "label=project=distributed-log-processor" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        echo "🔄 Stopping project-related containers..."
        docker stop $containers 2>/dev/null || true
        docker rm $containers 2>/dev/null || true
    fi
    
    # Stop any containers with our image names
    our_containers=$(docker ps -q --filter "ancestor=distributed-log-processor-backend" --filter "ancestor=distributed-log-processor-frontend" 2>/dev/null || true)
    if [ -n "$our_containers" ]; then
        echo "🔄 Stopping containers with our images..."
        docker stop $our_containers 2>/dev/null || true
        docker rm $our_containers 2>/dev/null || true
    fi
else
    echo "ℹ️  Docker not found, skipping container cleanup"
fi

# Clean up log files
echo ""
echo "🧹 Cleaning up log files..."
if [ -f "frontend.log" ]; then
    rm -f "frontend.log"
    echo "✅ Removed frontend.log"
fi

if [ -f "backend.log" ]; then
    rm -f "backend.log"
    echo "✅ Removed backend.log"
fi

# Clean up any other temporary files
if [ -d "backend/logs" ]; then
    rm -rf "backend/logs"/*.log 2>/dev/null || true
    echo "✅ Cleaned up backend log files"
fi

# Final comprehensive cleanup - kill any remaining processes that might be related
echo ""
echo "🔥 Final cleanup - killing any remaining related processes..."

# Kill any processes that might be using our project directory
project_processes=$(pgrep -f "$(pwd)" 2>/dev/null || true)
if [ -n "$project_processes" ]; then
    echo "🔄 Killing processes using project directory..."
    for pid in $project_processes; do
        # Skip our own process
        if [ "$pid" != "$$" ]; then
            kill -TERM "$pid" 2>/dev/null || true
            sleep 1
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
    done
fi

# Show what's still running on our common ports (for verification)
echo ""
echo "🔍 Final port check..."
for port in 3000 8000 5000 8080 3001 9000; do
    if lsof -ti:$port &>/dev/null; then
        echo "⚠️  Port $port still has processes running:"
        lsof -ti:$port | head -5
    fi
done

echo ""
echo "✅ All services stopped successfully!"
echo "🧹 All processes cleaned up!"
echo "🚀 Ports freed up!"
echo ""
echo "🚀 Run './start.sh' to restart the system" 