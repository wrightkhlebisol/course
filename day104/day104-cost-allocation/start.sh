#!/bin/bash

echo "🚀 Starting Cost Allocation System..."

# Activate virtual environment
source venv/bin/activate

# Create necessary directories
mkdir -p data/reports logs

# Start Redis (if not running)
if ! pgrep -f "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
fi

# Start the API server
echo "Starting Cost Allocation API..."
cd src && python -m api.cost_api &
API_PID=$!

# Wait for API to start
sleep 5

# Install frontend dependencies and start development server
echo "Starting frontend development server..."
cd src/frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm start &
FRONTEND_PID=$!

echo "✅ Cost Allocation System started successfully!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8104"
echo "📋 API Docs: http://localhost:8104/docs"

# Store PIDs for cleanup
echo $API_PID > ../../.api.pid
echo $FRONTEND_PID > ../../.frontend.pid

echo "Press Ctrl+C to stop all services"
wait
