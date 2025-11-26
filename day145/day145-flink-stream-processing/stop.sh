#!/bin/bash

echo "🛑 Stopping Flink Stream Processing System"

# Kill Python processes
pkill -f "python src/main.py"
pkill -f "python scripts/demo.py"

# Stop RabbitMQ
docker stop rabbitmq 2>/dev/null
docker rm rabbitmq 2>/dev/null

echo "✅ System stopped"
