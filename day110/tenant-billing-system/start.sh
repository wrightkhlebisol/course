#!/bin/bash

echo "🚀 Starting Tenant Usage Reporting & Billing System"
echo "================================================="

# Activate virtual environment
source venv/bin/activate

echo "🖥️ Starting backend server..."
cd backend
python src/api.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

echo "🌐 Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ System started successfully!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 To stop: ./stop.sh"

# Keep script running
wait
