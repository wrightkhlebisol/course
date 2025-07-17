#!/bin/bash

# Audit Trails System - Start Script
# This script starts the complete audit trails system with database initialization

set -e

echo "🚀 Starting Audit Trails System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Initialize database if needed (will be handled by Docker)
print_status "Database initialization will be handled by Docker containers..."

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose down --remove-orphans

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check service status
print_status "Checking service status..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U audit_user -d audit_db > /dev/null 2>&1; then
    print_success "PostgreSQL is ready"
else
    print_warning "PostgreSQL is still starting up..."
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is ready"
else
    print_warning "Redis is still starting up..."
fi

# Check Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API is ready"
else
    print_warning "Backend API is still starting up..."
fi

# Check Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is ready"
else
    print_warning "Frontend is still starting up..."
fi

echo ""
print_success "Audit Trails System is starting up!"
echo ""
echo "📊 Service URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🗄️  Database:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "📝 Logs:"
echo "   Docker logs: docker-compose logs -f"
echo "   Backend logs: docker-compose logs -f backend"
echo "   Frontend logs: docker-compose logs -f frontend"
echo ""
echo "🛑 To stop the system: ./stop.sh"
echo ""
print_status "Services are starting up. Please wait a moment for all services to be fully ready." 