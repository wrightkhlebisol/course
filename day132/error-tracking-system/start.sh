#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Error Tracking System..."
echo "📂 Working directory: $SCRIPT_DIR"

# Check if using Docker
if [ "$1" = "docker" ]; then
    echo "🐳 Starting with Docker Compose..."
    if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" up --build
    else
        echo "❌ docker-compose.yml not found in $SCRIPT_DIR"
        exit 1
    fi
else
    echo "🏃 Starting local development servers..."
    
    # Check if venv exists
    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
        echo "   Please run the setup script first"
        exit 1
    fi
    
    # Activate virtual environment
    source "$SCRIPT_DIR/venv/bin/activate"
    
    # Check if backend directory exists
    if [ ! -d "$SCRIPT_DIR/backend" ]; then
        echo "❌ Backend directory not found at $SCRIPT_DIR/backend"
        exit 1
    fi
    
    # Check if backend main.py exists
    if [ ! -f "$SCRIPT_DIR/backend/app/main.py" ]; then
        echo "❌ Backend main.py not found at $SCRIPT_DIR/backend/app/main.py"
        exit 1
    fi
    
    # Start backend in background
    echo "🔧 Starting backend server..."
    cd "$SCRIPT_DIR/backend"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd "$SCRIPT_DIR"
    
    # Start frontend if Node.js is available
    FRONTEND_PID=""
    if command -v node &> /dev/null; then
        if [ -d "$SCRIPT_DIR/frontend" ]; then
            echo "⚛️ Starting frontend server..."
            cd "$SCRIPT_DIR/frontend"
            npm start &
            FRONTEND_PID=$!
            cd "$SCRIPT_DIR"
        else
            echo "⚠️ Frontend directory not found, skipping frontend"
        fi
    else
        echo "⚠️ Node.js not found, skipping frontend"
    fi
    
    echo "✅ Services started!"
    echo "🌐 Backend API: http://localhost:8000"
    echo "🌐 Frontend: http://localhost:3000"
    echo "📊 API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" EXIT INT TERM
    wait
fi
