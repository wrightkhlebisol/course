#!/bin/bash
set -e

echo "🔨 Building Day 140: S3 Export System"

# Create and activate virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/exports data/metadata

# Initialize database
echo "🗄️  Initializing database with sample data..."
python src/init_db.py

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --tb=short

echo "✅ Build completed successfully!"
