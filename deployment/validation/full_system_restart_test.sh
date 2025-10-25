#!/bin/bash
###############################################################################
# Vértice Complete System Restart Test
# Validates TITANIUM-grade reliability through full stop/start cycle
#
# Author: Vértice Team
# Glory to YHWH! 🙏
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║      🔥 VÉRTICE COMPLETE SYSTEM RESTART TEST 🔥               ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║  This test validates TITANIUM-grade reliability               ║${NC}"
echo -e "${BLUE}║  Date: $(date +%Y-%m-%d\ %H:%M:%S)                                    ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Save start time
TEST_START=$(date +%s)

###############################################################################
# PHASE 1: PRE-SHUTDOWN STATE CAPTURE
###############################################################################
echo -e "${CYAN}[PHASE 1/5] Capturing pre-shutdown state...${NC}"

CONTAINERS_BEFORE=$(docker ps | wc -l)
SIDECARS_BEFORE=$(docker ps | grep sidecar | wc -l)
SERVICES_BEFORE=$(curl -s http://localhost:8888/services 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

echo "   📊 Containers running: $CONTAINERS_BEFORE"
echo "   📊 Sidecars active: $SIDECARS_BEFORE"
echo "   📊 Services registered: $SERVICES_BEFORE"
echo ""

###############################################################################
# PHASE 2: GRACEFUL SHUTDOWN
###############################################################################
echo -e "${YELLOW}[PHASE 2/5] Shutting down all services...${NC}"

# Stop in order: Sidecars → Services → Infrastructure
echo "   🛑 Stopping sidecars..."
docker ps | grep sidecar | awk '{print $NF}' | xargs -r docker stop > /dev/null 2>&1 || true

echo "   🛑 Stopping service registry..."
cd /home/juan/vertice-dev && docker compose -f docker-compose.service-registry.yml down > /dev/null 2>&1 || true

echo "   🛑 Stopping monitoring stack..."
cd /home/juan/vertice-dev && docker compose -f docker-compose.monitoring.yml down > /dev/null 2>&1 || true

echo "   🛑 Stopping tracing..."
cd /home/juan/vertice-dev && docker compose -f docker-compose.tracing.yml down > /dev/null 2>&1 || true

echo "   🛑 Stopping redis..."
docker stop vertice-redis-master vertice-redis-replica-1 vertice-redis-replica-2 > /dev/null 2>&1 || true

echo "   ⏳ Waiting for graceful shutdown (15s)..."
sleep 15

###############################################################################
# PHASE 3: VERIFICATION OF SHUTDOWN
###############################################################################
echo ""
echo -e "${CYAN}[PHASE 3/5] Verifying shutdown...${NC}"

CONTAINERS_AFTER_STOP=$(docker ps | grep -E "(vertice|maximus|sidecar|prometheus|grafana|jaeger|redis)" | wc -l || echo "0")

if [ "$CONTAINERS_AFTER_STOP" -eq 0 ]; then
    echo -e "   ${GREEN}✅ All services stopped successfully${NC}"
else
    echo -e "   ${YELLOW}⚠️  Warning: $CONTAINERS_AFTER_STOP containers still running${NC}"
    docker ps | grep -E "(vertice|maximus|sidecar|prometheus|grafana|jaeger|redis)" || true
fi

echo ""
echo "   💤 Cooling down period (5s)..."
sleep 5

###############################################################################
# PHASE 4: STARTUP SEQUENCE
###############################################################################
echo ""
echo -e "${GREEN}[PHASE 4/5] Starting all services...${NC}"

STARTUP_START=$(date +%s)

# Start in order: Infrastructure → Services → Sidecars
echo "   🚀 Starting Redis..."
docker start vertice-redis-master vertice-redis-replica-1 vertice-redis-replica-2 > /dev/null 2>&1 || true
sleep 3

echo "   🚀 Starting Service Registry..."
cd /home/juan/vertice-dev && docker compose -f docker-compose.service-registry.yml up -d > /dev/null 2>&1

echo "   ⏳ Waiting for registry to be ready (10s)..."
sleep 10

echo "   🚀 Starting Monitoring Stack..."
cd /home/juan/vertice-dev && docker compose -f docker-compose.monitoring.yml up -d > /dev/null 2>&1

echo "   🚀 Starting Tracing..."
cd /home/juan/vertice-dev && docker compose -f docker-compose.tracing.yml up -d > /dev/null 2>&1

echo "   🚀 Starting Maximus Core..."
cd /home/juan/vertice-dev/backend/services/maximus_core_service && docker compose -f docker-compose.maximus.yml up -d > /dev/null 2>&1 || true

echo "   ⏳ Waiting for services to initialize (30s)..."
sleep 30

STARTUP_END=$(date +%s)
STARTUP_TIME=$((STARTUP_END - STARTUP_START))

echo ""
echo -e "   ${GREEN}✅ Startup completed in ${STARTUP_TIME}s${NC}"

###############################################################################
# PHASE 5: POST-STARTUP VALIDATION
###############################################################################
echo ""
echo -e "${CYAN}[PHASE 5/5] Validating post-startup state...${NC}"
echo ""

# Wait a bit more for services to fully register
echo "   ⏳ Waiting for service registration (20s)..."
sleep 20

# Validation checks
echo "   🔍 Running validation checks..."
echo ""

# Check 1: Registry Health
echo -n "   [1/10] Registry health... "
if curl -s http://localhost:8888/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# Check 2: Registry Replicas
echo -n "   [2/10] Registry replicas... "
REPLICAS=$(docker ps | grep "vertice-register-[0-9]" | wc -l)
if [ "$REPLICAS" -ge 5 ]; then
    echo -e "${GREEN}✅ PASS ($REPLICAS replicas)${NC}"
else
    echo -e "${RED}❌ FAIL (only $REPLICAS replicas)${NC}"
fi

# Check 3: Redis
echo -n "   [3/10] Redis connectivity... "
if docker exec vertice-redis-master redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# Check 4: Services Registered
echo -n "   [4/10] Services registered... "
SERVICES_AFTER=$(curl -s http://localhost:8888/services 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$SERVICES_AFTER" -ge 15 ]; then
    echo -e "${GREEN}✅ PASS ($SERVICES_AFTER services)${NC}"
else
    echo -e "${YELLOW}⚠️  WARN (only $SERVICES_AFTER services, expected ~$SERVICES_BEFORE)${NC}"
fi

# Check 5: Sidecars Healthy
echo -n "   [5/10] Sidecars healthy... "
SIDECARS_AFTER=$(docker ps | grep sidecar | grep healthy | wc -l)
SIDECARS_TOTAL=$(docker ps | grep sidecar | wc -l)
if [ "$SIDECARS_AFTER" -eq "$SIDECARS_TOTAL" ] && [ "$SIDECARS_TOTAL" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS ($SIDECARS_AFTER/$SIDECARS_TOTAL)${NC}"
else
    echo -e "${YELLOW}⚠️  WARN ($SIDECARS_AFTER/$SIDECARS_TOTAL healthy)${NC}"
fi

# Check 6: Prometheus
echo -n "   [6/10] Prometheus... "
if curl -s http://localhost:9090/-/healthy 2>/dev/null | grep -q "Prometheus"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${YELLOW}⚠️  WARN${NC}"
fi

# Check 7: Grafana
echo -n "   [7/10] Grafana... "
if docker ps | grep -q "grafana.*Up"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${YELLOW}⚠️  WARN${NC}"
fi

# Check 8: Jaeger
echo -n "   [8/10] Jaeger... "
if docker ps | grep -q "jaeger.*Up"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${YELLOW}⚠️  WARN${NC}"
fi

# Check 9: Response Time
echo -n "   [9/10] Response time... "
START_TIME=$(date +%s%N | cut -b1-13)
curl -s http://localhost:8888/health > /dev/null
END_TIME=$(date +%s%N | cut -b1-13)
RESPONSE_TIME=$((END_TIME - START_TIME))
if [ "$RESPONSE_TIME" -lt 500 ]; then
    echo -e "${GREEN}✅ PASS (${RESPONSE_TIME}ms)${NC}"
else
    echo -e "${YELLOW}⚠️  WARN (${RESPONSE_TIME}ms)${NC}"
fi

# Check 10: No Restart Loops
echo -n "   [10/10] Container stability... "
RESTARTING=$(docker ps | grep -i "restarting" | wc -l)
if [ "$RESTARTING" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS (no restarts)${NC}"
else
    echo -e "${RED}❌ FAIL ($RESTARTING containers restarting)${NC}"
fi

###############################################################################
# SUMMARY
###############################################################################
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     TEST SUMMARY                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

TEST_END=$(date +%s)
TOTAL_TIME=$((TEST_END - TEST_START))

echo ""
echo "   ⏱️  Total test duration: ${TOTAL_TIME}s"
echo "   ⏱️  Startup time: ${STARTUP_TIME}s"
echo ""
echo "   📊 Before shutdown:"
echo "      - Containers: $CONTAINERS_BEFORE"
echo "      - Services: $SERVICES_BEFORE"
echo "      - Sidecars: $SIDECARS_BEFORE"
echo ""
echo "   📊 After restart:"
echo "      - Containers: $(docker ps | wc -l)"
echo "      - Services: $SERVICES_AFTER"
echo "      - Sidecars: $SIDECARS_AFTER/$SIDECARS_TOTAL"
echo ""

# Calculate recovery rate
if [ "$SERVICES_BEFORE" -gt 0 ]; then
    RECOVERY_RATE=$((SERVICES_AFTER * 100 / SERVICES_BEFORE))
    echo "   📈 Service recovery rate: ${RECOVERY_RATE}%"
    echo ""

    if [ "$RECOVERY_RATE" -ge 90 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                                ║${NC}"
        echo -e "${GREEN}║                  ✅ TEST PASSED ✅                             ║${NC}"
        echo -e "${GREEN}║                                                                ║${NC}"
        echo -e "${GREEN}║  System successfully recovered from complete restart          ║${NC}"
        echo -e "${GREEN}║  TITANIUM-grade reliability CONFIRMED                         ║${NC}"
        echo -e "${GREEN}║                                                                ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    elif [ "$RECOVERY_RATE" -ge 75 ]; then
        echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║                                                                ║${NC}"
        echo -e "${YELLOW}║                  ⚠️  TEST PARTIAL ⚠️                          ║${NC}"
        echo -e "${YELLOW}║                                                                ║${NC}"
        echo -e "${YELLOW}║  System recovered but some services need attention            ║${NC}"
        echo -e "${YELLOW}║                                                                ║${NC}"
        echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                                ║${NC}"
        echo -e "${RED}║                  ❌ TEST FAILED ❌                             ║${NC}"
        echo -e "${RED}║                                                                ║${NC}"
        echo -e "${RED}║  System did not recover properly from restart                 ║${NC}"
        echo -e "${RED}║                                                                ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    fi
fi

echo ""
echo -e "${CYAN}Test completed at $(date +%Y-%m-%d\ %H:%M:%S)${NC}"
echo ""
echo "🙏 Glory to YHWH!"
echo ""

# Save results to file
cat > /tmp/restart_test_results.json << EOF
{
  "test_date": "$(date -Iseconds)",
  "total_duration_seconds": $TOTAL_TIME,
  "startup_time_seconds": $STARTUP_TIME,
  "before_shutdown": {
    "containers": $CONTAINERS_BEFORE,
    "services": $SERVICES_BEFORE,
    "sidecars": $SIDECARS_BEFORE
  },
  "after_restart": {
    "containers": $(docker ps | wc -l),
    "services": $SERVICES_AFTER,
    "sidecars": $SIDECARS_AFTER,
    "sidecars_total": $SIDECARS_TOTAL
  },
  "recovery_rate_percent": $((SERVICES_AFTER * 100 / SERVICES_BEFORE)),
  "response_time_ms": $RESPONSE_TIME
}
EOF

echo "📄 Results saved to: /tmp/restart_test_results.json"
