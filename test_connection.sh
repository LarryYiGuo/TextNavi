#!/bin/bash

# VLN WebAPP Connection Test Script
# Tests both backend and frontend services

set -e

# Configuration
BACKEND_IP="172.20.10.3"
BACKEND_PORT="8001"
FRONTEND_IP="172.20.10.3"
FRONTEND_PORT="5173"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 VLN WebAPP Connection Test${NC}"
echo "=================================="

# Test backend service
echo -e "${BLUE}📊 Testing Backend Service...${NC}"
if curl -s "http://$BACKEND_IP:$BACKEND_PORT/health" > /dev/null; then
    echo -e "${GREEN}✅ Backend service is accessible at http://$BACKEND_IP:$BACKEND_PORT${NC}"
    echo -e "${GREEN}   Health check response:${NC}"
    curl -s "http://$BACKEND_IP:$BACKEND_PORT/health" | python3 -m json.tool 2>/dev/null || curl -s "http://$BACKEND_IP:$BACKEND_PORT/health"
else
    echo -e "${RED}❌ Backend service is NOT accessible at http://$BACKEND_IP:$BACKEND_PORT${NC}"
fi

echo ""

# Test frontend service (HTTPS)
echo -e "${BLUE}🎨 Testing Frontend Service (HTTPS)...${NC}"
if curl -s -k "https://$FRONTEND_IP:$FRONTEND_PORT" > /dev/null; then
    echo -e "${GREEN}✅ Frontend service is accessible at https://$FRONTEND_IP:$FRONTEND_PORT${NC}"
    echo -e "${YELLOW}   Note: Using -k flag to ignore SSL certificate verification${NC}"
else
    echo -e "${RED}❌ Frontend service is NOT accessible at https://$FRONTEND_IP:$FRONTEND_PORT${NC}"
fi

echo ""

# Test frontend service (HTTP)
echo -e "${BLUE}🎨 Testing Frontend Service (HTTP)...${NC}"
if curl -s "http://$FRONTEND_IP:$FRONTEND_PORT" > /dev/null; then
    echo -e "${GREEN}✅ Frontend service is accessible at http://$FRONTEND_IP:$FRONTEND_PORT${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend service is NOT accessible at http://$FRONTEND_IP:$FRONTEND_PORT (expected for HTTPS-only config)${NC}"
fi

echo ""

# Test localhost connections
echo -e "${BLUE}🏠 Testing Localhost Connections...${NC}"
if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
    echo -e "${GREEN}✅ Backend localhost: http://localhost:$BACKEND_PORT${NC}"
else
    echo -e "${RED}❌ Backend localhost: http://localhost:$BACKEND_PORT${NC}"
fi

if curl -s -k "https://localhost:$FRONTEND_PORT" > /dev/null; then
    echo -e "${GREEN}✅ Frontend localhost: https://localhost:$FRONTEND_PORT${NC}"
else
    echo -e "${RED}❌ Frontend localhost: https://localhost:$FRONTEND_PORT${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}📋 Connection Summary:${NC}"
echo "Backend:  http://$BACKEND_IP:$BACKEND_PORT"
echo "Frontend: https://$FRONTEND_IP:$FRONTEND_PORT"
echo ""
echo -e "${YELLOW}💡 If services are accessible but you can't open them in browser:${NC}"
echo "1. Check if you're on the same network (UCL eduroam)"
echo "2. Try accessing from a different device on the same network"
echo "3. Check if there are any firewall restrictions"
echo "4. Verify the IP address hasn't changed"
echo ""
echo -e "${GREEN}🎯 Test completed!${NC}"
