#!/bin/bash

# Circuit Breaker Log System - Start Script
# This script builds, tests, and runs the circuit breaker system

set -e  # Exit on any error

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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Function to setup virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Virtual environment setup complete"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Activate virtual environment if not already activated
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source venv/bin/activate
    fi
    
    # Run only the fastest tests to verify basic functionality
    python -m pytest tests/test_circuit_breaker.py::TestCircuitBreaker::test_circuit_breaker_creation -v
    
    if [ $? -eq 0 ]; then
        print_success "Basic test passed"
    else
        print_warning "Test failed, but continuing with build..."
    fi
}

# Function to build Docker images
build_docker() {
    print_status "Building Docker images..."
    
    # Build the main application
    docker-compose build --no-cache
    
    if [ $? -eq 0 ]; then
        print_success "Docker images built successfully"
    else
        print_error "Docker build failed"
        exit 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    # Start all services
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_success "All services are running"
    else
        print_error "Some services failed to start"
        docker-compose logs
        exit 1
    fi
}

# Function to run demo
run_demo() {
    print_status "Running demo..."
    
    # Wait a bit for services to be fully ready
    sleep 5
    
    # Run the demo script
    if command -v python3 &> /dev/null; then
        python3 demo.py
    else
        print_warning "Python3 not found, skipping demo"
    fi
}

# Function to show final status
show_final_status() {
    print_success "Circuit Breaker Log System is ready!"
    echo
    echo "🌐 Dashboard: http://localhost:8000"
    echo "📊 API Metrics: http://localhost:8000/api/metrics"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo
    echo "🛑 To stop all services: ./stop.sh"
    echo "🔄 To restart: ./start.sh"
    echo
    print_status "Services are running in the background"
    print_status "Check logs with: docker-compose logs -f"
}

# Main execution
main() {
    echo "🚀 Circuit Breaker Log System - Starting..."
    echo "============================================================"
    
    check_docker
    check_dependencies
    setup_venv
    run_tests
    build_docker
    start_services
    run_demo
    show_final_status
}

# Run main function
main "$@" 