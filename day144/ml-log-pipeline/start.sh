#!/bin/bash
set -e

source venv/bin/activate

# Generate training data
echo "📊 Generating training data..."
python scripts/generate_training_data.py

# Train models
echo "🎓 Training models..."
python -m src.main train

# Start API in background
echo "🚀 Starting API..."
python -m src.main api &
API_PID=$!

# Start dashboard in background
echo "🌐 Starting dashboard..."
python -m src.main dashboard &
DASH_PID=$!

echo ""
echo "✅ All services started!"
echo "   API: http://localhost:8000"
echo "   Dashboard: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $API_PID $DASH_PID; exit" INT
wait
