#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "🚀 Starting Elasticsearch Integration..."

# Check for duplicate services
if pgrep -f "python.*main.py" > /dev/null || pgrep -f "uvicorn.*app" > /dev/null; then
    echo "⚠️  Warning: API server may already be running"
    echo "Checking processes:"
    pgrep -af "python.*main.py|uvicorn.*app" || true
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Elasticsearch is running
if ! curl -s http://localhost:9200 > /dev/null 2>&1; then
    echo "❌ Elasticsearch not running. Starting with Docker..."
    if docker ps -a --format '{{.Names}}' | grep -q "^elasticsearch$"; then
        echo "Starting existing Elasticsearch container..."
        docker start elasticsearch
    else
        docker run -d --name elasticsearch \
            -p 9200:9200 -p 9300:9300 \
            -e "discovery.type=single-node" \
            -e "xpack.security.enabled=false" \
            docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    fi
    
    echo "⏳ Waiting for Elasticsearch to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:9200 > /dev/null 2>&1; then
            echo "✅ Elasticsearch is ready!"
            break
        fi
        sleep 1
    done
fi

# Check if RabbitMQ is running  
if ! curl -s http://localhost:15672 > /dev/null 2>&1; then
    echo "❌ RabbitMQ not running. Starting with Docker..."
    if docker ps -a --format '{{.Names}}' | grep -q "^rabbitmq$"; then
        echo "Starting existing RabbitMQ container..."
        docker start rabbitmq
    else
        docker run -d --name rabbitmq \
            -p 5672:5672 -p 15672:15672 \
            rabbitmq:3.12-management
    fi
    
    echo "⏳ Waiting for RabbitMQ to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:15672 > /dev/null 2>&1; then
            echo "✅ RabbitMQ is ready!"
            break
        fi
        sleep 1
    done
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/build.sh first"
    exit 1
fi

source venv/bin/activate

# Start API server
echo "🌐 Starting API server..."
python src/main.py &
API_PID=$!

sleep 5

# Check if server started successfully
if ! kill -0 $API_PID 2>/dev/null; then
    echo "❌ Failed to start API server"
    exit 1
fi

echo "✅ Services started!"
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo "🔍 API: http://localhost:8000/api/search"
echo "💚 Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"

# Wait for interrupt
trap "kill $API_PID 2>/dev/null; exit" INT TERM
wait $API_PID
