#!/bin/bash

# Day 52: Lightning-Fast Log Search with Inverted Indexing
# Comprehensive Build, Test, and Demo Script

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3.11; then
        PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
        print_success "Found Python $PYTHON_VERSION"
        PYTHON_CMD="python3.11"
    elif command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_warning "Found Python $PYTHON_VERSION (recommended: 3.11.9)"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.11.9 not found. Please install Python 3.11.9"
        exit 1
    fi
}

# Function to setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_status "Installing Python dependencies..."
    pip install -r backend/requirements.txt
    
    print_success "Python environment setup complete"
}

# Function to setup Node.js environment
setup_node_env() {
    print_status "Setting up Node.js environment..."
    
    if ! command_exists node; then
        print_error "Node.js not found. Please install Node.js (version 18 or higher)"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    print_success "Found Node.js $NODE_VERSION"
    
    if ! command_exists npm; then
        print_error "npm not found. Please install npm"
        exit 1
    fi
    
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
    
    print_success "Node.js environment setup complete"
}

# Function to run backend tests
run_backend_tests() {
    print_status "Running backend tests..."
    
    source venv/bin/activate
    cd backend
    
    # Check if test directories exist
    if [ -d "tests/unit/" ]; then
        print_status "Running unit tests..."
        python -m pytest tests/unit/ -v
    else
        print_warning "Unit tests directory not found, skipping..."
    fi
    
    if [ -d "tests/integration/" ]; then
        print_status "Running integration tests..."
        python -m pytest tests/integration/ -v
    else
        print_warning "Integration tests directory not found, skipping..."
    fi
    
    if [ -d "tests/load/" ]; then
        print_status "Running performance tests..."
        python -m pytest tests/load/ -v
    else
        print_warning "Performance tests directory not found, skipping..."
    fi
    
    cd ..
    print_success "Backend tests completed"
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running frontend tests..."
    
    cd frontend
    npm test -- --watchAll=false --passWithNoTests
    
    cd ..
    print_success "Frontend tests completed"
}

# Function to build frontend
build_frontend() {
    print_status "Building frontend..."
    
    cd frontend
    npm run build
    
    cd ..
    print_success "Frontend build completed"
}

# Function to start Redis (if not running)
start_redis() {
    print_status "Checking Redis status..."
    
    if ! command_exists redis-server; then
        print_warning "Redis not found. Installing Redis..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install redis
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            sudo apt-get update && sudo apt-get install -y redis-server
        else
            print_error "Please install Redis manually for your OS"
            exit 1
        fi
    fi
    
    # Check if Redis is running
    if ! pgrep -x "redis-server" > /dev/null; then
        print_status "Starting Redis server..."
        redis-server --daemonize yes
        sleep 2
    else
        print_status "Redis server already running"
    fi
    
    print_success "Redis is ready"
}

# Function to start backend server
start_backend() {
    print_status "Starting backend server..."
    
    source venv/bin/activate
    cd backend
    
    # Start backend in background
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    cd ..
    
    # Wait for backend to start
    print_status "Waiting for backend to start..."
    sleep 5
    
    # Test backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend server started successfully (PID: $BACKEND_PID)"
    else
        print_error "Backend server failed to start"
        exit 1
    fi
}

# Function to start frontend server
start_frontend() {
    print_status "Starting frontend server..."
    
    cd frontend
    
    # Start frontend in background
    npm start &
    FRONTEND_PID=$!
    
    cd ..
    
    # Wait for frontend to start
    print_status "Waiting for frontend to start..."
    sleep 10
    
    # Test frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend server started successfully (PID: $FRONTEND_PID)"
    else
        print_warning "Frontend server may still be starting..."
    fi
}

# Function to load sample data
load_sample_data() {
    print_status "Loading sample data..."
    
    source venv/bin/activate
    cd backend
    
    # Create sample log files if they don't exist
    if [ ! -f "../data/sample_logs.txt" ]; then
        print_status "Creating sample log data..."
        mkdir -p ../data
        cat > ../data/sample_logs.txt << 'EOF'
2024-01-15 10:30:15 INFO User login successful user_id=12345
2024-01-15 10:31:22 ERROR Database connection failed timeout=30s
2024-01-15 10:32:45 WARN High memory usage detected usage=85%
2024-01-15 10:33:12 INFO API request processed endpoint=/api/users duration=150ms
2024-01-15 10:34:28 ERROR Authentication failed user_id=67890
2024-01-15 10:35:15 INFO Cache miss for key=user_profile_12345
2024-01-15 10:36:42 WARN Slow query detected query_time=2.5s
2024-01-15 10:37:18 INFO File upload completed file_size=1.2MB
2024-01-15 10:38:33 ERROR Payment processing failed transaction_id=txn_123
2024-01-15 10:39:55 INFO Email sent successfully recipient=user@example.com
EOF
    fi
    
    # Index the sample data
    print_status "Indexing sample data..."
    python -c "
import sys
import asyncio
sys.path.append('src')
from src.indexing.inverted_index import InvertedIndex
from src.indexing.tokenizer import LogTokenizer
from src.storage.index_storage import IndexStorage

async def index_data():
    # Initialize components
    tokenizer = LogTokenizer()
    storage = IndexStorage('../data/sample_index.json')
    index = InvertedIndex(tokenizer, storage)
    
    # Load and index sample data
    with open('../data/sample_logs.txt', 'r') as f:
        for line_num, line in enumerate(f, 1):
            doc_data = {
                'id': f'doc_{line_num}',
                'message': line.strip(),
                'timestamp': line.split()[0] + ' ' + line.split()[1]
            }
            await index.add_document(doc_data)
    
    # Save index
    await index.save_to_storage()
    print('Sample data indexed successfully')

# Run the async function
asyncio.run(index_data())
"
    
    cd ..
    print_success "Sample data loaded and indexed"
}

# Function to display demo information
show_demo_info() {
    echo ""
    echo "🎉 Demo is now running!"
    echo "=================================="
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo ""
    echo "Sample queries to try:"
    echo "- 'error' - Find all error logs"
    echo "- 'user_id=12345' - Find logs for specific user"
    echo "- 'database' - Find database-related logs"
    echo "- 'timeout' - Find timeout-related logs"
    echo ""
    echo "Press Ctrl+C to stop all servers"
    echo ""
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "react-scripts" 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Main execution
main() {
    echo "🚀 Day 52: Building Lightning-Fast Log Search with Inverted Indexing"
    echo "=================================================================="
    echo ""
    
    # Check Python version
    check_python_version
    
    # Setup environments
    setup_python_env
    setup_node_env
    
    # Run tests
    run_backend_tests
    run_frontend_tests
    
    # Build frontend
    build_frontend
    
    # Start services
    start_redis
    load_sample_data
    start_backend
    start_frontend
    
    # Show demo information
    show_demo_info
    
    # Keep script running
    print_status "Demo is running. Press Ctrl+C to stop..."
    wait
}

# Run main function
main "$@"
