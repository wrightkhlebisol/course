#!/bin/bash

echo "🚀 Starting Enterprise Authentication System"

# Check if Docker is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Using Docker Compose..."
    docker-compose up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    echo "🔧 Initializing LDAP data..."
    python scripts/init_ldap.py
    
    echo "✅ System started successfully!"
    echo "🌐 Web Interface: http://localhost:8000"
    echo "📊 LDAP Admin: http://localhost:8080"
    
else
    echo "⚠️  Docker not found, starting in development mode..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start background services (you need to install PostgreSQL and Redis)
    echo "⚠️  Please ensure PostgreSQL and Redis are running"
    echo "⚠️  Please ensure LDAP server is configured"
    
    # Start the application
    python src/api/main.py &
    API_PID=$!
    
    echo "✅ API started with PID: $API_PID"
    echo "🌐 Web Interface: http://localhost:8000"
    
    # Store PID for stop script
    echo $API_PID > .api.pid
fi
