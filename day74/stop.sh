#!/bin/bash

# Storage Format Optimization System - Stop Script
# This script stops all running processes and cleans up

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PID_FILE="storage_optimizer.pid"
LOG_FILE="storage_optimizer.log"
DASHBOARD_PORT=8000

echo -e "${BLUE}🛑 Storage Format Optimization System - Stop Script${NC}"
echo -e "${BLUE}==================================================${NC}"

# Function to check if a process is running
is_process_running() {
    ps -p $1 > /dev/null 2>&1
}

# Function to stop process gracefully
stop_process() {
    local pid=$1
    local process_name=$2
    
    if is_process_running $pid; then
        echo -e "${YELLOW}🛑 Stopping $process_name (PID: $pid)...${NC}"
        
        # Try graceful shutdown first
        kill $pid 2>/dev/null || true
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! is_process_running $pid; then
                echo -e "${GREEN}✅ $process_name stopped gracefully${NC}"
                return 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        if is_process_running $pid; then
            echo -e "${YELLOW}⚠️  Force stopping $process_name...${NC}"
            kill -9 $pid 2>/dev/null || true
            sleep 1
            
            if is_process_running $pid; then
                echo -e "${RED}❌ Failed to stop $process_name${NC}"
                return 1
            else
                echo -e "${GREEN}✅ $process_name force stopped${NC}"
            fi
        fi
    else
        echo -e "${CYAN}ℹ️  $process_name is not running${NC}"
    fi
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to stop processes on specific port
stop_port_processes() {
    local port=$1
    if port_in_use $port; then
        echo -e "${YELLOW}🛑 Stopping processes on port $port...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✅ Port $port cleared${NC}"
    else
        echo -e "${CYAN}ℹ️  No processes running on port $port${NC}"
    fi
}

# Stop main application if PID file exists
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    stop_process $PID "Storage Optimization System"
    rm -f "$PID_FILE"
else
    echo -e "${CYAN}ℹ️  No PID file found${NC}"
fi

# Stop any processes on the dashboard port
stop_port_processes $DASHBOARD_PORT

# Look for any remaining Python processes related to our application
echo -e "${CYAN}🔍 Checking for any remaining application processes...${NC}"
PYTHON_PROCESSES=$(ps aux | grep -E "(main\.py|storage.*optimization)" | grep -v grep | awk '{print $2}' || true)

if [ -n "$PYTHON_PROCESSES" ]; then
    echo -e "${YELLOW}🛑 Found additional Python processes, stopping them...${NC}"
    for pid in $PYTHON_PROCESSES; do
        stop_process $pid "Python process $pid"
    done
else
    echo -e "${GREEN}✅ No additional application processes found${NC}"
fi

# Clean up log files (optional - uncomment if you want to remove them)
# echo -e "${CYAN}🧹 Cleaning up log files...${NC}"
# rm -f "$LOG_FILE" "test_results.log" "demo_output.log" 2>/dev/null || true

# Verify everything is stopped
echo -e "${CYAN}🔍 Verifying all processes are stopped...${NC}"
if port_in_use $DASHBOARD_PORT; then
    echo -e "${RED}❌ Port $DASHBOARD_PORT is still in use${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Port $DASHBOARD_PORT is free${NC}"
fi

# Check for any remaining processes
REMAINING_PROCESSES=$(ps aux | grep -E "(main\.py|storage.*optimization)" | grep -v grep || true)
if [ -n "$REMAINING_PROCESSES" ]; then
    echo -e "${YELLOW}⚠️  Some processes may still be running:${NC}"
    echo "$REMAINING_PROCESSES"
else
    echo -e "${GREEN}✅ All application processes stopped${NC}"
fi

echo -e "\n${BLUE}🎉 Storage Format Optimization System stopped successfully!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}✅ All processes stopped${NC}"
echo -e "${GREEN}✅ Port $DASHBOARD_PORT freed${NC}"
echo -e "${GREEN}✅ Cleanup completed${NC}"
echo -e "\n${CYAN}💡 To restart the system, run: ./start.sh${NC}" 