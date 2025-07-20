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
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

echo -e "${BLUE}🚀 Starting Compliance Reports System${NC}"
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

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}   Attempt $attempt/$max_attempts - $service_name not ready yet...${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed to start within expected time${NC}"
    return 1
}

# Check if Docker Compose is available and preferred
if command -v docker-compose &> /dev/null && [ "$1" != "--no-docker" ]; then
    echo -e "${CYAN}🐳 Starting with Docker Compose...${NC}"
    
    # Check if ports are already in use
    if check_port $BACKEND_PORT; then
        echo -e "${RED}❌ Port $BACKEND_PORT is already in use${NC}"
        exit 1
    fi
    
    if check_port $FRONTEND_PORT; then
        echo -e "${RED}❌ Port $FRONTEND_PORT is already in use${NC}"
        exit 1
    fi
    
    # Start Docker services
    echo -e "${YELLOW}📦 Building and starting Docker containers...${NC}"
    docker-compose up --build -d
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to start Docker containers${NC}"
        exit 1
    fi
    
    # Wait for services to be ready
    echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
    sleep 10
    
    # Check backend
    if wait_for_service "http://localhost:$BACKEND_PORT/" "Backend API"; then
        echo -e "${GREEN}✅ Backend API is running${NC}"
    else
        echo -e "${RED}❌ Backend API failed to start${NC}"
        docker-compose logs backend
        exit 1
    fi
    
    # Check frontend
    if wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend"; then
        echo -e "${GREEN}✅ Frontend is running${NC}"
    else
        echo -e "${RED}❌ Frontend failed to start${NC}"
        docker-compose logs frontend
        exit 1
    fi
    
    echo -e "${GREEN}✅ System started successfully with Docker!${NC}"
    
else
    echo -e "${CYAN}🔧 Starting services manually...${NC}"
    
    # Check if Python virtual environment exists
    if [ ! -d "backend/venv" ]; then
        echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
    fi
    
    # Check if Node modules exist
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
        cd frontend
        npm install
        cd ..
    fi
    
    # Check if ports are available
    if check_port $BACKEND_PORT; then
        echo -e "${RED}❌ Port $BACKEND_PORT is already in use${NC}"
        exit 1
    fi
    
    if check_port $FRONTEND_PORT; then
        echo -e "${RED}❌ Port $FRONTEND_PORT is already in use${NC}"
        exit 1
    fi
    
    # Start backend
    echo -e "${YELLOW}🔧 Starting backend...${NC}"
    cd backend
    source venv/bin/activate
    python app/main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend
    echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
    sleep 5
    
    if ! check_port $BACKEND_PORT; then
        echo -e "${RED}❌ Backend failed to start${NC}"
        cat logs/backend.log
        exit 1
    fi
    
    # Start frontend
    echo -e "${YELLOW}🔧 Starting frontend...${NC}"
    cd frontend
    npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend
    echo -e "${YELLOW}⏳ Waiting for frontend to start...${NC}"
    sleep 10
    
    if ! check_port $FRONTEND_PORT; then
        echo -e "${RED}❌ Frontend failed to start${NC}"
        cat logs/frontend.log
        exit 1
    fi
    
    # Save PIDs for cleanup
    echo $BACKEND_PID > .backend.pid
    echo $FRONTEND_PID > .frontend.pid
    
    echo -e "${GREEN}✅ System started successfully manually!${NC}"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Display system information
echo -e "\n${PURPLE}📊 System Information${NC}"
echo -e "${PURPLE}====================${NC}"
echo -e "${CYAN}🌐 Frontend Dashboard:${NC} http://localhost:$FRONTEND_PORT"
echo -e "${CYAN}🔌 Backend API:${NC} http://localhost:$BACKEND_PORT"
echo -e "${CYAN}📊 API Documentation:${NC} http://localhost:$BACKEND_PORT/docs"
echo -e "${CYAN}📋 OpenAPI Spec:${NC} http://localhost:$BACKEND_PORT/openapi.json"

# Run demo if requested
if [ "$1" = "--demo" ] || [ "$2" = "--demo" ]; then
    echo -e "\n${YELLOW}🎬 Running system demo...${NC}"
    sleep 3
    python scripts/demo.py
fi

echo -e "\n${GREEN}🎉 Compliance Reports System is ready!${NC}"
echo -e "${YELLOW}💡 Use './stop.sh' to stop the system${NC}"
echo -e "${YELLOW}💡 Use './demo.sh' to run the demo${NC}" 