#!/bin/bash

echo "🧪 Running comprehensive test suite..."

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v --tb=short

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration/ -v --tb=short

# Run chaos tests (if requested)
if [ "$1" == "chaos" ]; then
    echo "Running chaos engineering tests..."
    python -m pytest tests/chaos/ -v --tb=short -s
fi

echo "✅ All tests completed!"
