#!/bin/bash
set -e

echo "🏗️ Building Linux Log Collector..."

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --cov=src --cov-report=html

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t linux-log-collector:latest .

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "  ./start.sh    - Start the collector"
echo "  ./test.sh     - Run functional tests"
echo "  ./demo.sh     - Run demonstration"
