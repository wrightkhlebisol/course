#!/bin/bash
set -e

echo "🧪 Running Distributed Tracing System Tests"
echo "======================================="

# Activate virtual environment
source venv/bin/activate

# Run tests
python tests/run_tests.py

echo "✅ Tests completed"
