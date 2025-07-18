#!/bin/bash

set -e

echo "🚀 Starting Day 68: Data Retention System"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Install Python dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Create storage directories
echo "📁 Creating storage directories..."
mkdir -p /tmp/logs/{hot,warm,cold}

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

# Start backend API
echo "🔧 Starting backend API..."
python src/main.py &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API started successfully (PID: $BACKEND_PID)"
else
    echo "❌ Backend API failed to start"
    exit 1
fi

# Start frontend (if it exists)
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    echo "⚛️ Starting React frontend..."
    cd frontend
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install --silent
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install frontend dependencies"
            cd ..
            exit 1
        fi
    fi
    
    # Check if npm start script exists
    if ! npm run | grep -q "start"; then
        echo "❌ No 'start' script found in package.json"
        cd ..
        exit 1
    fi
    
    # Start the frontend
    echo "🚀 Launching React development server..."
    npm start &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
    
    # Verify the process is running
    if ! ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        echo "❌ Frontend failed to start"
        exit 1
    fi
    
    # Wait for frontend to start
    echo "⏳ Waiting for frontend to start..."
    sleep 10
    
    # Check if frontend is running
    if curl -s http://localhost:3000 > /dev/null; then
        echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
    else
        echo "⚠️ Frontend may still be starting up..."
        echo "   Check http://localhost:3000 in a few moments"
        echo "   You can also check the logs with: tail -f logs/frontend.log"
    fi
else
    echo "ℹ️ No frontend found, starting backend only"
fi

echo ""
echo "🎉 Data Retention System Started Successfully!"
echo "=============================================="
echo "🌐 Backend API: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
echo "📚 API Docs: http://localhost:8000/docs"
if [ -n "$FRONTEND_PID" ]; then
    echo "⚛️ Frontend: http://localhost:3000"
fi
echo ""
echo "📋 Service PIDs:"
echo "  • Backend: $BACKEND_PID"
if [ -n "$FRONTEND_PID" ]; then
    echo "  • Frontend: $FRONTEND_PID"
fi
echo ""
echo "🛑 To stop services, run: ./stop.sh"
echo "==============================================" 