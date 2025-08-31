#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Compliance Reports System${NC}"
echo -e "${BLUE}=====================================${NC}"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to kill process by port
kill_process_on_port() {
    local port=$1
    local service_name=$2
    
    if check_port $port; then
        echo -e "${YELLOW}🛑 Stopping $service_name on port $port...${NC}"
        local pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            kill -TERM $pid 2>/dev/null
            sleep 2
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force killing $service_name...${NC}"
                kill -KILL $pid 2>/dev/null
            fi
        fi
    else
        echo -e "${GREEN}✅ $service_name is not running${NC}"
    fi
}

# Check if Docker Compose is available and containers are running
if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
    echo -e "${CYAN}🐳 Stopping Docker containers...${NC}"
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        echo -e "${YELLOW}📦 Stopping and removing containers...${NC}"
        docker-compose down
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Docker containers stopped successfully${NC}"
        else
            echo -e "${RED}❌ Failed to stop Docker containers${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ No Docker containers are running${NC}"
    fi
    
    # Clean up Docker resources if requested
    if [ "$1" = "--clean" ]; then
        echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"
        docker-compose down --volumes --remove-orphans
        docker system prune -f
        echo -e "${GREEN}✅ Docker cleanup completed${NC}"
    fi
    
else
    echo -e "${CYAN}🔧 Stopping manual services...${NC}"
    
    # Stop backend if PID file exists
    if [ -f ".backend.pid" ]; then
        local backend_pid=$(cat .backend.pid)
        if [ ! -z "$backend_pid" ] && kill -0 $backend_pid 2>/dev/null; then
            echo -e "${YELLOW}🛑 Stopping backend (PID: $backend_pid)...${NC}"
            kill -TERM $backend_pid
            sleep 3
            
            # Force kill if still running
            if kill -0 $backend_pid 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force killing backend...${NC}"
                kill -KILL $backend_pid
            fi
        fi
        rm -f .backend.pid
        echo -e "${GREEN}✅ Backend stopped${NC}"
    else
        # Try to kill by port
        kill_process_on_port 8000 "Backend API"
    fi
    
    # Stop frontend if PID file exists
    if [ -f ".frontend.pid" ]; then
        local frontend_pid=$(cat .frontend.pid)
        if [ ! -z "$frontend_pid" ] && kill -0 $frontend_pid 2>/dev/null; then
            echo -e "${YELLOW}🛑 Stopping frontend (PID: $frontend_pid)...${NC}"
            kill -TERM $frontend_pid
            sleep 3
            
            # Force kill if still running
            if kill -0 $frontend_pid 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force killing frontend...${NC}"
                kill -KILL $frontend_pid
            fi
        fi
        rm -f .frontend.pid
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    else
        # Try to kill by port
        kill_process_on_port 3000 "Frontend"
    fi
    
    # Kill any remaining processes on our ports
    kill_process_on_port 8000 "Backend API"
    kill_process_on_port 3000 "Frontend"
fi

# Clean up temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f .backend.pid .frontend.pid

# Clean up logs if requested
if [ "$1" = "--clean" ] || [ "$2" = "--clean" ]; then
    echo -e "${YELLOW}🧹 Cleaning up log files...${NC}"
    rm -rf logs/*
    echo -e "${GREEN}✅ Log files cleaned${NC}"
fi

# Verify services are stopped
echo -e "\n${PURPLE}🔍 Verifying services are stopped...${NC}"
if check_port 8000; then
    echo -e "${RED}❌ Backend API is still running on port 8000${NC}"
else
    echo -e "${GREEN}✅ Backend API is stopped${NC}"
fi

if check_port 3000; then
    echo -e "${RED}❌ Frontend is still running on port 3000${NC}"
else
    echo -e "${GREEN}✅ Frontend is stopped${NC}"
fi

echo -e "\n${GREEN}🎉 Compliance Reports System stopped successfully!${NC}"
echo -e "${YELLOW}💡 Use './start.sh' to start the system again${NC}" 