#!/bin/bash
###############################################################################
# Vértice System Stability Audit
# Validates if system is TITANIUM-grade (99%+ uptime ready)
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
NC='\033[0m' # No Color

# Counters
PASS=0
WARN=0
FAIL=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║           🔍 VÉRTICE SYSTEM STABILITY AUDIT 🔍                ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║  Target: 99%+ Uptime (TITANIUM Grade)                         ║${NC}"
echo -e "${BLUE}║  Date: $(date +%Y-%m-%d)                                            ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# TEST 1: Service Registry Health
###############################################################################
echo -e "${BLUE}[1/15] Service Registry Health...${NC}"

REGISTRY_REPLICAS=$(docker ps | grep "vertice-register-[0-9]" | grep -v "lb" | wc -l)
REGISTRY_TARGET=5

if [ "$REGISTRY_REPLICAS" -ge "$REGISTRY_TARGET" ]; then
    echo -e "${GREEN}✅ PASS: $REGISTRY_REPLICAS registry replicas UP (target: $REGISTRY_TARGET)${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL: Only $REGISTRY_REPLICAS registry replicas UP (target: $REGISTRY_TARGET)${NC}"
    ((FAIL++))
fi

# Check load balancer
if docker ps | grep -q "vertice-register-lb"; then
    echo -e "${GREEN}✅ PASS: Load balancer running${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL: Load balancer NOT running${NC}"
    ((FAIL++))
fi

# Check registry health endpoint
if curl -s http://localhost:8888/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS: Registry health endpoint responding${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL: Registry health endpoint not responding${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 2: Redis Availability
###############################################################################
echo ""
echo -e "${BLUE}[2/15] Redis Availability...${NC}"

