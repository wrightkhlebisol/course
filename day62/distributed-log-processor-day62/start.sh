#!/bin/bash

# Start script for Distributed Log Processing System - Day 62
set -e

echo "🚀 Starting Distributed Log Processing System - Day 62"
echo "=================================================="

# Fast startup mode (skip some checks for faster startup)
FAST_MODE=${1:-false}
if [ "$FAST_MODE" = "fast" ] || [ "$FAST_MODE" = "--fast" ]; then
    echo "⚡ Fast startup mode enabled - skipping some checks..."
    FAST_MODE=true
else
    FAST_MODE=false
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    local service_name=$2
    if lsof -ti:$port &>/dev/null; then
        echo "⚠️  Port $port ($service_name) is already in use. Cleaning up..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -ti:$port &>/dev/null; then
            echo "❌ Failed to free port $port. Please run './stop.sh' first"
            exit 1
        fi
        echo "✅ Port $port freed up"
    fi
}

# Function to verify dependencies
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found. Please install Python 3.8+"
        exit 1
    fi
    echo "✅ Python3 found: $(python3 --version)"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found. Please install Node.js 16+"
        exit 1
    fi
    echo "✅ Node.js found: $(node --version)"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        echo "❌ npm not found. Please install npm"
        exit 1
    fi
    echo "✅ npm found: $(npm --version)"
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        echo "❌ curl not found. Please install curl"
        exit 1
    fi
    
    # Check if backend dependencies are installed
    if [ ! -d "backend/src/__pycache__" ] && [ ! -f "backend/.venv/pyvenv.cfg" ]; then
        echo "⚠️  Backend dependencies may not be installed"
        echo "🔧 Installing backend dependencies..."
        cd backend
        pip3 install -r requirements.txt || {
            echo "❌ Failed to install backend dependencies"
            exit 1
        }
        cd ..
        echo "✅ Backend dependencies installed"
    fi
    
    # Check if frontend is built
    if [ ! -d "frontend/build" ]; then
        echo "⚠️  Frontend not built"
        echo "🔧 Building frontend..."
        cd frontend
        npm install || {
            echo "❌ Failed to install frontend dependencies"
            exit 1
        }
        npm run build || {
            echo "❌ Failed to build frontend"
            exit 1
        }
        cd ..
        echo "✅ Frontend built successfully"
    fi
    
    echo "✅ All dependencies verified"
}

# Function to setup environment
setup_environment() {
    echo "🌍 Setting up environment..."
    
    # Create logs directory if it doesn't exist
    mkdir -p backend/logs
    
    # Set environment variables
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend/src"
    export NODE_ENV=production
    
    # Create .env file if it doesn't exist
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << EOF
# Environment Configuration
DEBUG=False
LOG_LEVEL=INFO
PORT=8000
HOST=0.0.0.0

# Performance Settings
MAX_WORKERS=4
QUEUE_SIZE=1000
BATCH_SIZE=100

# Monitoring
METRICS_ENABLED=True
METRICS_PORT=9000
EOF
        echo "✅ Created backend/.env file"
    fi
    
    echo "✅ Environment setup complete"
}

# Function to start Docker services (if available)
start_docker_services() {
    if [ -f "docker-compose.yml" ] && command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        echo "🐳 Starting Docker services..."
        docker-compose up -d --build || {
            echo "⚠️  Docker services failed to start, continuing with local services"
            return 1
        }
        echo "✅ Docker services started"
        return 0
    fi
    return 1
}

# Function to wait for service health
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-30}
    
    echo "⏳ Waiting for $service_name to be ready..."
    local attempt=0
    local delay=0.2  # Start with 200ms delay
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --connect-timeout 2 --max-time 3 "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready (attempt $((attempt + 1)))"
            return 0
        fi
        
        attempt=$((attempt + 1))
        
        # Exponential backoff with cap
        if [ $attempt -le 5 ]; then
            sleep $delay
        elif [ $attempt -le 10 ]; then
            sleep 0.5
        else
            sleep 1
        fi
        
        # Increase delay for next attempt
        delay=$(echo "$delay * 1.2" | bc -l | cut -d. -f1-2)
        
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service_name failed to start properly (tried $max_attempts times)"
            return 1
        fi
    done
}

# Pre-flight checks
if [ "$FAST_MODE" = true ]; then
    echo "⚡ Fast mode: Skipping dependency checks..."
    setup_environment
else
    echo "🔧 Running pre-flight checks..."
    check_dependencies
    setup_environment
fi

# Check and free up ports
echo ""
echo "🔧 Checking and freeing up ports..."
check_port 3000 "Frontend"
check_port 8000 "Backend API"
check_port 9000 "Metrics"

