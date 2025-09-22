#!/bin/bash
set -e

echo "🚀 Starting Data Lifecycle Policy Engine..."

# Activate virtual environment
source venv/bin/activate

# Start backend server
echo "Starting backend server on port 8000..."
python -m src.backend.api.main &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/tier-stats > /dev/null; then
    echo "✅ Backend started successfully"
    echo "🌐 Dashboard available at: http://localhost:8000"
    echo "📊 API available at: http://localhost:8000/api/"
else
    echo "❌ Backend failed to start"
    exit 1
fi

echo "Press Ctrl+C to stop the server"
wait $BACKEND_PID
