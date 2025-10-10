#!/bin/bash
# Multi-Agent Demo - Platelet Digital Communication
# 
# Demonstrates 3 platelet agents communicating via P2P signaling,
# detecting breach, and triggering coordinated response.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/../bin"
AGENT_BIN="$BIN_DIR/platelet-agent"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}🩸 PLATELET AGENT DEMO - Multi-Agent Communication${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════${NC}"
echo ""

# Check binary
if [ ! -f "$AGENT_BIN" ]; then
    echo -e "${RED}❌ Agent binary not found${NC}"
    echo -e "${YELLOW}Run: cd backend/coagulation && go build -o bin/platelet-agent ./platelet_agent/agent.go${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Agent binary found${NC}"
echo -e "${YELLOW}Note: This demo requires NATS on localhost:4222${NC}"
echo -e "${YELLOW}Run: docker run -d -p 4222:4222 nats:2.10-alpine -js${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping agents...${NC}"
    kill $AGENT1_PID $AGENT2_PID $AGENT3_PID 2>/dev/null || true
    wait 2>/dev/null || true
    echo -e "${GREEN}✅ Demo complete${NC}"
}

trap cleanup EXIT INT TERM

# Start 3 agents
echo -e "${CYAN}Starting Agent 1 (platelet-alpha, threshold=0.6)...${NC}"
$AGENT_BIN --id platelet-alpha --nats nats://localhost:4222 --threshold 0.6 &
AGENT1_PID=$!
sleep 1

echo -e "${CYAN}Starting Agent 2 (platelet-beta, threshold=0.7)...${NC}"
$AGENT_BIN --id platelet-beta --nats nats://localhost:4222 --threshold 0.7 &
AGENT2_PID=$!
sleep 1

echo -e "${CYAN}Starting Agent 3 (platelet-gamma, threshold=0.8)...${NC}"
$AGENT_BIN --id platelet-gamma --nats nats://localhost:4222 --threshold 0.8 &
AGENT3_PID=$!
sleep 2

echo ""
echo -e "${GREEN}✅ All 3 agents running and monitoring${NC}"
echo ""
echo -e "${MAGENTA}════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}📊 AGENTS CIRCULATING${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Agent 1 (alpha):${NC}  PID=$AGENT1_PID, Threshold=0.6"
echo -e "${CYAN}Agent 2 (beta):${NC}   PID=$AGENT2_PID, Threshold=0.7"
echo -e "${YELLOW}Agent 3 (gamma):${NC}  PID=$AGENT3_PID, Threshold=0.8"
echo ""
echo -e "${YELLOW}Agents will detect anomalies and communicate via NATS P2P.${NC}"
echo -e "${GREEN}Press Ctrl+C to stop${NC}"
echo ""

# Monitor
for i in {60..1}; do
    echo -ne "${CYAN}Demo running: ${i}s remaining  \r${NC}"
    sleep 1
done

echo ""
echo -e "${MAGENTA}\"As plaquetas circulam. A cascata se prepara.\" 🩸${NC}"
