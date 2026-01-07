#!/bin/bash

# Mobile Device Connection Test Script
# Tests connectivity from mobile device perspective

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

echo -e "${BLUE}📱 Mobile Device Connection Test${NC}"
echo "====================================="

# Test network interface binding
echo -e "${BLUE}🌐 Network Interface Test...${NC}"
echo "Current IP: $BACKEND_IP"
echo "Network mask: $(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $4}')"
echo "Broadcast: $(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $6}')"

echo ""

# Test service binding
echo -e "${BLUE}🔧 Service Binding Test...${NC}"
echo "Backend (8001):"
netstat -an | grep "8001" | grep "LISTEN" || echo "No backend listening"
echo "Frontend (5173):"
netstat -an | grep "5173" | grep "LISTEN" || echo "No frontend listening"

echo ""

# Test firewall status
echo -e "${BLUE}🔥 Firewall Test...${NC}"
if command -v ufw >/dev/null 2>&1; then
    ufw status
else
    echo "UFW not installed"
fi

echo ""

# Test from different network perspectives
echo -e "${BLUE}📡 Network Access Test...${NC}"

# Test localhost
echo "1. Localhost test:"
if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
    echo -e "   ${GREEN}✅ Backend localhost: OK${NC}"
else
    echo -e "   ${RED}❌ Backend localhost: FAILED${NC}"
fi

if curl -s -k "https://localhost:$FRONTEND_PORT" > /dev/null; then
    echo -e "   ${GREEN}✅ Frontend localhost: OK${NC}"
else
    echo -e "   ${RED}❌ Frontend localhost: FAILED${NC}"
fi

# Test from current IP
echo "2. Current IP test:"
if curl -s "http://$BACKEND_IP:$BACKEND_PORT/health" > /dev/null; then
    echo -e "   ${GREEN}✅ Backend current IP: OK${NC}"
else
    echo -e "   ${RED}❌ Backend current IP: FAILED${NC}"
fi

if curl -s -k "https://$FRONTEND_IP:$FRONTEND_PORT" > /dev/null; then
    echo -e "   ${GREEN}✅ Frontend current IP: OK${NC}"
else
    echo -e "   ${RED}❌ Frontend current IP: FAILED${NC}"
fi

# Test from 0.0.0.0 (all interfaces)
echo "3. All interfaces test:"
if curl -s "http://0.0.0.0:$BACKEND_PORT/health" > /dev/null; then
    echo -e "   ${GREEN}✅ Backend 0.0.0.0: OK${NC}"
else
    echo -e "   ${RED}❌ Backend 0.0.0.0: FAILED${NC}"
fi

echo ""

# Mobile device troubleshooting
echo -e "${BLUE}📱 Mobile Device Troubleshooting...${NC}"
echo -e "${YELLOW}Common issues and solutions:${NC}"
echo ""
echo "1. ${BLUE}Network Isolation:${NC}"
echo "   - UCL eduroam may isolate devices"
echo "   - Try connecting both devices to the same network"
echo ""
echo "2. ${BLUE}Firewall Restrictions:${NC}"
echo "   - Mobile carriers may block certain ports"
echo "   - Try using mobile data vs WiFi"
echo ""
echo "3. ${BLUE}Port Blocking:${NC}"
echo "   - Ports 8001 and 5173 may be blocked"
echo "   - Try different ports if possible"
echo ""
echo "4. ${BLUE}HTTPS Issues:${NC}"
echo "   - Mobile browsers are stricter with SSL"
echo "   - Consider switching to HTTP for testing"
echo ""

# Test alternative ports
echo -e "${BLUE}🔍 Alternative Port Test...${NC}"
echo "Testing if other ports are accessible:"
for port in 3000 8080 9000; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "   ${YELLOW}Port $port: IN USE${NC}"
    else
        echo -e "   ${GREEN}Port $port: AVAILABLE${NC}"
    fi
done

echo ""

# Summary and recommendations
echo -e "${BLUE}📋 Summary & Recommendations:${NC}"
echo "Current services:"
echo "  Backend:  http://$BACKEND_IP:$BACKEND_PORT"
echo "  Frontend: https://$FRONTEND_IP:$FRONTEND_PORT"
echo ""
echo -e "${YELLOW}For mobile access, try:${NC}"
echo "1. Use HTTP instead of HTTPS (if possible)"
echo "2. Check if both devices are on the same network"
echo "3. Try accessing from mobile browser with 'Advanced' → 'Proceed' for SSL"
echo "4. Check mobile device firewall settings"
echo "5. Try different mobile browsers (Chrome, Safari, Firefox)"
echo ""
echo -e "${GREEN}🎯 Test completed!${NC}"
