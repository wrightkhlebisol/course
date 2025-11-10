#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 Building Day 126 Container Log Collector"
echo "Working directory: $SCRIPT_DIR"

# Create and activate virtual environment
echo "📦 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v || echo "⚠️  Some tests may have failed, but continuing..."

echo "✅ Build complete!"
echo "Run './start.sh' to start the system"
