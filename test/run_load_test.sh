#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}🚀 FastAPI Load Testing Suite${NC}"
echo -e "${CYAN}========================================${NC}\n"

# Check if server is running
echo -e "${YELLOW}Checking if server is running...${NC}"
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo -e "${YELLOW}Please start the server first:${NC}"
    echo -e "  cd /home/sagomez/claude_practice"
    echo -e "  source claude_practice_venv/bin/activate"
    echo -e "  uvicorn main:app --reload"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}\n"

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source ../claude_practice_venv/bin/activate

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -r requirements.txt -q 2>/dev/null || pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}\n"

# Start monitoring in background
echo -e "${YELLOW}Starting system monitor...${NC}"
python3 monitor.py > /dev/null 2>&1 &
MONITOR_PID=$!
echo -e "${GREEN}✅ Monitor started (PID: $MONITOR_PID)${NC}\n"

# Give monitor time to start
sleep 2

# Run load tests
echo -e "${CYAN}Starting load tests...${NC}\n"
python3 load_test.py

# Wait for monitor to finish
echo -e "\n${YELLOW}Waiting for monitor to finish...${NC}"
sleep 5

# Kill monitor if still running
kill $MONITOR_PID 2>/dev/null

echo -e "\n${GREEN}✅ Load testing complete!${NC}"
echo -e "${CYAN}Results saved to: load_test_results.json${NC}\n"
