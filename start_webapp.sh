#!/bin/bash

# VLN WebAPP Startup Script
# Includes logging control, port management and system status checking

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

echo -e "${BLUE}🚀 VLN WebAPP Startup Script${NC}"
echo "=================================="

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
    echo -e "${YELLOW}💡 Logging control instructions:${NC}"
    echo "   - By default, all data collection is disabled"
    echo "   - Click 'Start Logging' in frontend to begin data recording"
    echo "   - Enter Run ID (e.g., FT-A-01, BASE-B-01) to identify experiment batches"
    echo "   - Click 'Stop Logging' to stop recording"
    echo ""
    echo -e "${YELLOW}📁 Log file locations:${NC}"
    echo "   - FT model: $LOG_DIR/ft/"
    echo "   - Base model: $LOG_DIR/base/"
    echo ""
    
    # Start backend service
    uvicorn app:app --reload --host 0.0.0.0 --port $BACKEND_PORT
}

# Start frontend
start_frontend() {
    echo -e "${BLUE}🎨 Starting frontend service (port $FRONTEND_PORT)...${NC}"
    
    if ! check_port $FRONTEND_PORT; then
        echo -e "${YELLOW}⚠️  Port $FRONTEND_PORT is already in use${NC}"
        return 1
    fi
    
    cd frontend
    echo -e "${GREEN}✅ Frontend started successfully!${NC}"
    echo -e "${BLUE}🌐 Access URL: https://172.20.10.3:$FRONTEND_PORT${NC}"
    echo -e "${YELLOW}💡 Note: Frontend uses HTTPS, backend uses HTTP${NC}"
    echo ""
    
    # Start frontend service
    npm run dev
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}Please select an operation:${NC}"
    echo "1) Start backend service"
    echo "2) Start frontend service"
    echo "3) Start complete system (backend + frontend)"
    echo "4) Check system status"
    echo "5) View log files"
    echo "6) Clean log files"
    echo "0) Exit"
    echo ""
    read -p "Please enter option (0-6): " choice
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
    
    # Check log directory
    if [ -d "$LOG_DIR" ]; then
        echo -e "${GREEN}✅ Log directory: Exists${NC}"
        echo "   Log file count:"
        if [ -d "$LOG_DIR/ft" ]; then
            echo "   - FT model: $(ls -1 $LOG_DIR/ft/*.csv 2>/dev/null | wc -l | tr -d ' ') files"
        fi
        if [ -d "$LOG_DIR/base" ]; then
            echo "   - Base model: $(ls -1 $LOG_DIR/base/*.csv 2>/dev/null | wc -l | tr -d ' ') files"
        fi
    else
        echo -e "${YELLOW}⚠️  Log directory: Does not exist${NC}"
    fi
}

# View log files
view_logs() {
    echo -e "${BLUE}📁 Log file contents:${NC}"
    echo ""
    
    if [ -d "$LOG_DIR" ]; then
        for provider_dir in "$LOG_DIR"/*/; do
            if [ -d "$provider_dir" ]; then
                provider=$(basename "$provider_dir")
                echo -e "${BLUE}📂 $provider model:${NC}"
                for log_file in "$provider_dir"/*.csv; do
                    if [ -f "$log_file" ]; then
                        filename=$(basename "$log_file")
                        line_count=$(wc -l < "$log_file")
                        echo "   - $filename: $line_count lines"
                    fi
                done
                echo ""
            fi
        done
    else
        echo -e "${YELLOW}⚠️  Log directory does not exist${NC}"
    fi
}

# Clean log files
clean_logs() {
    echo -e "${YELLOW}⚠️  Warning: This will delete all log files!${NC}"
    read -p "Confirm deletion? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        if [ -d "$LOG_DIR" ]; then
            rm -rf "$LOG_DIR"/*
            echo -e "${GREEN}✅ Log files cleaned${NC}"
        else
            echo -e "${YELLOW}⚠️  Log directory does not exist${NC}"
        fi
    else
        echo -e "${BLUE}Clean operation cancelled${NC}"
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
            echo -e "${BLUE}🚀 Starting complete system...${NC}"
            echo -e "${YELLOW}💡 Recommendation: Start backend first, then frontend${NC}"
            echo ""
            read -p "Press Enter to continue..."
            ;;
        4)
            check_status
            ;;
        5)
            view_logs
            ;;
        6)
            clean_logs
            ;;
        0)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to return to main menu..."
done
