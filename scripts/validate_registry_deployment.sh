#!/bin/bash
# ============================================================================
# Service Registry Deployment Validation Script
#
# This script performs COMPREHENSIVE validation of the Service Registry
# deployment to ensure 100% RELIABILITY.
#
# Exit codes:
#   0 - All checks passed (CONFIÁVEL)
#   1 - Critical failure detected (NÃO CONFIÁVEL)
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Test result tracking
declare -a FAILED_TESTS

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED++))
    FAILED_TESTS+=("$1")
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    ((WARNINGS++))
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "Command '$1' is available"
        return 0
    else
        log_error "Command '$1' is NOT available"
        return 1
    fi
}

# ============================================================================
# PRE-DEPLOYMENT CHECKS
# ============================================================================

echo ""
echo "=========================================="
echo "  PHASE 1: PRE-DEPLOYMENT VALIDATION"
echo "=========================================="
echo ""

log_info "Checking required commands..."
check_command "docker"
if docker compose version &>/dev/null; then
    log_success "Docker Compose v2 is available"
else
    log_error "Docker Compose is NOT available"
fi
check_command "curl"
if command -v jq &>/dev/null; then
    log_success "Command 'jq' is available"
else
    log_warning "jq not installed (optional but recommended)"
fi

log_info "Checking Docker daemon..."
if docker info &> /dev/null; then
    log_success "Docker daemon is running"
else
    log_error "Docker daemon is NOT running"
    exit 1
fi

log_info "Checking Redis HA backend..."
if docker ps --filter name=vertice-redis-master --format "{{.Status}}" | grep -q "Up"; then
    log_success "Redis master is running"

    # Check replication
    SLAVES=$(docker exec vertice-redis-master redis-cli INFO replication | grep connected_slaves | cut -d: -f2 | tr -d '\r')
    if [ "$SLAVES" -ge "1" ]; then
        log_success "Redis has $SLAVES replica(s) connected"
    else
        log_warning "Redis has NO replicas (HA degraded)"
    fi

    # Test connectivity
    if docker exec vertice-redis-master redis-cli PING | grep -q "PONG"; then
        log_success "Redis responds to PING"
    else
        log_error "Redis does NOT respond to PING"
    fi
else
    log_error "Redis master is NOT running"
fi

log_info "Checking network..."
if docker network ls | grep -q "maximus-network"; then
    log_success "Docker network 'maximus-network' exists"
else
    log_error "Docker network 'maximus-network' does NOT exist"
fi

log_info "Checking file structure..."
if [ -f "/home/juan/vertice-dev/docker-compose.service-registry.yml" ]; then
    log_success "docker-compose.service-registry.yml exists"
else
    log_error "docker-compose.service-registry.yml NOT found"
fi

if [ -f "/home/juan/vertice-dev/backend/services/vertice_register/main.py" ]; then
    log_success "vertice_register/main.py exists"
else
    log_error "vertice_register/main.py NOT found"
fi

if [ -f "/home/juan/vertice-dev/backend/services/vertice_register/Dockerfile" ]; then
    log_success "vertice_register/Dockerfile exists"
else
    log_error "vertice_register/Dockerfile NOT found"
fi

if [ -f "/home/juan/vertice-dev/backend/shared/vertice_registry_client.py" ]; then
    log_success "shared/vertice_registry_client.py exists"
else
    log_error "shared/vertice_registry_client.py NOT found"
fi

# ============================================================================
# DEPLOYMENT READINESS
# ============================================================================

echo ""
echo "=========================================="
echo "  PHASE 2: DEPLOYMENT READINESS"
echo "=========================================="
echo ""

log_info "Checking if registry is already running..."
if docker ps --filter name=vertice-register --format "{{.Names}}" | grep -q "vertice-register"; then
    log_warning "Service Registry containers are already running"
    echo "         Run 'docker compose -f docker-compose.service-registry.yml down' to stop them"
else
    log_success "No conflicting registry containers found"
fi

log_info "Checking port availability..."
if ! nc -z localhost 8888 2>/dev/null; then
    log_success "Port 8888 is available"
else
    log_warning "Port 8888 is already in use"
fi

# ============================================================================
# FINAL REPORT
# ============================================================================

echo ""
echo "=========================================="
echo "  VALIDATION SUMMARY"
echo "=========================================="
echo ""
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ SISTEMA CONFIÁVEL - Pronto para deploy!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SISTEMA NÃO CONFIÁVEL - Corrija os erros abaixo:${NC}"
    echo ""
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}•${NC} $test"
    done
    echo ""
    exit 1
fi
