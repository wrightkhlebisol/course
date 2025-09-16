#!/bin/bash

echo "🚀 Building Tenant Usage Reporting & Billing System"
echo "=================================================="

# Activate virtual environment
source venv/bin/activate

echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo "🧪 Running backend tests..."
cd backend
python -m pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "❌ Backend tests failed"
    exit 1
fi
cd ..

echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "🏗️ Building frontend..."
cd frontend
npm run build
cd ..

echo "🐳 Building Docker images..."
docker-compose build

echo "✅ Build completed successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Run 'chmod +x start.sh && ./start.sh' to start the system"
echo "  2. Open http://localhost:3000 for the dashboard"
echo "  3. API available at http://localhost:8000"
