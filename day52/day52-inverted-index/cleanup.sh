#!/bin/bash

# Day 52: Cleanup Script for Log Search System
# Stops all running services and cleans up processes

set -e

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

# Function to check if process is running
is_process_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to kill process by pattern
kill_process() {
    local pattern="$1"
    local process_name="$2"
    
    if is_process_running "$pattern"; then
        print_status "Stopping $process_name..."
        pkill -f "$pattern" 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if is_process_running "$pattern"; then
            print_warning "Force killing $process_name..."
            pkill -9 -f "$pattern" 2>/dev/null || true
        fi
        
        if ! is_process_running "$pattern"; then
            print_success "$process_name stopped"
        else
            print_error "Failed to stop $process_name"
        fi
    else
        print_status "$process_name is not running"
    fi
}

# Function to stop services on specific ports
stop_port_service() {
    local port="$1"
    local service_name="$2"
    
    if lsof -ti:$port > /dev/null 2>&1; then
        print_status "Stopping $service_name on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        
        if ! lsof -ti:$port > /dev/null 2>&1; then
            print_success "$service_name on port $port stopped"
        else
            print_error "Failed to stop $service_name on port $port"
        fi
    else
        print_status "$service_name on port $port is not running"
    fi
}

# Main cleanup function
main() {
    echo "🧹 Day 52: Cleaning up Log Search System"
    echo "========================================"
    echo ""
    
    # Stop backend services
    print_status "Stopping backend services..."
    kill_process "uvicorn" "Backend server"
    kill_process "python.*main:app" "Backend application"
    stop_port_service "8000" "Backend API"
    
    # Stop frontend services
    print_status "Stopping frontend services..."
    kill_process "react-scripts" "Frontend development server"
    kill_process "npm.*start" "Frontend npm process"
    stop_port_service "3000" "Frontend application"
    
    # Stop Redis
    print_status "Stopping Redis..."
    kill_process "redis-server" "Redis server"
    
    # Stop any remaining Python processes related to the project
    print_status "Stopping remaining Python processes..."
    kill_process "python.*day52" "Python processes"
    
    # Stop any remaining Node.js processes related to the project
    print_status "Stopping remaining Node.js processes..."
    kill_process "node.*day52" "Node.js processes"
    
    # Clean up any temporary files
    print_status "Cleaning up temporary files..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Check if any processes are still running
    echo ""
    print_status "Checking for remaining processes..."
    
    local remaining_processes=0
    
    if is_process_running "uvicorn"; then
        print_warning "Backend server still running"
        remaining_processes=$((remaining_processes + 1))
    fi
    
    if is_process_running "react-scripts"; then
        print_warning "Frontend server still running"
        remaining_processes=$((remaining_processes + 1))
    fi
    
    if is_process_running "redis-server"; then
        print_warning "Redis server still running"
        remaining_processes=$((remaining_processes + 1))
    fi
    
    if lsof -ti:8000 > /dev/null 2>&1; then
        print_warning "Port 8000 still in use"
        remaining_processes=$((remaining_processes + 1))
    fi
    
    if lsof -ti:3000 > /dev/null 2>&1; then
        print_warning "Port 3000 still in use"
        remaining_processes=$((remaining_processes + 1))
    fi
    
    if [ $remaining_processes -eq 0 ]; then
        print_success "All services stopped successfully!"
    else
        print_warning "$remaining_processes process(es) still running"
        print_status "You may need to manually stop them or restart your system"
    fi
    
    echo ""
    print_success "Cleanup completed!"
}

# Run cleanup
main "$@" 