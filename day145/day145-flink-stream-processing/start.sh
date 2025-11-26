#!/bin/bash

# Get script directory and change to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Flink Stream Processing System"
echo "📁 Working directory: $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./build.sh first"
    exit 1
fi

# Check if required files exist
if [ ! -f "src/main.py" ]; then
    echo "❌ src/main.py not found"
    exit 1
fi

if [ ! -f "scripts/demo.py" ]; then
    echo "❌ scripts/demo.py not found"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start RabbitMQ (if not already running)
if ! docker ps | grep -q rabbitmq; then
    echo "Starting RabbitMQ..."
    docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management
    sleep 10
else
    echo "✅ RabbitMQ already running"
fi

# Start main application in background
echo "🚀 Starting main application..."
python "$SCRIPT_DIR/src/main.py" &
APP_PID=$!

sleep 5

# Run demo
echo "🎬 Running demonstration..."
python "$SCRIPT_DIR/scripts/demo.py"

echo ""
echo "✅ System running!"
echo "🌐 Dashboard: http://localhost:8080"
echo "🐰 RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for user interrupt
wait $APP_PID
