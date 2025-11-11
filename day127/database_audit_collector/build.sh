#!/bin/bash

echo "🔨 Building Database Audit Collection System"
echo "============================================="

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t database-audit-collector:latest .

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run: ./start.sh"
echo "2. Open: http://localhost:8080"
