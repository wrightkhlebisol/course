#!/bin/bash

echo "🚀 Starting Day 77: Adaptive Resource Allocation System"
echo "======================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run the main setup script first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"

# Create logs directory
mkdir -p logs

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "📊 Starting metrics collection and adaptive allocation..."

# Start the main application
python src/main.py &
MAIN_PID=$!

echo "🌐 Web dashboard will be available at: http://localhost:8080"
echo "📊 System monitoring active"
echo "🎯 Adaptive scaling enabled"
echo ""
echo "🎬 To run the demo, open another terminal and run:"
echo "   source venv/bin/activate"
echo "   python scripts/demo.py"
echo ""
echo "Press Ctrl+C to stop the system..."

# Wait for main process
wait $MAIN_PID
