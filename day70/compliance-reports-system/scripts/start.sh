#!/bin/bash

echo "🚀 Starting Compliance Reports System"
echo "====================================="

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up --build -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 15
    
    echo "✅ System started with Docker"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔌 Backend API: http://localhost:8000"
    echo "📊 API Docs: http://localhost:8000/docs"
    
else
    echo "🔧 Starting services manually..."
    
    # Start backend
    echo "Starting backend..."
    cd backend
    source venv/bin/activate
    python app/main.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend
    sleep 5
    
    # Start frontend
    echo "Starting frontend..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo "✅ System started manually"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔌 Backend API: http://localhost:8000"
    
    # Save PIDs for cleanup
    echo $BACKEND_PID > .backend.pid
    echo $FRONTEND_PID > .frontend.pid
fi

echo "🎬 Running system demo..."
sleep 5
python scripts/demo.py
