#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Container Log Collector"
echo "Working directory: $SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./build.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Add project root to Python path so src module can be found
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Start the system
python -m src.main
