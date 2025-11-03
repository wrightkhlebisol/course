#!/bin/bash

set -e

echo "🎬 Azure Monitor Integration Demo"
echo "================================="

# Start the system
echo "1. 🚀 Starting Azure Monitor Integration..."
source venv/bin/activate

# Run connection test
echo "2. 🔍 Testing Azure Monitor connection..."
cd src && python main.py test
cd ..

echo ""
echo "3. 🌐 Starting web dashboard..."
echo "   Dashboard URL: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

cd src && python main.py web
