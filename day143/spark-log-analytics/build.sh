#!/bin/bash

# Build script for Spark Log Analytics

set -e

echo "🔨 Building Spark Log Analytics..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv || python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate test data
echo "Generating test data..."
python scripts/generate_test_logs.py

# Run tests
echo "Running tests..."
python -m pytest tests/unit -v

echo "✓ Build complete!"
echo ""
echo "Next steps:"
echo "  ./start.sh    - Start the application"
echo "  ./stop.sh     - Stop the application"
