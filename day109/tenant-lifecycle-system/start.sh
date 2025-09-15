#!/bin/bash
set -e

echo "🚀 Starting Tenant Lifecycle Management System"
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

# Start backend server in background
echo "🔄 Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend server is running at http://localhost:8000"
else
    echo "❌ Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend development server
echo "🔄 Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend server starting at http://localhost:5173"
echo ""
echo "🌐 Access the application:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://localhost:8000/api"
echo "  - API Health: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop all servers"

# Save PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for user to stop
trap 'echo "🛑 Stopping servers..."; kill $(cat .backend.pid) $(cat .frontend.pid) 2>/dev/null || true; rm -f .backend.pid .frontend.pid; exit 0' INT

wait
