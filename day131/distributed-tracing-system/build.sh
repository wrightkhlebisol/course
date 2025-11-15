#!/bin/bash
set -e

echo "🏗️  Building Distributed Tracing System"
echo "=================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -o "3\.[0-9]\+")
if [[ ! "$PYTHON_VERSION" =~ ^3\.(9|10|11|12)$ ]]; then
    echo "❌ Python 3.9+ required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Run syntax checks
echo "🔍 Checking Python syntax..."
find src tests -name "*.py" -exec python -m py_compile {} \;

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Start services: ./start.sh"
echo "  2. Run tests: python tests/run_tests.py"
echo "  3. View dashboard: http://localhost:8000"