# Try Docker first, fall back to local services
echo ""
if start_docker_services; then
    echo "🐳 Using Docker services"
    
    # Wait for Docker services to be ready
    wait_for_service "http://localhost:8000/api/v1/system/health" "Backend (Docker)" 60
    wait_for_service "http://localhost:3000" "Frontend (Docker)" 30
    
else
    echo "🏠 Starting local services..."
    
    # Check if services are already running
    if pgrep -f "python3.*main.py" > /dev/null; then
        echo "⚠️  Backend already running"
    else
        echo "🐍 Starting backend server..."
        cd backend
        nohup python3 src/main.py > logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > ../backend.pid
        cd ..
        echo "✅ Backend started (PID: $BACKEND_PID)"
    fi

    # Wait for backend to be ready (reduced timeout since backend starts quickly)
    if ! wait_for_service "http://localhost:8000/api/v1/system/health" "Backend" 15; then
        echo "❌ Backend health check failed"
        exit 1
    fi

    # Check if frontend is already running
    if pgrep -f "serve.*build" > /dev/null; then
        echo "⚠️  Frontend already running"
    else
        echo "🎨 Starting frontend server..."
        cd frontend
        
        # Install serve if not available
        if ! command -v npx &> /dev/null || ! npx serve --version &> /dev/null; then
            echo "🔧 Installing serve..."
            npm install -g serve || npm install serve
        fi
        
        nohup npx serve -s build -l 3000 > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid
        cd ..
        echo "✅ Frontend started (PID: $FRONTEND_PID)"
    fi

    # Wait for frontend to be ready (reduced timeout)
    wait_for_service "http://localhost:3000" "Frontend" 15
fi

# Start monitoring/metrics if available
echo ""
echo "📊 Starting monitoring services..."
if [ -f "backend/src/utils/metrics.py" ]; then
    if ! pgrep -f "metrics" > /dev/null; then
        echo "📈 Starting metrics collection..."
        # Metrics are typically integrated into the main backend service
        echo "✅ Metrics integrated with backend service"
    fi
fi

# Final health checks
echo ""
echo "🏥 Running final health checks..."
services_healthy=true

# Check backend health
if curl -s http://localhost:8000/api/v1/system/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    services_healthy=false
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend health check passed"
else
    echo "❌ Frontend health check failed"
    services_healthy=false
fi

# Show system status
echo ""
echo "📋 System Status Summary:"
echo "========================="

# Backend status
backend_status="❌ Not Running"
if pgrep -f "python3.*main.py" > /dev/null || curl -s http://localhost:8000/api/v1/system/status > /dev/null 2>&1; then
    backend_status="✅ Running"
fi
echo "Backend API:     $backend_status"

# Frontend status  
frontend_status="❌ Not Running"
if pgrep -f "serve.*build" > /dev/null || curl -s http://localhost:3000 > /dev/null 2>&1; then
    frontend_status="✅ Running"
fi
echo "Frontend:        $frontend_status"

# Docker status
docker_status="❌ Not Running"
if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        docker_status="✅ Running"
    fi
fi
echo "Docker Services: $docker_status"

# Port status
echo ""
echo "🌐 Service Endpoints:"
echo "===================="
echo "   • Web Interface:     http://localhost:3000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • System Status:     http://localhost:8000/api/v1/system/status"
echo "   • Health Check:      http://localhost:8000/api/v1/system/health"

if curl -s http://localhost:9000 > /dev/null 2>&1; then
    echo "   • Metrics:           http://localhost:9000/metrics"
fi

echo ""
if [ "$services_healthy" = true ]; then
    echo "🎉 All services started successfully!"
    echo ""
    echo "🎯 Quick Actions:"
    echo "   🎬 Run './scripts/demo.sh' to see backpressure mechanisms in action!"
    echo "   📊 Monitor system performance at http://localhost:3000"
    echo "   🔧 View API docs at http://localhost:8000/docs"
    echo "   🛑 Run './stop.sh' to stop all services"
    echo ""
    echo "📝 Log Files:"
    echo "   • Backend: backend/logs/backend.log"
    echo "   • Frontend: frontend.log"
else
    echo "⚠️  Some services failed to start properly"
    echo "🔍 Check log files for details:"
    echo "   • Backend: backend/logs/backend.log"
    echo "   • Frontend: frontend.log"
    echo ""
    echo "🛠️  Troubleshooting:"
    echo "   1. Run './stop.sh' to clean up"
    echo "   2. Check if ports 3000, 8000 are free"
    echo "   3. Verify dependencies with 'python3 --version' and 'node --version'"
    echo "   4. Try running './start.sh' again"
    exit 1
fi 