#!/bin/bash
# MAXIMUS AI 3.0 + HSAS Service - Stack Startup Script
#
# REGRA DE OURO: Production-ready deployment script
# Author: Claude Code + JuanCS-Dev
# Date: 2025-10-06

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}MAXIMUS AI 3.0 + HSAS Service - Stack Startup${NC}"
echo -e "${BLUE}============================================================${NC}\n"

# ============================
# 1. Check Prerequisites
# ============================
echo -e "${YELLOW}[1/5]${NC} Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Docker Compose installed${NC}"

# ============================
# 2. Check .env File
# ============================
echo -e "\n${YELLOW}[2/5]${NC} Checking environment configuration..."

cd "${PROJECT_ROOT}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}  ⚠  .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}  ✓ .env created from .env.example${NC}"
        echo -e "${YELLOW}  ⚠  Please edit .env and add your API keys!${NC}"
    else
        echo -e "${RED}  ✗ .env.example not found!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  ✓ .env file exists${NC}"
fi

# Check if API keys are set
if grep -q "your_.*_api_key_here" .env; then
    echo -e "${YELLOW}  ⚠  Warning: Default API keys detected in .env${NC}"
    echo -e "${YELLOW}     Some features may not work without valid API keys${NC}"
fi

# ============================
# 3. Create Required Directories
# ============================
echo -e "\n${YELLOW}[3/5]${NC} Creating required directories..."

mkdir -p logs models
echo -e "${GREEN}  ✓ Directories created${NC}"

# ============================
# 4. Stop Existing Containers
# ============================
echo -e "\n${YELLOW}[4/5]${NC} Stopping existing containers (if any)..."

docker-compose -f docker-compose.maximus.yml down 2>/dev/null || true
echo -e "${GREEN}  ✓ Existing containers stopped${NC}"

# ============================
# 5. Start Services
# ============================
echo -e "\n${YELLOW}[5/5]${NC} Starting MAXIMUS AI 3.0 stack..."

# Build and start services
docker-compose -f docker-compose.maximus.yml up --build -d

echo -e "\n${GREEN}✓ Services starting...${NC}\n"

# ============================
# Wait for Services
# ============================
echo -e "${YELLOW}Waiting for services to be healthy...${NC}\n"

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "${url}" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ ${service} is healthy${NC}"
            return 0
        fi
        echo -ne "  Waiting for ${service}... (${attempt}/${max_attempts})\r"
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}  ✗ ${service} failed to start${NC}"
    return 1
}

# Check services
check_service "Redis" "http://localhost:6379" || true
check_service "PostgreSQL" "http://localhost:5432" || true
check_service "HSAS Service" "http://localhost:8023/health" || true
check_service "MAXIMUS Core" "http://localhost:8150/health" || true

# ============================
# Display Status
# ============================
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}Stack Status${NC}"
echo -e "${BLUE}============================================================${NC}\n"

docker-compose -f docker-compose.maximus.yml ps

echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}Service URLs${NC}"
echo -e "${BLUE}============================================================${NC}\n"

echo -e "  🧠 MAXIMUS Core:  ${GREEN}http://localhost:8150${NC}"
echo -e "  🎓 HSAS Service:  ${GREEN}http://localhost:8023${NC}"
echo -e "  🗄️  PostgreSQL:    ${GREEN}localhost:5432${NC}"
echo -e "  📦 Redis:         ${GREEN}localhost:6379${NC}"

echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}Useful Commands${NC}"
echo -e "${BLUE}============================================================${NC}\n"

echo -e "  View logs:        ${YELLOW}docker-compose -f docker-compose.maximus.yml logs -f${NC}"
echo -e "  Stop stack:       ${YELLOW}docker-compose -f docker-compose.maximus.yml down${NC}"
echo -e "  Restart service:  ${YELLOW}docker-compose -f docker-compose.maximus.yml restart <service>${NC}"
echo -e "  Run demo:         ${YELLOW}python demo/demo_maximus_complete.py${NC}"

echo -e "\n${GREEN}✅ MAXIMUS AI 3.0 stack is running!${NC}\n"
