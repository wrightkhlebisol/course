#!/bin/bash

echo "🔨 Building Deployment Tracking System..."

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Create data directory
mkdir -p data logs

# Run tests
echo "🧪 Running tests..."
cd backend && python -m pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi

echo "✅ Build completed successfully!"
