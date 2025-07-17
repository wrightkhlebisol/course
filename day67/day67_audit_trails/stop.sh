#!/bin/bash

# Audit Trails System - Stop Script
# This script gracefully stops all services and cleans up

set -e

echo "🛑 Stopping Audit Trails System..."

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

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running."
    exit 1
fi

# Stop all services gracefully
print_status "Stopping all services..."
docker-compose down --remove-orphans

# Check if any containers are still running
if docker-compose ps | grep -q "Up"; then
    print_warning "Some containers are still running. Force stopping..."
    docker-compose down --remove-orphans --timeout 10
fi

# Remove any dangling containers
print_status "Cleaning up containers..."
docker container prune -f > /dev/null 2>&1 || true

# Remove any dangling networks
print_status "Cleaning up networks..."
docker network prune -f > /dev/null 2>&1 || true

# Optional: Remove volumes (uncomment if you want to reset data)
# print_status "Removing volumes..."
# docker-compose down -v

print_success "All services stopped successfully!"
echo ""
echo "📊 Services stopped:"
echo "   Frontend (port 3000)"
echo "   Backend API (port 8000)"
echo "   PostgreSQL (port 5432)"
echo "   Redis (port 6379)"
echo ""
echo "🚀 To restart the system: ./start.sh" 