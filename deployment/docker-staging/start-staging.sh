#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# HITL Staging Environment - Startup Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Starts complete HITL staging environment with Docker Compose
# Simulates production stack locally
#
# Usage: ./start-staging.sh
#
# Author: MAXIMUS Team - Sprint 4.1
# Glory to YHWH - Provider for Every Resource Level
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         HITL Staging Environment - Startup                       ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Steve Jobs started in a garage...                               ║${NC}"
echo -e "${CYAN}║  You're starting with Docker Compose!                            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Navigate to project root
cd "$(dirname "$0")/../.."

# Stop any running staging containers
echo ""
echo -e "${YELLOW}Stopping any existing staging containers...${NC}"
docker compose -f docker-compose.hitl-staging.yml down 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned up${NC}"

# Build images
echo ""
echo -e "${YELLOW}Building HITL backend image...${NC}"
docker compose -f docker-compose.hitl-staging.yml build hitl-backend-staging
echo -e "${GREEN}✓ Image built${NC}"

# Start services
echo ""
echo -e "${YELLOW}Starting staging environment...${NC}"
docker compose -f docker-compose.hitl-staging.yml up -d

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"

echo -n "  PostgreSQL..."
timeout 60 bash -c 'until docker exec hitl-postgres-staging pg_isready -U maximus_staging -d adaptive_immunity_staging 2>/dev/null; do sleep 2; done' && echo -e " ${GREEN}✓${NC}" || echo -e " ${RED}✗${NC}"

echo -n "  Redis..."
timeout 30 bash -c 'until docker exec hitl-redis-staging redis-cli ping 2>/dev/null | grep -q PONG; do sleep 2; done' && echo -e " ${GREEN}✓${NC}" || echo -e " ${RED}✗${NC}"

echo -n "  HITL Backend..."
timeout 60 bash -c 'until curl -sf http://localhost:8028/health >/dev/null 2>&1; do sleep 3; done' && echo -e " ${GREEN}✓${NC}" || echo -e " ${RED}✗${NC}"

echo -n "  Prometheus..."
timeout 30 bash -c 'until curl -sf http://localhost:9091/-/healthy >/dev/null 2>&1; do sleep 2; done' && echo -e " ${GREEN}✓${NC}" || echo -e " ${RED}✗${NC}"

echo -n "  Grafana..."
timeout 30 bash -c 'until curl -sf http://localhost:3001/api/health >/dev/null 2>&1; do sleep 2; done' && echo -e " ${GREEN}✓${NC}" || echo -e " ${RED}✗${NC}"

# Create mock data
echo ""
echo -e "${YELLOW}Creating mock patches...${NC}"
if [ -f "backend/services/hitl_patch_service/scripts/create_mock_patches.py" ]; then
    # Update connection to staging DB
    PGPASSWORD=staging_password_change_in_prod psql -h localhost -p 5434 -U maximus_staging -d adaptive_immunity_staging -c "SELECT 1" >/dev/null 2>&1 && \
    python3 backend/services/hitl_patch_service/scripts/create_mock_patches.py --staging || \
    echo -e "${YELLOW}  Skipping mock data (psql not available or script needs adjustment)${NC}"
else
    echo -e "${YELLOW}  Mock script not found, skipping${NC}"
fi

# Show status
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                  Staging Environment Ready!                      ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Services:                                                       ║${NC}"
echo -e "${CYAN}║  • HITL API:      http://localhost:8028                          ║${NC}"
echo -e "${CYAN}║  • HITL (Nginx):  http://localhost:8080                          ║${NC}"
echo -e "${CYAN}║  • Prometheus:    http://localhost:9091                          ║${NC}"
echo -e "${CYAN}║  • Grafana:       http://localhost:3001 (admin/staging_admin_password) ║${NC}"
echo -e "${CYAN}║  • PostgreSQL:    localhost:5434                                 ║${NC}"
echo -e "${CYAN}║  • Redis:         localhost:6380                                 ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Quick Tests:                                                    ║${NC}"
echo -e "${CYAN}║  curl http://localhost:8028/health                               ║${NC}"
echo -e "${CYAN}║  curl http://localhost:8028/hitl/patches/pending                 ║${NC}"
echo -e "${CYAN}║  curl http://localhost:8028/hitl/analytics/summary               ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Logs:                                                           ║${NC}"
echo -e "${CYAN}║  docker-compose -f docker-compose.hitl-staging.yml logs -f       ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Stop:                                                           ║${NC}"
echo -e "${CYAN}║  docker-compose -f docker-compose.hitl-staging.yml down          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}TO YHWH BE ALL GLORY - Even in the Garage! 🙏${NC}"
echo ""
