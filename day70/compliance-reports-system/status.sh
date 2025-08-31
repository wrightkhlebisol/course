#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
POSTGRES_PORT=5432
REDIS_PORT=6379

echo -e "${BLUE}📊 Compliance Reports System Status${NC}"
echo -e "${BLUE}===================================${NC}"

# Function to check if port is in use
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not running on port $port${NC}"
        return 1
    fi
}

# Function to check HTTP service
check_http_service() {
    local url=$1
    local service_name=$2
    
    if curl -s "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is responding at $url${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not responding at $url${NC}"
        return 1
    fi
}

# Function to get service info
get_service_info() {
    local url=$1
    local service_name=$2
    
    if curl -s "$url" >/dev/null 2>&1; then
        echo -e "${CYAN}📋 $service_name Information:${NC}"
        curl -s "$url" | jq '.' 2>/dev/null || echo "   Raw response: $(curl -s "$url" | head -c 200)..."
    fi
}

# Check Docker containers if available
if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
    echo -e "\n${PURPLE}🐳 Docker Container Status${NC}"
    echo -e "${PURPLE}=======================${NC}"
    
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ Docker containers are running${NC}"
        docker-compose ps
    else
        echo -e "${RED}❌ No Docker containers are running${NC}"
    fi
fi

# Check individual services
echo -e "\n${PURPLE}🔍 Service Status${NC}"
echo -e "${PURPLE}================${NC}"

backend_running=false
frontend_running=false

# Check backend
if check_port 8000 "Backend API"; then
    backend_running=true
    if check_http_service "$BACKEND_URL/" "Backend API"; then
        get_service_info "$BACKEND_URL/" "Backend API"
    fi
fi

# Check frontend
if check_port 3000 "Frontend"; then
    frontend_running=true
    if check_http_service "$FRONTEND_URL" "Frontend"; then
        echo -e "${CYAN}📋 Frontend is accessible at $FRONTEND_URL${NC}"
    fi
fi

# Check database
check_port $POSTGRES_PORT "PostgreSQL Database"

# Check Redis
check_port $REDIS_PORT "Redis Cache"

# Check PID files for manual mode
echo -e "\n${PURPLE}📁 Process Files${NC}"
echo -e "${PURPLE}================${NC}"

if [ -f ".backend.pid" ]; then
    local backend_pid=$(cat .backend.pid)
    if [ ! -z "$backend_pid" ] && kill -0 $backend_pid 2>/dev/null; then
        echo -e "${GREEN}✅ Backend PID file exists (PID: $backend_pid)${NC}"
    else
        echo -e "${RED}❌ Backend PID file exists but process is not running${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  No backend PID file found${NC}"
fi

if [ -f ".frontend.pid" ]; then
    local frontend_pid=$(cat .frontend.pid)
    if [ ! -z "$frontend_pid" ] && kill -0 $frontend_pid 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend PID file exists (PID: $frontend_pid)${NC}"
    else
        echo -e "${RED}❌ Frontend PID file exists but process is not running${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  No frontend PID file found${NC}"
fi

# Check log files
echo -e "\n${PURPLE}📄 Log Files${NC}"
echo -e "${PURPLE}============${NC}"

if [ -d "logs" ]; then
    if [ -f "logs/backend.log" ]; then
        echo -e "${GREEN}✅ Backend log file exists${NC}"
        echo -e "${CYAN}   Last 3 lines:${NC}"
        tail -3 logs/backend.log 2>/dev/null || echo "   (empty or unreadable)"
    else
        echo -e "${YELLOW}ℹ️  No backend log file found${NC}"
    fi
    
    if [ -f "logs/frontend.log" ]; then
        echo -e "${GREEN}✅ Frontend log file exists${NC}"
        echo -e "${CYAN}   Last 3 lines:${NC}"
        tail -3 logs/frontend.log 2>/dev/null || echo "   (empty or unreadable)"
    else
        echo -e "${YELLOW}ℹ️  No frontend log file found${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  No logs directory found${NC}"
fi

# System summary
echo -e "\n${PURPLE}📊 System Summary${NC}"
echo -e "${PURPLE}================${NC}"

if $backend_running && $frontend_running; then
    echo -e "${GREEN}🎉 System is fully operational!${NC}"
    echo -e "${CYAN}🌐 Dashboard: $FRONTEND_URL${NC}"
    echo -e "${CYAN}📚 API Docs: $BACKEND_URL/docs${NC}"
    echo -e "${CYAN}🔌 API Base: $BACKEND_URL${NC}"
elif $backend_running; then
    echo -e "${YELLOW}⚠️  Backend is running but frontend is not${NC}"
elif $frontend_running; then
    echo -e "${YELLOW}⚠️  Frontend is running but backend is not${NC}"
else
    echo -e "${RED}❌ System is not running${NC}"
    echo -e "${YELLOW}💡 Use './start.sh' to start the system${NC}"
fi

# Quick actions
echo -e "\n${PURPLE}⚡ Quick Actions${NC}"
echo -e "${PURPLE}===============${NC}"
echo -e "${CYAN}./start.sh${NC}     - Start the system"
echo -e "${CYAN}./stop.sh${NC}      - Stop the system"
echo -e "${CYAN}./demo.sh${NC}      - Run interactive demo"
echo -e "${CYAN}./status.sh${NC}    - Check system status (this script)" 