#!/bin/bash

set -e

echo "▶️ Starting Azure Monitor Integration Dashboard"
echo "============================================="

# Activate virtual environment
source venv/bin/activate

# Start the dashboard
echo "🌐 Starting web dashboard on http://localhost:8000"
cd src && python main.py web
