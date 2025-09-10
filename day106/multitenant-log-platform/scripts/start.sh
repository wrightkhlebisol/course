#!/bin/bash

echo "🚀 Starting Multi-Tenant Log Platform"
echo "====================================="

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Using Docker Compose..."
    docker-compose up --build -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 15
    
    echo "✅ Services started successfully!"
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "💾 PostgreSQL: localhost:5432"
    echo "🔄 Redis: localhost:6379"
    
else
    echo "📦 Starting services individually..."
    
    # Start backend
    echo "🐍 Starting backend..."
    cd backend
    python main.py &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    echo "🎨 Starting frontend..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo "✅ Services started!"
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 Backend: http://localhost:8000"
    echo ""
    echo "To stop services:"
    echo "kill $BACKEND_PID $FRONTEND_PID"
fi

echo ""
echo "🎮 Run the demo:"
echo "python scripts/demo.py"
