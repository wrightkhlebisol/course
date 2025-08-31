#!/bin/bash

echo "🔨 Building Compliance Reports System"
echo "====================================="

# Backend setup
echo "📦 Setting up backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend
npm install
echo "✅ Frontend dependencies installed"

# Create exports directory
mkdir -p ../backend/exports
echo "✅ Exports directory created"

echo "🎉 Build completed successfully!"
echo "Run './scripts/start.sh' to start the system"
