#!/bin/bash
set -e

echo "🔨 Building Metrics Export System"
echo "=================================="

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --tb=short

echo "✅ Build completed successfully!"
