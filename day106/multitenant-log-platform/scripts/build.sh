#!/bin/bash

set -e

echo "🔨 Building Multi-Tenant Log Platform"
echo "===================================="

# Build backend
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Build frontend
echo "🎨 Installing frontend dependencies..."
cd frontend
npm install
echo "🏗️  Building frontend..."
npm run build
cd ..

echo "✅ Build completed successfully!"
