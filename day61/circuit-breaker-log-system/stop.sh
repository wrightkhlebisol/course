#!/bin/bash

# Circuit Breaker Log System - Stop Script
# This script stops all services and cleans up resources

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
        print_warning "Docker is not running. Services may already be stopped."
        return 1
    fi
    return 0
}

# Function to stop Docker services
stop_docker_services() {
    print_status "Stopping Docker services..."
    
    if docker-compose ps | grep -q "Up"; then
        # Stop all services gracefully
        docker-compose down --timeout 30
        
        if [ $? -eq 0 ]; then
            print_success "Docker services stopped successfully"
        else
            print_warning "Some services may still be running"
        fi
    else
        print_status "No Docker services are currently running"
    fi
}

# Function to remove Docker containers and networks
cleanup_docker() {
    print_status "Cleaning up Docker resources..."
    
    # Remove any stopped containers
    docker container prune -f
    
    # Remove unused networks
    docker network prune -f
    
    # Remove unused volumes (optional - uncomment if needed)
    # docker volume prune -f
    
    print_success "Docker cleanup completed"
}

# Function to stop any running Python processes
stop_python_processes() {
    print_status "Checking for running Python processes..."
    
    # Find and stop any Python processes related to this project
    local python_pids=$(ps aux | grep -E "python.*src/main.py|python.*circuit_breaker" | grep -v grep | awk '{print $2}')
    
    if [ ! -z "$python_pids" ]; then
        print_status "Stopping Python processes: $python_pids"
        echo "$python_pids" | xargs kill -TERM 2>/dev/null || true
        
        # Wait a moment and force kill if necessary
        sleep 2
        echo "$python_pids" | xargs kill -KILL 2>/dev/null || true
        
        print_success "Python processes stopped"
    else
        print_status "No running Python processes found"
    fi
}

# Function to deactivate virtual environment
deactivate_venv() {
    if [ ! -z "$VIRTUAL_ENV" ]; then
        print_status "Deactivating virtual environment..."
        deactivate 2>/dev/null || true
        print_success "Virtual environment deactivated"
    fi
}

# Function to show final status
show_final_status() {
    print_status "Final Status:"
    echo "=============="
    
    # Check if any containers are still running
    if check_docker; then
        local running_containers=$(docker-compose ps --filter "status=running" --format "table {{.Name}}\t{{.Status}}")
        if [ ! -z "$running_containers" ]; then
            print_warning "Some containers are still running:"
            echo "$running_containers"
        else
            print_success "All containers stopped"
        fi
    fi
    
    # Check for any remaining Python processes
    local remaining_python=$(ps aux | grep -E "python.*src/main.py|python.*circuit_breaker" | grep -v grep)
    if [ ! -z "$remaining_python" ]; then
        print_warning "Some Python processes may still be running:"
        echo "$remaining_python"
    else
        print_success "All Python processes stopped"
    fi
}

# Function to provide cleanup options
show_cleanup_options() {
    echo ""
    print_status "Additional cleanup options:"
    echo "================================"
    echo "  - Remove all Docker images: docker system prune -a"
    echo "  - Remove all Docker volumes: docker volume prune -a"
    echo "  - Remove virtual environment: rm -rf venv"
    echo "  - Clean Python cache: find . -type d -name '__pycache__' -exec rm -rf {} +"
    echo ""
    print_status "To restart the system, run: ./start.sh"
}

# Main execution
main() {
    echo "🛑 Circuit Breaker Log System - Stopping..."
    echo "============================================="
    
    # Stop Python processes first
    stop_python_processes
    
    # Deactivate virtual environment
    deactivate_venv
    
    # Stop Docker services if Docker is available
    if check_docker; then
        stop_docker_services
        cleanup_docker
    fi
    
    # Show final status
    show_final_status
    
    # Show cleanup options
    show_cleanup_options
    
    echo ""
    print_success "✅ Circuit Breaker Log System stopped successfully!"
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}[WARNING]${NC} Script interrupted. Some processes may still be running."; exit 1' INT TERM

# Run main function
main "$@" 