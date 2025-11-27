#!/bin/bash
set -e

echo "🚀 Starting Day 146 Time Series Metrics System..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Starting services with Docker..."
    docker-compose up -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
    echo "✅ Services started!"
    echo "   - TimescaleDB: localhost:5432"
    echo "   - API: http://localhost:8000"
    echo "   - Dashboard: http://localhost:3000"
else
    echo "⚠️  Docker not found. Starting locally..."
    
    # Activate venv
    source venv/bin/activate
    
    # Start API in background
    echo "🔌 Starting API server..."
    python -m uvicorn src.api.query_api:app --host 0.0.0.0 --port 8000 &
    API_PID=$!
    
    # Start dashboard
    echo "📊 Starting dashboard..."
    cd src/dashboard
    npm start &
    DASH_PID=$!
    
    echo "✅ Services started!"
    echo "   API PID: $API_PID"
    echo "   Dashboard PID: $DASH_PID"
    echo ""
    echo "To stop: kill $API_PID $DASH_PID"
fi
