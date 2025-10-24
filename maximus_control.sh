#!/bin/bash
# MAXIMUS Organism Control Script
# Controls the entire Vértice Cyber-Organism

set -e

SERVICES_BASE="/home/juan/vertice-dev/backend/services"
MASTER_COMPOSE="/home/juan/vertice-dev/docker-compose.ALL-SIDECARS-MASTER.yml"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

case "$1" in
  start)
    echo -e "${GREEN}🚀 STARTING VÉRTICE CYBER-ORGANISM${NC}"
    echo "========================================"
    
    # Start infrastructure
    echo -e "${YELLOW}Phase 1: Infrastructure...${NC}"
    docker start maximus-postgres hcl-postgres 2>/dev/null || true
    
    # Start all sidecars
    echo -e "${YELLOW}Phase 2: Service Registry & Sidecars...${NC}"
    docker compose -f "$MASTER_COMPOSE" up -d 2>&1 | grep -E "(Started|Running)" || echo "Sidecars already running"
    
    # Start organism services
    echo -e "${YELLOW}Phase 3: Organism Services...${NC}"
    bash /tmp/start_organism.sh 2>&1 | tail -10
    
    echo ""
    echo -e "${GREEN}✅ Organism activation complete${NC}"
    echo "Waiting 30s for full initialization..."
    sleep 30
    
    # Status
    REGISTERED=$(curl -s http://localhost:8888/services | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    CONTAINERS=$(docker ps | wc -l)
    echo ""
    echo "Status:"
    echo "  Containers UP: $((CONTAINERS-1))"
    echo "  Services Registered: $REGISTERED"
    ;;
    
  stop)
    echo -e "${RED}🛑 STOPPING VÉRTICE CYBER-ORGANISM${NC}"
    echo "========================================"
    
    # Stop in reverse order
    echo -e "${YELLOW}Stopping organism services...${NC}"
    docker stop $(docker ps --filter "name=immunis" --filter "name=cortex" --filter "name=thalamus" --filter "name=sensory" --filter "name=architect" --filter "name=command" --filter "name=narrative" --filter "name=memory" --filter "name=homeostatic" --filter "name=adaptive" -q) 2>/dev/null || true
    
    echo -e "${YELLOW}Stopping sidecars...${NC}"
    docker compose -f "$MASTER_COMPOSE" down 2>&1 | grep -E "(Stopped|Removed)" || echo "Sidecars stopped"
    
    echo -e "${YELLOW}Stopping infrastructure...${NC}"
    docker stop maximus-postgres hcl-postgres 2>/dev/null || true
    
    echo ""
    echo -e "${GREEN}✅ Organism stopped${NC}"
    ;;
    
  status)
    echo "VÉRTICE CYBER-ORGANISM STATUS"
    echo "=============================="
    echo ""
    
    TOTAL=$(docker ps | wc -l)
    ORGANISM=$(docker ps --format "{{.Names}}" | grep -E "(immunis|cortex|thalamus|sensory|architect|command)" | wc -l)
    REGISTERED=$(curl -s http://localhost:8888/services 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" || echo "Registry offline")
    
    echo "Containers UP: $((TOTAL-1))"
    echo "Organism Services: $ORGANISM"
    echo "Services Registered: $REGISTERED"
    echo ""
    echo "Key Systems:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(immunis|cortex|maximus-core|thalamus)" | head -10
    ;;
    
  *)
    echo "Usage: $0 {start|stop|status}"
    echo ""
    echo "Commands:"
    echo "  start  - Start the entire cyber-organism"
    echo "  stop   - Stop the entire cyber-organism"
    echo "  status - Show organism status"
    exit 1
    ;;
esac
