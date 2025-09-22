#!/bin/bash
set -e

echo "🏗️ Building Data Lifecycle Policy Engine..."

# Create and activate virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd src/frontend
npm install
npm run build
cd ../..

# Create database and run migrations
echo "Setting up database..."
python -c "
from src.backend.database import create_tables
from src.backend.policy_engine.manager import PolicyManager
create_tables()
manager = PolicyManager()
manager.create_default_policies()
print('✅ Database setup complete')
"

echo "✅ Build completed successfully!"
echo "Run './start.sh' to start the application"
