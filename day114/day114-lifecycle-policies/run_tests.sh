#!/bin/bash
set -e

echo "🧪 Running tests for Data Lifecycle Policy Engine..."

# Activate virtual environment
source venv/bin/activate

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration/ -v

echo "✅ All tests passed!"
