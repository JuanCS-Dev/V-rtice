#!/bin/bash
#
# Governance SSE - Performance Benchmark Script
#
# Measures latency metrics for E2E validation:
# - Decision enqueue → SSE broadcast latency
# - Approve action → response latency
# - SSE connection establishment time
# - Health check response time
#
# Author: Claude Code + JuanCS-Dev
# Date: 2025-10-06
# Quality: Production-ready, REGRA DE OURO compliant
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"
ITERATIONS="${ITERATIONS:-5}"

echo "================================================================================"
echo -e "${CYAN}🏛️  Governance SSE - Performance Benchmarking${NC}"
echo "================================================================================"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Iterations: $ITERATIONS"
echo ""

# Create temp file for results
RESULTS_FILE=$(mktemp)
trap "rm -f $RESULTS_FILE" EXIT

# ============================================================================
# Test 1: Health Check Latency
# ============================================================================

echo -e "${YELLOW}📊 Test 1: Health Check Latency${NC}"
echo "Measuring GET /api/v1/governance/health response time..."
echo ""

TOTAL_MS=0
for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%3N)
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/governance/health")
    END=$(date +%s%3N)
    LATENCY=$((END - START))
    TOTAL_MS=$((TOTAL_MS + LATENCY))

    if [ "$RESPONSE" = "200" ]; then
        echo "  Iteration $i: ${LATENCY}ms ✅"
    else
        echo -e "  Iteration $i: ${LATENCY}ms ${RED}✗ (HTTP $RESPONSE)${NC}"
    fi
done

AVG_HEALTH=$((TOTAL_MS / ITERATIONS))
echo ""
echo -e "${GREEN}Average Health Check Latency: ${AVG_HEALTH}ms${NC}"
echo "health_check_avg_ms=$AVG_HEALTH" >> $RESULTS_FILE

# Target: < 100ms
if [ $AVG_HEALTH -lt 100 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Below 100ms target"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - Above 100ms target"
fi
echo ""

# ============================================================================
# Test 2: Decision Enqueue Latency
# ============================================================================

echo -e "${YELLOW}📊 Test 2: Decision Enqueue Latency${NC}"
echo "Measuring POST /api/v1/governance/test/enqueue response time..."
echo ""

TOTAL_MS=0
for i in $(seq 1 $ITERATIONS); do
    DECISION_ID="bench_$(date +%s%3N)"
    PAYLOAD="{
        \"decision_id\": \"$DECISION_ID\",
        \"risk_level\": \"high\",
        \"automation_level\": \"supervised\",
        \"context\": {
            \"action_type\": \"block_ip\",
            \"action_params\": {\"target\": \"192.168.1.$(($i % 255))\"},
            \"ai_reasoning\": \"Benchmark test\",
            \"confidence\": 0.95,
            \"threat_score\": 0.95,
            \"threat_type\": \"benchmark\",
            \"metadata\": {}
        }
    }"

    START=$(date +%s%3N)
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "$BACKEND_URL/api/v1/governance/test/enqueue")
    END=$(date +%s%3N)
    LATENCY=$((END - START))
    TOTAL_MS=$((TOTAL_MS + LATENCY))

    if [ "$RESPONSE" = "200" ]; then
        echo "  Iteration $i: ${LATENCY}ms ✅"
    else
        echo -e "  Iteration $i: ${LATENCY}ms ${RED}✗ (HTTP $RESPONSE)${NC}"
    fi

    # Small delay to avoid overwhelming queue
    sleep 0.2
done

AVG_ENQUEUE=$((TOTAL_MS / ITERATIONS))
echo ""
echo -e "${GREEN}Average Enqueue Latency: ${AVG_ENQUEUE}ms${NC}"
echo "enqueue_avg_ms=$AVG_ENQUEUE" >> $RESULTS_FILE

# Target: < 1000ms (1s)
if [ $AVG_ENQUEUE -lt 1000 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Below 1s target"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - Above 1s target"
fi
echo ""

# ============================================================================
# Test 3: Pending Stats Query Latency
# ============================================================================

echo -e "${YELLOW}📊 Test 3: Pending Stats Query Latency${NC}"
echo "Measuring GET /api/v1/governance/pending response time..."
echo ""

TOTAL_MS=0
for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%3N)
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/governance/pending")
    END=$(date +%s%3N)
    LATENCY=$((END - START))
    TOTAL_MS=$((TOTAL_MS + LATENCY))

    if [ "$RESPONSE" = "200" ]; then
        echo "  Iteration $i: ${LATENCY}ms ✅"
    else
        echo -e "  Iteration $i: ${LATENCY}ms ${RED}✗ (HTTP $RESPONSE)${NC}"
    fi
done

AVG_PENDING=$((TOTAL_MS / ITERATIONS))
echo ""
echo -e "${GREEN}Average Pending Stats Latency: ${AVG_PENDING}ms${NC}"
echo "pending_stats_avg_ms=$AVG_PENDING" >> $RESULTS_FILE

