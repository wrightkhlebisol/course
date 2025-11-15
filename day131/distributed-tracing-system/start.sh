#!/bin/bash
set -e

echo "🚀 Starting Distributed Tracing System"
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./build.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Redis is running
if ! command -v redis-cli &> /dev/null || ! redis-cli ping &> /dev/null; then
    echo "🚀 Starting Redis with Docker..."
    docker run -d --name redis-tracing -p 6379:6379 redis:7-alpine || true
    sleep 3
fi

# Start the application
echo "🚀 Starting application..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python src/main.py

echo "🛑 Application stopped"
