#!/bin/bash

echo "🐳 Building with Docker"
echo "======================"

# Build and start services
docker-compose up --build -d

echo "✅ Docker services started!"
echo ""
echo "🌐 Dashboard: http://localhost:3000"
echo "📡 API: http://localhost:8000"
echo ""
echo "Run 'docker-compose logs -f' to view logs"
echo "Run 'docker-compose down' to stop services"
