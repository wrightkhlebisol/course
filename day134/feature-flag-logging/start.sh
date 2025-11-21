#!/bin/bash

set -e

echo "🚀 Starting Feature Flag Status Logging System"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./build.sh first."
    exit 1
fi

# Start services with Docker Compose
echo "🐳 Starting infrastructure services (PostgreSQL, Redis, RabbitMQ)..."
docker-compose up -d postgres redis rabbitmq

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🏥 Checking service health..."
docker-compose ps

# Activate virtual environment and start backend
echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "🖥️  Starting backend server..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start frontend
echo "⚛️  Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started successfully!"
echo ""
echo "🌐 Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo ""
echo "🛑 To stop all services: ./stop.sh"

# Save PIDs for stop script
echo $BACKEND_PID > .backend_pid
echo $FRONTEND_PID > .frontend_pid

# Wait for user input
echo "Press Ctrl+C to stop all services..."
wait
