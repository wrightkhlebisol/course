#!/bin/bash

echo "🚀 Starting Storage Optimization System"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found. Run ./build.sh first."
    exit 1
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
source venv/bin/activate
python src/main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend
echo "🌐 Starting frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "✅ System started successfully!"
echo ""
echo "🌐 Dashboard: http://localhost:3000"
echo "📡 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT
wait