if docker ps | grep -q "redis.*Up"; then
    echo -e "${GREEN}✅ PASS: Redis container running${NC}"
    ((PASS++))

    # Test Redis connection
    if docker exec maximus-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ PASS: Redis responding to PING${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  WARN: Redis not responding to PING${NC}"
        ((WARN++))
    fi
else
    echo -e "${RED}❌ FAIL: Redis container NOT running${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 3: Sidecars Health
###############################################################################
echo ""
echo -e "${BLUE}[3/15] Sidecars Health...${NC}"

TOTAL_SIDECARS=$(docker ps | grep sidecar | wc -l)
HEALTHY_SIDECARS=$(docker ps | grep sidecar | grep "healthy" | wc -l)
UNHEALTHY_SIDECARS=$((TOTAL_SIDECARS - HEALTHY_SIDECARS))

echo "   Total sidecars: $TOTAL_SIDECARS"
echo "   Healthy: $HEALTHY_SIDECARS"
echo "   Unhealthy: $UNHEALTHY_SIDECARS"

if [ "$UNHEALTHY_SIDECARS" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: All $TOTAL_SIDECARS sidecars healthy${NC}"
    ((PASS++))
elif [ "$UNHEALTHY_SIDECARS" -le 2 ]; then
    echo -e "${YELLOW}⚠️  WARN: $UNHEALTHY_SIDECARS sidecars unhealthy${NC}"
    ((WARN++))
else
    echo -e "${RED}❌ FAIL: $UNHEALTHY_SIDECARS sidecars unhealthy${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 4: Service Discovery
###############################################################################
echo ""
echo -e "${BLUE}[4/15] Service Discovery...${NC}"

REGISTERED_SERVICES=$(curl -s http://localhost:8888/services 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$REGISTERED_SERVICES" -ge 20 ]; then
    echo -e "${GREEN}✅ PASS: $REGISTERED_SERVICES services registered${NC}"
    ((PASS++))
elif [ "$REGISTERED_SERVICES" -ge 10 ]; then
    echo -e "${YELLOW}⚠️  WARN: Only $REGISTERED_SERVICES services registered${NC}"
    ((WARN++))
else
    echo -e "${RED}❌ FAIL: Only $REGISTERED_SERVICES services registered${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 5: Monitoring Stack
###############################################################################
echo ""
echo -e "${BLUE}[5/15] Monitoring Stack (Prometheus + Grafana + Alertmanager)...${NC}"

# Prometheus
if docker ps | grep -q "prometheus.*Up"; then
    echo -e "${GREEN}✅ PASS: Prometheus running${NC}"
    ((PASS++))

    # Test Prometheus health
    if curl -s http://localhost:9090/-/healthy 2>/dev/null | grep -q "Prometheus"; then
        echo -e "${GREEN}✅ PASS: Prometheus healthy${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  WARN: Prometheus not responding${NC}"
        ((WARN++))
    fi
else
    echo -e "${RED}❌ FAIL: Prometheus NOT running${NC}"
    ((FAIL++))
fi

# Grafana
if docker ps | grep -q "grafana.*Up"; then
    echo -e "${GREEN}✅ PASS: Grafana running${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  WARN: Grafana NOT running${NC}"
    ((WARN++))
fi

# Alertmanager
if docker ps | grep -q "alertmanager.*Up"; then
    echo -e "${GREEN}✅ PASS: Alertmanager running${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  WARN: Alertmanager NOT running${NC}"
    ((WARN++))
fi

###############################################################################
# TEST 6: Jaeger Tracing
###############################################################################
echo ""
echo -e "${BLUE}[6/15] Distributed Tracing (Jaeger)...${NC}"

if docker ps | grep -q "jaeger.*Up"; then
    echo -e "${GREEN}✅ PASS: Jaeger running${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  WARN: Jaeger NOT running${NC}"
    ((WARN++))
fi

###############################################################################
# TEST 7: Network Connectivity
###############################################################################
echo ""
echo -e "${BLUE}[7/15] Network Connectivity...${NC}"

# Check maximus-network
if docker network ls | grep -q "maximus-network"; then
    echo -e "${GREEN}✅ PASS: maximus-network exists${NC}"
    ((PASS++))

    # Check how many containers are connected
    CONNECTED=$(docker network inspect maximus-network 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)[0]['Containers']))" 2>/dev/null || echo "0")
    echo "   Connected containers: $CONNECTED"

    if [ "$CONNECTED" -ge 20 ]; then
        echo -e "${GREEN}✅ PASS: $CONNECTED containers on network${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  WARN: Only $CONNECTED containers on network${NC}"
        ((WARN++))
    fi
else
    echo -e "${RED}❌ FAIL: maximus-network NOT found${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 8: Container Restarts
###############################################################################
echo ""
echo -e "${BLUE}[8/15] Container Stability (Restart Count)...${NC}"

RESTART_COUNT=$(docker ps --format "{{.Names}}: {{.Status}}" | grep -oP "Restarting|restart" | wc -l)
HIGH_RESTART=$(docker ps --format "table {{.Names}}\t{{.Status}}" | awk '{print $NF}' | grep -oP '\d+' | awk '$1 > 5' | wc -l)

if [ "$RESTART_COUNT" -eq 0 ] && [ "$HIGH_RESTART" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: No containers restarting, no high restart counts${NC}"
    ((PASS++))
elif [ "$HIGH_RESTART" -le 2 ]; then
    echo -e "${YELLOW}⚠️  WARN: $HIGH_RESTART containers with >5 restarts${NC}"
    ((WARN++))
else
    echo -e "${RED}❌ FAIL: $HIGH_RESTART containers with excessive restarts${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 9: Disk Space
###############################################################################
echo ""
echo -e "${BLUE}[9/15] Disk Space...${NC}"

DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✅ PASS: Disk usage at ${DISK_USAGE}%${NC}"
    ((PASS++))
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠️  WARN: Disk usage at ${DISK_USAGE}%${NC}"
    ((WARN++))
else
    echo -e "${RED}❌ FAIL: Disk usage at ${DISK_USAGE}% (CRITICAL)${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 10: Memory Usage
###############################################################################
echo ""
echo -e "${BLUE}[10/15] Memory Usage...${NC}"

MEMORY_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')

if [ "$MEMORY_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✅ PASS: Memory usage at ${MEMORY_USAGE}%${NC}"
    ((PASS++))
elif [ "$MEMORY_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠️  WARN: Memory usage at ${MEMORY_USAGE}%${NC}"
    ((WARN++))
else
    echo -e "${RED}❌ FAIL: Memory usage at ${MEMORY_USAGE}% (CRITICAL)${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 11: Docker Daemon Health
###############################################################################
echo ""
echo -e "${BLUE}[11/15] Docker Daemon Health...${NC}"

if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS: Docker daemon responding${NC}"
    ((PASS++))

    # Check Docker version
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
    echo "   Docker version: $DOCKER_VERSION"
else
    echo -e "${RED}❌ FAIL: Docker daemon not responding${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 12: Log Errors (Last Hour)
###############################################################################
echo ""
echo -e "${BLUE}[12/15] Recent Log Errors...${NC}"

# Count errors in registry logs
ERROR_COUNT=$(docker logs vertice-register-1 --since 1h 2>&1 | grep -i "error\|exception\|fatal" | wc -l || echo "0")

if [ "$ERROR_COUNT" -lt 10 ]; then
    echo -e "${GREEN}✅ PASS: Only $ERROR_COUNT errors in last hour${NC}"
    ((PASS++))
elif [ "$ERROR_COUNT" -lt 50 ]; then
    echo -e "${YELLOW}⚠️  WARN: $ERROR_COUNT errors in last hour${NC}"
    ((WARN++))
else
    echo -e "${RED}❌ FAIL: $ERROR_COUNT errors in last hour (CRITICAL)${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 13: Uptime
###############################################################################
echo ""
echo -e "${BLUE}[13/15] Container Uptime...${NC}"

# Check registry uptime
REGISTRY_UPTIME=$(docker inspect vertice-register-1 --format='{{.State.StartedAt}}' 2>/dev/null || echo "")

if [ -n "$REGISTRY_UPTIME" ]; then
    STARTED=$(date -d "$REGISTRY_UPTIME" +%s 2>/dev/null || echo "0")
    NOW=$(date +%s)
    UPTIME_SECONDS=$((NOW - STARTED))
    UPTIME_HOURS=$((UPTIME_SECONDS / 3600))

    echo "   Registry uptime: ${UPTIME_HOURS}h"

    if [ "$UPTIME_HOURS" -ge 1 ]; then
        echo -e "${GREEN}✅ PASS: Registry uptime ${UPTIME_HOURS}h (stable)${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  WARN: Registry uptime only ${UPTIME_HOURS}h (recently restarted)${NC}"
        ((WARN++))
    fi
else
    echo -e "${RED}❌ FAIL: Cannot determine registry uptime${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 14: Response Time
###############################################################################
echo ""
echo -e "${BLUE}[14/15] API Response Time...${NC}"

# Test registry response time
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}\n' http://localhost:8888/health 2>/dev/null || echo "999")
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc | cut -d'.' -f1)

if [ "$RESPONSE_MS" -lt 100 ]; then
    echo -e "${GREEN}✅ PASS: Response time ${RESPONSE_MS}ms (excellent)${NC}"
    ((PASS++))
elif [ "$RESPONSE_MS" -lt 500 ]; then
    echo -e "${YELLOW}⚠️  WARN: Response time ${RESPONSE_MS}ms (acceptable)${NC}"
    ((WARN++))
else
    echo -e "${RED}❌ FAIL: Response time ${RESPONSE_MS}ms (too slow)${NC}"
    ((FAIL++))
fi

###############################################################################
# TEST 15: Circuit Breakers
###############################################################################
echo ""
echo -e "${BLUE}[15/15] Circuit Breaker Status...${NC}"

# Check if any circuit breakers are OPEN (from registry health)
CB_STATUS=$(curl -s http://localhost:8888/health 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('components', {}).get('redis', {}).get('circuit_breaker', {}).get('state', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")

if [ "$CB_STATUS" == "CLOSED" ]; then
    echo -e "${GREEN}✅ PASS: All circuit breakers CLOSED (healthy)${NC}"
    ((PASS++))
elif [ "$CB_STATUS" == "HALF_OPEN" ]; then
    echo -e "${YELLOW}⚠️  WARN: Circuit breaker HALF_OPEN (recovering)${NC}"
    ((WARN++))
elif [ "$CB_STATUS" == "OPEN" ]; then
    echo -e "${RED}❌ FAIL: Circuit breaker OPEN (failures detected)${NC}"
    ((FAIL++))
else
    echo -e "${YELLOW}⚠️  WARN: Cannot determine circuit breaker status${NC}"
    ((WARN++))
fi

###############################################################################
# FINAL REPORT
###############################################################################
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      AUDIT SUMMARY                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

TOTAL=$((PASS + WARN + FAIL))
PASS_PCT=$((PASS * 100 / TOTAL))
WARN_PCT=$((WARN * 100 / TOTAL))
FAIL_PCT=$((FAIL * 100 / TOTAL))

echo ""
echo "   Total tests: $TOTAL"
echo -e "   ${GREEN}✅ Passed: $PASS ($PASS_PCT%)${NC}"
echo -e "   ${YELLOW}⚠️  Warnings: $WARN ($WARN_PCT%)${NC}"
echo -e "   ${RED}❌ Failed: $FAIL ($FAIL_PCT%)${NC}"
echo ""

# Determine grade
if [ "$FAIL" -eq 0 ] && [ "$WARN" -le 2 ]; then
    GRADE="TITANIUM"
    COLOR=$GREEN
    SYMBOL="🏆"
    RECOMMENDATION="System is production-ready with 99%+ uptime capability"
elif [ "$FAIL" -eq 0 ] && [ "$WARN" -le 5 ]; then
    GRADE="GOLD"
    COLOR=$GREEN
    SYMBOL="🥇"
    RECOMMENDATION="System is stable but has minor issues to address"
elif [ "$FAIL" -le 2 ]; then
    GRADE="SILVER"
    COLOR=$YELLOW
    SYMBOL="🥈"
    RECOMMENDATION="System needs improvements before production"
else
    GRADE="BRONZE"
    COLOR=$RED
    SYMBOL="🥉"
    RECOMMENDATION="System requires significant fixes"
fi

echo -e "${COLOR}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${COLOR}║                                                                ║${NC}"
echo -e "${COLOR}║            SYSTEM GRADE: $SYMBOL $GRADE $SYMBOL                         ║${NC}"
echo -e "${COLOR}║                                                                ║${NC}"
echo -e "${COLOR}║  $RECOMMENDATION   ${NC}"
echo -e "${COLOR}║                                                                ║${NC}"
echo -e "${COLOR}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Exit code
if [ "$FAIL" -eq 0 ]; then
    exit 0
else
    exit 1
fi
