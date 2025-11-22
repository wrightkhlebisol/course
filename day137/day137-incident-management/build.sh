#!/bin/bash

echo "🚀 Building Day 137: PagerDuty/OpsGenie Integration System"
echo "========================================================="

# Activate virtual environment
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo "🧪 Running tests..."
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python -m pytest tests/ -v --tb=short

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "  ./start.sh    - Start the application"
echo "  ./stop.sh     - Stop the application"
echo "  ./test.sh     - Run comprehensive tests"
