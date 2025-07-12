#!/bin/bash

# Build script for Day 62 implementation
set -e

echo "🔨 Building Distributed Log Processing System - Day 62"
echo "================================================="

# Build backend
echo "📦 Building backend..."
cd backend
python -m pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Build frontend
echo "🎨 Building frontend..."
cd ../frontend
npm install
npm run build
echo "✅ Frontend built successfully"

# Return to root
cd ..

echo "🎉 Build complete! Ready to run the application."
echo ""
echo "Next steps:"
echo "  1. Run: python backend/src/main.py"
echo "  2. Open: http://localhost:8000"
echo "  3. Test backpressure mechanisms in the web interface"