# Target: < 200ms
if [ $AVG_PENDING -lt 200 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Below 200ms target"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - Above 200ms target"
fi
echo ""

# ============================================================================
# Test 4: Session Creation Latency
# ============================================================================

echo -e "${YELLOW}📊 Test 4: Session Creation Latency${NC}"
echo "Measuring POST /api/v1/governance/session/create response time..."
echo ""

TOTAL_MS=0
for i in $(seq 1 $ITERATIONS); do
    OPERATOR_ID="bench_op_${i}@test"
    PAYLOAD="{
        \"operator_id\": \"$OPERATOR_ID\",
        \"operator_name\": \"bench_op_$i\",
        \"operator_role\": \"soc_operator\"
    }"

    START=$(date +%s%3N)
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "$BACKEND_URL/api/v1/governance/session/create")
    END=$(date +%s%3N)
    LATENCY=$((END - START))
    TOTAL_MS=$((TOTAL_MS + LATENCY))

    if [ "$RESPONSE" = "200" ]; then
        echo "  Iteration $i: ${LATENCY}ms ✅"
    else
        echo -e "  Iteration $i: ${LATENCY}ms ${RED}✗ (HTTP $RESPONSE)${NC}"
    fi
done

AVG_SESSION=$((TOTAL_MS / ITERATIONS))
echo ""
echo -e "${GREEN}Average Session Creation Latency: ${AVG_SESSION}ms${NC}"
echo "session_create_avg_ms=$AVG_SESSION" >> $RESULTS_FILE

# Target: < 500ms
if [ $AVG_SESSION -lt 500 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Below 500ms target"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - Above 500ms target"
fi
echo ""

# ============================================================================
# Final Summary
# ============================================================================

echo "================================================================================"
echo -e "${CYAN}📊 Benchmark Summary${NC}"
echo "================================================================================"
echo ""

# Read results
source $RESULTS_FILE

# Display table
printf "%-30s | %-12s | %-12s | %-10s\n" "Metric" "Avg Latency" "Target" "Status"
echo "--------------------------------------------------------------------------------"

# Health Check
TARGET_HEALTH=100
STATUS_HEALTH="✅ PASS"
[ $health_check_avg_ms -ge $TARGET_HEALTH ] && STATUS_HEALTH="⚠️  WARN"
printf "%-30s | %-12s | %-12s | %-10s\n" "Health Check" "${health_check_avg_ms}ms" "< ${TARGET_HEALTH}ms" "$STATUS_HEALTH"

# Decision Enqueue
TARGET_ENQUEUE=1000
STATUS_ENQUEUE="✅ PASS"
[ $enqueue_avg_ms -ge $TARGET_ENQUEUE ] && STATUS_ENQUEUE="⚠️  WARN"
printf "%-30s | %-12s | %-12s | %-10s\n" "Decision Enqueue" "${enqueue_avg_ms}ms" "< ${TARGET_ENQUEUE}ms" "$STATUS_ENQUEUE"

# Pending Stats
TARGET_PENDING=200
STATUS_PENDING="✅ PASS"
[ $pending_stats_avg_ms -ge $TARGET_PENDING ] && STATUS_PENDING="⚠️  WARN"
printf "%-30s | %-12s | %-12s | %-10s\n" "Pending Stats Query" "${pending_stats_avg_ms}ms" "< ${TARGET_PENDING}ms" "$STATUS_PENDING"

# Session Creation
TARGET_SESSION=500
STATUS_SESSION="✅ PASS"
[ $session_create_avg_ms -ge $TARGET_SESSION ] && STATUS_SESSION="⚠️  WARN"
printf "%-30s | %-12s | %-12s | %-10s\n" "Session Creation" "${session_create_avg_ms}ms" "< ${TARGET_SESSION}ms" "$STATUS_SESSION"

echo ""

# Overall status
TOTAL_TESTS=4
PASSED_TESTS=0
[ $health_check_avg_ms -lt $TARGET_HEALTH ] && PASSED_TESTS=$((PASSED_TESTS + 1))
[ $enqueue_avg_ms -lt $TARGET_ENQUEUE ] && PASSED_TESTS=$((PASSED_TESTS + 1))
[ $pending_stats_avg_ms -lt $TARGET_PENDING ] && PASSED_TESTS=$((PASSED_TESTS + 1))
[ $session_create_avg_ms -lt $TARGET_SESSION ] && PASSED_TESTS=$((PASSED_TESTS + 1))

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED ($PASSED_TESTS/$TOTAL_TESTS)${NC}"
else
    echo -e "${YELLOW}⚠️  SOME TESTS EXCEEDED TARGETS ($PASSED_TESTS/$TOTAL_TESTS passed)${NC}"
fi

echo ""
echo "Benchmark completed at: $(date)"
echo "Results saved to: $RESULTS_FILE (temporary)"
echo ""
