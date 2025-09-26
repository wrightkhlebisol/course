#!/bin/bash
set -euo pipefail

echo "🏗️  Building Archive Restoration System"
echo "====================================="

# Activate virtual environment
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build frontend
if command -v npm &> /dev/null; then
    echo "⚛️  Building React frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Copy build to backend static directory
    rm -rf backend/static
    cp -r frontend/build backend/static
else
    echo "⚠️  npm not found. Skipping frontend build."
    echo "   Install Node.js to build the complete UI."
fi

echo "🧪 Running tests..."
cd backend
python -m pytest tests/ -v --tb=short

echo "✅ Build completed successfully!"
echo ""
echo "🚀 To start the system:"
echo "   ./start.sh"
echo ""
echo "📊 Access the dashboard at:"
echo "   http://localhost:8000"
