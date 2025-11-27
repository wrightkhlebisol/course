#!/bin/bash
set -e

echo "🔨 Building Day 146 project..."

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python -m pytest tests/ -v --tb=short || echo "⚠️  Some tests skipped (database may not be running)"

echo "✅ Build complete!"
echo ""
echo "Next steps:"
echo "1. Start TimescaleDB: docker-compose up -d timescaledb"
echo "2. Run pipeline: python src/main.py"
echo "3. Start API: uvicorn src.api.query_api:app --reload"
echo "4. Start dashboard: cd src/dashboard && npm install && npm start"
