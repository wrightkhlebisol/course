#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "🎬 Running Elasticsearch Integration Demo..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/build.sh first"
    exit 1
fi

source venv/bin/activate

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API server is not running. Please start it with ./scripts/start.sh"
    exit 1
fi

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 5

# Generate test logs
echo "📝 Generating test logs..."
python src/generate_test_logs.py

echo "⏳ Waiting for logs to be indexed..."
sleep 15

# Test search
echo "🔍 Testing search functionality..."
echo ""
echo "Search for 'error' logs:"
curl -s "http://localhost:8000/api/search?q=error&size=5" | python -m json.tool

echo ""
echo "Get log level aggregations:"
curl -s "http://localhost:8000/api/aggregations/levels" | python -m json.tool

echo ""
echo "Get indexing statistics:"
curl -s "http://localhost:8000/api/stats/indexing" | python -m json.tool

echo ""
echo "✅ Demo complete!"
echo "🌐 Open http://localhost:8000/dashboard for interactive search"
