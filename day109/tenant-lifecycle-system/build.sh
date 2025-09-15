#!/bin/bash
set -e

echo "🏗️  Building Tenant Lifecycle Management System"
echo "=============================================="

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install Node.js dependencies for frontend
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
echo "✅ Frontend dependencies installed"

# Build React frontend
echo "🔨 Building React frontend..."
npm run build
echo "✅ Frontend built successfully"

cd ..

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/tenants

# Run Python tests
echo "🧪 Running backend tests..."
python -m pytest tests/ -v
echo "✅ All tests passed"

echo "🎉 Build completed successfully!"
echo ""
echo "Next steps:"
echo "  ./start.sh    - Start the application"
echo "  ./test.sh     - Run comprehensive tests"
echo "  ./demo.sh     - Run demonstration"
