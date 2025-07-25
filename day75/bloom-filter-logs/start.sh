#!/bin/bash

echo "🚀 Starting Bloom Filter Log Processing System"
echo "=============================================="

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment. Please ensure Python 3 is installed."
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check requirements.txt and try again."
    exit 1
fi

# Create data directory
mkdir -p data/bloom_filters

if [[ "$1" == "--docker" ]]; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up --build -d
    echo "🎉 Bloom Filter System (Docker) is running!"
    echo "=================================="
    echo "📊 Dashboard: http://localhost:8002"
    echo "🌐 API: http://localhost:8001"
    echo "📖 API Docs: http://localhost:8001/docs"
    echo "Use 'bash stop.sh --docker' to stop all Docker services"
    exit 0
fi

# Start API server in background
echo "🌐 Starting API server on port 8001..."
export PYTHONPATH=$PWD
nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload > logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > .api.pid

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ API server is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ API server failed to start"
        exit 1
    fi
done

# Start dashboard in background
echo "📊 Starting dashboard on port 8002..."
nohup python src/web/dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > .dashboard.pid

# Wait for dashboard to be ready
echo "⏳ Waiting for dashboard to be ready..."
sleep 5

echo ""
echo "🎉 Bloom Filter System is running!"
echo "=================================="
echo "📊 Dashboard: http://localhost:8002"
echo "🌐 API: http://localhost:8001"
echo "📖 API Docs: http://localhost:8001/docs"
echo ""
echo "Use 'bash stop.sh' to stop all services"
