#!/bin/bash
set -e

echo "🎬 Day 140 S3 Export System - Complete Demonstration"
echo "===================================================="
echo ""

# Set AWS credentials for MinIO (local development)
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-minioadmin}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-minioadmin}

# Activate virtual environment
source venv/bin/activate

# Check if server is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Server is already running, using existing instance"
    SERVER_PID=""
else
    # Start the server in background
    echo "🚀 Starting export system..."
    python src/main.py &
    SERVER_PID=$!
    
    # Wait for server to start
    echo "⏳ Waiting for server to initialize..."
    sleep 8
fi

echo ""
echo "📊 System Status Check"
echo "----------------------"
curl -s http://localhost:8000/api/export/status | python -m json.tool

echo ""
echo ""
echo "🔥 Triggering Manual Export"
echo "---------------------------"
curl -s -X POST http://localhost:8000/api/export/manual \
  -H "Content-Type: application/json" \
  -d '{}' | python -m json.tool

echo ""
echo "⏳ Waiting for export to complete..."
sleep 5

echo ""
echo "📋 Export History"
echo "-----------------"
curl -s http://localhost:8000/api/export/history | python -m json.tool

echo ""
echo "📦 Storage Objects"
echo "------------------"
curl -s http://localhost:8000/api/storage/objects | python -m json.tool

echo ""
echo ""
echo "✅ Demonstration Complete!"
echo ""
echo "🌐 Web Dashboard: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""

# Only wait if we started the server
if [ -n "$SERVER_PID" ]; then
    echo "Press Ctrl+C to stop the server"
    wait $SERVER_PID
else
    echo "Server was already running - it will continue running in the background"
fi
