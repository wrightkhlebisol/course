#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧪 Running Error Tracking System Tests..."
echo "📂 Working directory: $SCRIPT_DIR"

# Check if venv exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
    echo "   Please run the setup script first"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Check if backend directory exists
if [ ! -d "$SCRIPT_DIR/backend" ]; then
    echo "❌ Backend directory not found at $SCRIPT_DIR/backend"
    exit 1
fi

# Check if tests directory exists
if [ ! -d "$SCRIPT_DIR/backend/tests" ]; then
    echo "⚠️ Tests directory not found at $SCRIPT_DIR/backend/tests"
    echo "   Creating basic test structure..."
    mkdir -p "$SCRIPT_DIR/backend/tests"
fi

# Run backend tests
echo "🔧 Running backend tests..."
cd "$SCRIPT_DIR/backend"
python -m pytest tests/ -v --tb=short
TEST_EXIT_CODE=$?
cd "$SCRIPT_DIR"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
    exit 1
fi
