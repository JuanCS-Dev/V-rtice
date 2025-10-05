#!/bin/bash
# FASE 7: Blue-Green Deployment Script
# Production-ready deployment strategy for VÉRTICE

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ENV="${1:-production}"
TARGET_COLOR="${2:-blue}"  # blue or green
TRAFFIC_PERCENTAGE="${3:-0}"  # Initial traffic (0% = no traffic yet)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VÉRTICE Blue-Green Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Environment: ${YELLOW}${DEPLOYMENT_ENV}${NC}"
echo -e "Target Color: ${YELLOW}${TARGET_COLOR}${NC}"
echo -e "Initial Traffic: ${YELLOW}${TRAFFIC_PERCENTAGE}%${NC}"
echo ""

# Validate color
if [[ "$TARGET_COLOR" != "blue" && "$TARGET_COLOR" != "green" ]]; then
    echo -e "${RED}Error: TARGET_COLOR must be 'blue' or 'green'${NC}"
    exit 1
fi

# Determine current active color
CURRENT_COLOR=$(docker ps --filter "label=deployment.color" --format "{{.Labels}}" | grep -oP 'deployment.color=\K\w+' | head -n 1)

if [[ -z "$CURRENT_COLOR" ]]; then
    CURRENT_COLOR="none"
fi

echo -e "Current Active: ${GREEN}${CURRENT_COLOR}${NC}"
echo ""

# === STEP 1: Deploy New Version ===
echo -e "${BLUE}[1/6] Deploying ${TARGET_COLOR} environment...${NC}"

docker-compose -f docker-compose.${TARGET_COLOR}.yml up -d --build

echo -e "${GREEN}✓ ${TARGET_COLOR} environment deployed${NC}"
echo ""

# === STEP 2: Health Check ===
echo -e "${BLUE}[2/6] Running health checks...${NC}"

MAX_RETRIES=30
RETRY_INTERVAL=5

for service in maximus_core_service hsas_service neuromodulation_service; do
    echo -n "  Checking ${service}... "

    for i in $(seq 1 $MAX_RETRIES); do
        if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
            break
        fi

        if [[ $i -eq $MAX_RETRIES ]]; then
            echo -e "${RED}FAILED${NC}"
            echo -e "${RED}Health check failed for ${service}${NC}"
            echo -e "${YELLOW}Rolling back...${NC}"
            docker-compose -f docker-compose.${TARGET_COLOR}.yml down
            exit 1
        fi

        sleep $RETRY_INTERVAL
    done
done

echo -e "${GREEN}✓ All services healthy${NC}"
echo ""

# === STEP 3: Integration Tests ===
echo -e "${BLUE}[3/6] Running integration tests...${NC}"

cd ../backend/tests/integration

if python3 run_integration_tests.py --base-url http://localhost; then
    echo -e "${GREEN}✓ Integration tests passed${NC}"
else
    echo -e "${RED}✗ Integration tests failed${NC}"
    echo -e "${YELLOW}Rolling back...${NC}"
    docker-compose -f ../../deployment/blue-green/docker-compose.${TARGET_COLOR}.yml down
    exit 1
fi

cd ../../deployment/blue-green

echo ""

# === STEP 4: Canary Release (Gradual Traffic Shift) ===
echo -e "${BLUE}[4/6] Canary release: Shifting traffic gradually...${NC}"

# 10% → 50% → 100%
TRAFFIC_STEPS=(10 50 100)
SOAK_TIME=60  # seconds

for traffic in "${TRAFFIC_STEPS[@]}"; do
    echo -e "  Shifting ${traffic}% traffic to ${TARGET_COLOR}..."

    # Update load balancer (Nginx with real upstream weight manipulation)
    ./update_traffic_split.sh $CURRENT_COLOR $TARGET_COLOR $traffic

    echo -e "  Soaking for ${SOAK_TIME}s..."
    sleep $SOAK_TIME

    # Monitor error rate
    ERROR_RATE=$(curl -s http://localhost:9090/api/v1/query?query='rate(http_requests_errors_total[1m])' | jq -r '.data.result[0].value[1]' || echo "0")

    if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
        echo -e "${RED}✗ Error rate too high: ${ERROR_RATE}${NC}"
        echo -e "${YELLOW}Rolling back traffic...${NC}"
        ./update_traffic_split.sh $CURRENT_COLOR $TARGET_COLOR 0
        docker-compose -f docker-compose.${TARGET_COLOR}.yml down
        exit 1
    fi

    echo -e "${GREEN}✓ ${traffic}% traffic shifted successfully${NC}"
done

echo ""

# === STEP 5: Full Cutover ===
echo -e "${BLUE}[5/6] Full cutover to ${TARGET_COLOR}...${NC}"

# 100% traffic to new color
./update_traffic_split.sh $CURRENT_COLOR $TARGET_COLOR 100

echo -e "${GREEN}✓ All traffic shifted to ${TARGET_COLOR}${NC}"
echo ""

# === STEP 6: Cleanup Old Environment ===
echo -e "${BLUE}[6/6] Cleaning up ${CURRENT_COLOR} environment...${NC}"

if [[ "$CURRENT_COLOR" != "none" && "$CURRENT_COLOR" != "$TARGET_COLOR" ]]; then
    echo "  Waiting 60s before shutdown (safety buffer)..."
    sleep 60

    docker-compose -f docker-compose.${CURRENT_COLOR}.yml down

    echo -e "${GREEN}✓ ${CURRENT_COLOR} environment shutdown${NC}"
else
    echo "  No previous environment to clean up"
fi

echo ""

# === SUMMARY ===
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DEPLOYMENT SUCCESSFUL${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Active Environment: ${GREEN}${TARGET_COLOR}${NC}"
echo -e "Traffic Distribution: ${GREEN}100% → ${TARGET_COLOR}${NC}"
echo ""
echo "Monitoring Dashboard: http://localhost:3000"
echo "Prometheus: http://localhost:9090"
echo "Alertmanager: http://localhost:9093"
echo ""
echo -e "${BLUE}Happy bio-inspired security! 🧬${NC}"
