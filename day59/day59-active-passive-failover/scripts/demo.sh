#!/bin/bash

echo "🎬 Starting Active-Passive Failover Demo..."

# Start services
echo "Starting Redis..."
docker-compose up -d redis

echo "Waiting for Redis to be ready..."
sleep 5

echo "Starting primary node..."
docker-compose up -d primary-node

echo "Starting standby nodes..."
docker-compose up -d standby-node-1 standby-node-2

echo "Starting frontend..."
docker-compose up -d frontend

echo "Waiting for services to be ready..."
sleep 10

echo "🚀 Demo is ready!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔍 Primary API: http://localhost:8001/health"
echo "🔍 Standby 1 API: http://localhost:8002/health"
echo "🔍 Standby 2 API: http://localhost:8003/health"

echo "💡 Try these commands:"
echo "  - Check health: curl http://localhost:8001/health"
echo "  - Submit logs: curl -X POST http://localhost:8001/logs -H 'Content-Type: application/json' -d '{\"message\":\"Test log\",\"level\":\"INFO\"}'"
echo "  - Trigger failover: curl -X POST http://localhost:8001/admin/trigger-failover"
echo "  - Search logs: curl 'http://localhost:8001/logs/search?query=test'"

echo "Press Ctrl+C to stop the demo"
docker-compose logs -f
