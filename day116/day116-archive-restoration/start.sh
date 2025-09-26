#!/bin/bash
set -euo pipefail

echo "🚀 Starting Archive Restoration System"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run build.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the backend server
echo "🌐 Starting backend server on http://localhost:8000"
cd backend
python -m src.main &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo ""
echo "📊 Dashboard will be available at: http://localhost:8000"
echo "📡 API documentation at: http://localhost:8000/docs"
echo ""
echo "🛑 To stop the system, run: ./stop.sh"
echo "   Or press Ctrl+C to stop"

# Wait for the backend process
wait $BACKEND_PID
