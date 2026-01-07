#!/bin/bash

# Mobile Device Test Startup Script
# Uses HTTP instead of HTTPS for better mobile compatibility

set -e

# Configuration
BACKEND_PORT=8001
FRONTEND_PORT=5173
LOG_DIR="backend/logs"
VENV_PATH=".venv"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📱 Mobile Device Test Startup Script${NC}"
echo "=========================================="
echo -e "${YELLOW}This script uses HTTP instead of HTTPS for mobile compatibility${NC}"
echo ""

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment does not exist, creating...${NC}"
    python3 -m venv $VENV_PATH
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source $VENV_PATH/bin/activate

# Install dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r backend/requirements.txt

# Check port usage
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        lsof -i :$port
        return 1
    fi
    return 0
}

# Start backend
start_backend() {
    echo -e "${BLUE}🔧 Starting backend service (port $BACKEND_PORT)...${NC}"
    
    if ! check_port $BACKEND_PORT; then
        echo -e "${YELLOW}💡 Attempting to terminate processes using the port...${NC}"
        lsof -ti :$BACKEND_PORT | xargs kill -9
        sleep 2
    fi
    
    cd backend
    echo -e "${GREEN}✅ Backend started successfully!${NC}"
    echo -e "${BLUE}📊 Access URL: http://172.20.10.3:$BACKEND_PORT${NC}"
    echo -e "${BLUE}🔍 Health check: http://172.20.10.3:$BACKEND_PORT/health${NC}"
    echo ""
    
    # Start backend service
    uvicorn app:app --reload --host 0.0.0.0 --port $BACKEND_PORT
}

# Start frontend (HTTP mode)
start_frontend() {
    echo -e "${BLUE}🎨 Starting frontend service in HTTP mode (port $FRONTEND_PORT)...${NC}"
    
    if ! check_port $FRONTEND_PORT; then
        echo -e "${YELLOW}⚠️  Port $FRONTEND_PORT is already in use${NC}"
        return 1
    fi
    
    cd frontend
    echo -e "${GREEN}✅ Frontend started successfully in HTTP mode!${NC}"
            echo -e "${BLUE}🌐 Access URL: http://172.20.10.3:$FRONTEND_PORT${NC}"
    echo -e "${YELLOW}💡 Note: Using HTTP mode for mobile compatibility${NC}"
    echo ""
    
    # Start frontend service with HTTP config
    npm run dev -- --config vite.config.http.js
}

# Start complete system
start_complete() {
    echo -e "${BLUE}🚀 Starting complete system in HTTP mode...${NC}"
    
    # Start backend in background
    start_backend &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 3
    
    # Start frontend
    start_frontend &
    FRONTEND_PID=$!
    
    echo -e "${GREEN}✅ Both services started!${NC}"
    echo -e "${BLUE}📱 Mobile device access URLs:${NC}"
            echo -e "   Backend:  http://172.20.10.3:$BACKEND_PORT"
        echo -e "   Frontend: http://172.20.10.3:$FRONTEND_PORT"
    echo ""
    echo -e "${YELLOW}💡 Press Ctrl+C to stop both services${NC}"
    
    # Wait for user to stop
    wait
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}Please select an operation:${NC}"
    echo "1) Start backend service (HTTP)"
    echo "2) Start frontend service (HTTP mode)"
    echo "3) Start complete system (HTTP mode)"
    echo "4) Check system status"
    echo "5) Test mobile connectivity"
    echo "0) Exit"
    echo ""
    read -p "Please enter option (0-5): " choice
}

# Check system status
check_status() {
    echo -e "${BLUE}🔍 Checking system status...${NC}"
    echo ""
    
    # Check backend
    if check_port $BACKEND_PORT; then
        echo -e "${GREEN}✅ Backend service: Not running${NC}"
    else
        echo -e "${GREEN}✅ Backend service: Running (port $BACKEND_PORT)${NC}"
    fi
    
    # Check frontend
    if check_port $FRONTEND_PORT; then
        echo -e "${GREEN}✅ Frontend service: Not running${NC}"
    else
        echo -e "${GREEN}✅ Frontend service: Running (port $FRONTEND_PORT)${NC}"
    fi
}

# Test mobile connectivity
test_mobile() {
    echo -e "${BLUE}📱 Testing mobile connectivity...${NC}"
    echo ""
    
    # Get current IP
    CURRENT_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    
    if [ -n "$CURRENT_IP" ]; then
        echo -e "${GREEN}Current IP: $CURRENT_IP${NC}"
        echo ""
        echo -e "${BLUE}Testing backend...${NC}"
        if curl -s "http://$CURRENT_IP:$BACKEND_PORT/health" > /dev/null; then
            echo -e "${GREEN}✅ Backend accessible at http://$CURRENT_IP:$BACKEND_PORT${NC}"
        else
            echo -e "${RED}❌ Backend not accessible${NC}"
        fi
        
        echo ""
        echo -e "${BLUE}Testing frontend...${NC}"
        if curl -s "http://$CURRENT_IP:$FRONTEND_PORT" > /dev/null; then
            echo -e "${GREEN}✅ Frontend accessible at http://$CURRENT_IP:$FRONTEND_PORT${NC}"
        else
            echo -e "${RED}❌ Frontend not accessible${NC}"
        fi
        
        echo ""
        echo -e "${YELLOW}📱 Mobile device test URLs:${NC}"
        echo "Backend:  http://$CURRENT_IP:$BACKEND_PORT"
        echo "Frontend: http://$CURRENT_IP:$FRONTEND_PORT"
    else
        echo -e "${RED}❌ Could not determine current IP address${NC}"
    fi
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1)
            start_backend
            ;;
        2)
            start_frontend
            ;;
        3)
            start_complete
            ;;
        4)
            check_status
            ;;
        5)
            test_mobile
            ;;
        0)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option. Please try again.${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
