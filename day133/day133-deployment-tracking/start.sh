#!/bin/bash

echo "🚀 Starting Deployment Tracking System..."

# Create necessary directories
mkdir -p data logs

# Start with Docker Compose
docker-compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 15

# Check health
curl -s http://localhost:8000/api/deployments > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Deployment Tracking System is running!"
    echo "📊 Dashboard: http://localhost:8000"
    echo "🔍 API Health: http://localhost:8000/api/deployments"
else
    echo "❌ System failed to start properly"
    docker-compose logs
fi
