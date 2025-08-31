#!/bin/bash

# Storage Format Optimization System - Start Script
# This script builds, launches, and demonstrates the system with UI dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="storage-optimizer"
PYTHON_VERSION="python3.11"
DASHBOARD_PORT=8000
PID_FILE="storage_optimizer.pid"
LOG_FILE="storage_optimizer.log"

echo -e "${BLUE}🚀 Storage Format Optimization System - Start Script${NC}"
echo -e "${BLUE}==================================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Cleaning up...${NC}"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping process $PID...${NC}"
            kill $PID 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Error: $PROJECT_DIR directory not found${NC}"
    echo -e "${YELLOW}Please run this script from the project root directory${NC}"
    exit 1
fi

# Check Python version
if ! command_exists $PYTHON_VERSION; then
    echo -e "${RED}❌ Error: $PYTHON_VERSION not found${NC}"
    echo -e "${YELLOW}Please install Python 3.11 or update the PYTHON_VERSION variable${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Check if dependencies are installed
echo -e "${CYAN}📦 Checking dependencies...${NC}"
if ! $PYTHON_VERSION -c "import fastapi, uvicorn, pyarrow, pandas" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies not found. Installing...${NC}"
    $PYTHON_VERSION -m pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Check if port is available
if port_in_use $DASHBOARD_PORT; then
    echo -e "${YELLOW}⚠️  Port $DASHBOARD_PORT is already in use${NC}"
    echo -e "${YELLOW}Please stop any existing services on port $DASHBOARD_PORT${NC}"
    exit 1
fi

# Run tests to ensure everything is working
echo -e "${CYAN}🧪 Running tests...${NC}"
if $PYTHON_VERSION -m pytest tests/ -v --tb=short > test_results.log 2>&1; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${RED}❌ Some tests failed. Check test_results.log for details${NC}"
    exit 1
fi

# Run demo to generate sample data
echo -e "${CYAN}🎭 Running demo to generate sample data...${NC}"
$PYTHON_VERSION demo.py > demo_output.log 2>&1
echo -e "${GREEN}✅ Demo completed${NC}"

# Start the main application
echo -e "${CYAN}🌐 Starting Storage Optimization Dashboard...${NC}"
echo -e "${PURPLE}📊 Dashboard will be available at: http://localhost:$DASHBOARD_PORT${NC}"

# Start the application in background
$PYTHON_VERSION src/main.py > "$LOG_FILE" 2>&1 &
MAIN_PID=$!

# Save PID for cleanup
echo $MAIN_PID > "$PID_FILE"

# Wait a moment for the server to start
sleep 3

# Check if the server started successfully
if ps -p $MAIN_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Storage Optimization System started successfully!${NC}"
    echo -e "${GREEN}📊 Dashboard PID: $MAIN_PID${NC}"
    echo -e "${GREEN}📝 Log file: $LOG_FILE${NC}"
    
    # Wait for server to be ready
    echo -e "${CYAN}⏳ Waiting for server to be ready...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:$DASHBOARD_PORT > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠️  Server may still be starting up...${NC}"
        fi
        sleep 1
    done
    
    # Run comprehensive demo execution steps
    echo -e "${CYAN}🎬 Running comprehensive demo execution steps...${NC}"
    
    # Step 1: Generate initial demo data
    echo -e "${YELLOW}📝 Step 1: Generating initial demo data...${NC}"
    curl -s -X POST http://localhost:$DASHBOARD_PORT/api/demo/metrics > /dev/null 2>&1 || true
    sleep 2
    
    # Step 2: Run multiple demo cycles to build up metrics
    echo -e "${YELLOW}📊 Step 2: Building up metrics with multiple demo cycles...${NC}"
    for i in {1..3}; do
        echo -e "${PURPLE}   Running demo cycle $i/3...${NC}"
        curl -s -X POST http://localhost:$DASHBOARD_PORT/api/demo/metrics > /dev/null 2>&1 || true
        sleep 1
    done
    
    # Step 3: Verify metrics are working
    echo -e "${YELLOW}🔍 Step 3: Verifying metrics are working...${NC}"
    sleep 2
    if curl -s http://localhost:$DASHBOARD_PORT/api/stats | grep -q "format_distribution"; then
        echo -e "${GREEN}✅ Format distribution metrics verified${NC}"
    else
        echo -e "${YELLOW}⚠️  Format distribution may still be initializing...${NC}"
    fi
    
    echo -e "${GREEN}✅ Comprehensive demo execution completed${NC}"
    
    # Display final metrics summary
    echo -e "${CYAN}📊 Final Metrics Summary:${NC}"
    sleep 1
    if command_exists jq; then
        echo -e "${YELLOW}Format Distribution:${NC}"
        curl -s http://localhost:$DASHBOARD_PORT/api/stats | jq -r '.storage_stats.format_distribution | "   Row: \(.row), Columnar: \(.columnar), Hybrid: \(.hybrid)"' 2>/dev/null || echo -e "${YELLOW}   Metrics available on dashboard${NC}"
        
        echo -e "${YELLOW}Storage Stats:${NC}"
        curl -s http://localhost:$DASHBOARD_PORT/api/stats | jq -r '.storage_stats | "   Total Storage: \(.total_storage_mb) MB, Compression: \(.compression_savings)%"' 2>/dev/null || echo -e "${YELLOW}   Metrics available on dashboard${NC}"
    else
        echo -e "${YELLOW}   Metrics available on dashboard${NC}"
    fi
    
    echo -e "\n${BLUE}🎉 Storage Format Optimization System is now running!${NC}"
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${GREEN}📊 Dashboard: http://localhost:$DASHBOARD_PORT${NC}"
    echo -e "${GREEN}📝 Logs: $LOG_FILE${NC}"
    echo -e "${GREEN}🆔 Process ID: $MAIN_PID${NC}"
    echo -e "${YELLOW}🛑 To stop the system, run: ./stop.sh${NC}"
    echo -e "\n${CYAN}🔍 System Features:${NC}"
    echo -e "   • Adaptive storage format optimization"
    echo -e "   • Real-time query pattern analysis"
    echo -e "   • Performance monitoring dashboard"
    echo -e "   • Automatic format recommendations"
    echo -e "\n${PURPLE}💡 The system will continuously optimize storage formats based on query patterns${NC}"
    
    # Keep the script running to maintain the background process
    echo -e "\n${YELLOW}🔄 System is running. Press Ctrl+C to stop...${NC}"
    wait $MAIN_PID
    
else
    echo -e "${RED}❌ Failed to start Storage Optimization System${NC}"
    echo -e "${YELLOW}Check the log file: $LOG_FILE${NC}"
    exit 1
fi 