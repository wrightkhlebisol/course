#!/bin/bash

echo "🛑 Stopping Tenant Usage Reporting & Billing System"
echo "================================================="

# Kill processes by port
echo "🔌 Stopping backend (port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "Backend not running"

echo "🌐 Stopping frontend (port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "Frontend not running"

echo "🐳 Stopping Docker containers..."
docker-compose down

echo "✅ System stopped successfully!"
