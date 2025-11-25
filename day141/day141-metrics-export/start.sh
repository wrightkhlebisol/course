#!/bin/bash
set -e

echo "🚀 Starting Metrics Export System"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup first."
    exit 1
fi

source venv/bin/activate

# Enable Datadog if not explicitly disabled
export DATADOG_ENABLED=${DATADOG_ENABLED:-true}

# Start the application
echo "Starting FastAPI server..."
python -m src.main &
APP_PID=$!

echo "✅ Application started (PID: $APP_PID)"
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo "📈 Metrics: http://localhost:8000/metrics"
echo "🏥 Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"

# Wait for interrupt
trap "kill $APP_PID; exit" INT TERM
wait $APP_PID
