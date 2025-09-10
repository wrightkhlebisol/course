#!/bin/bash

set -e

echo "🧪 Running Multi-Tenant Log Platform Tests"
echo "=========================================="

# Run backend tests
echo "🐍 Running Python tests..."
python -m pytest tests/ -v --tb=short

echo "✅ All tests passed!"
