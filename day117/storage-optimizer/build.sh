#!/bin/bash

echo "🚀 Building Storage Optimization System"
echo "======================================"

# Backend setup
echo "📦 Setting up backend..."
cd backend
source venv/bin/activate
pip install -r requirements.txt

echo "🧪 Running backend tests..."
cd ..
python -m pytest backend/tests/ -v

# Frontend setup
echo "🌐 Setting up frontend..."
cd frontend
npm install

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run: ./start.sh to start the system"
echo "2. Open: http://localhost:3000 for dashboard"
echo "3. API: http://localhost:8000/docs for API documentation"
