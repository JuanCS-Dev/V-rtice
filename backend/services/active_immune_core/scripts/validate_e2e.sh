#!/bin/bash
# ============================================================================
# ACTIVE IMMUNE CORE - E2E VALIDATION SCRIPT
# ============================================================================
#
# Validates the complete system end-to-end including:
# - Unit tests (fast, no dependencies)
# - Integration tests (requires test environment)
# - Service health checks
#
# Usage:
#   ./scripts/validate_e2e.sh
#
# Prerequisites:
#   - Test environment running (docker-compose -f docker-compose.test.yml up -d)
#   - Python dependencies installed
#
# NO MOCKS, NO PLACEHOLDERS, NO TODOS - Production-grade validation.
#
# Authors: Juan & Claude
# Version: 1.0.0
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_step() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "   $1"
}

# Header
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Active Immune Core - E2E Validation                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
print_info "Quality-First | Doutrina Vértice v2.0"
print_info "NO MOCKS, NO PLACEHOLDERS, NO TODOS"
echo ""

# ============================================================================
# STEP 1: CHECK TEST ENVIRONMENT
# ============================================================================

print_step "📋 Step 1: Checking test environment"

if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose not found. Please install Docker Compose."
    exit 1
fi

print_info "Checking if test environment is running..."
if ! docker-compose -f docker-compose.test.yml ps 2>/dev/null | grep -q "Up"; then
    print_warning "Test environment is NOT running"
    print_info "Integration tests will be skipped"
    print_info ""
    print_info "To run full E2E validation with integration tests:"
    print_info "  make test-env-up  # Start test environment"
    print_info "  $0                # Run this script again"
    print_info ""
    INTEGRATION_AVAILABLE=false
else
    print_success "Test environment is running"
    docker-compose -f docker-compose.test.yml ps
    INTEGRATION_AVAILABLE=true
fi

# ============================================================================
# STEP 2: RUN UNIT TESTS
# ============================================================================

print_step "🧪 Step 2: Running unit tests"

print_info "Unit tests run fast and require no external dependencies"
print_info "Running tests marked as 'unit' (or not marked as 'integration')..."
echo ""

if PYTHONPATH=. VERTICE_LYMPHNODE_SHARED_SECRET=test-secret \
   python -m pytest -v -m "not integration" --tb=short -q; then
    print_success "Unit tests passed!"
    UNIT_PASSED=true
else
    print_error "Unit tests failed!"
    UNIT_PASSED=false
fi

# ============================================================================
# STEP 3: RUN INTEGRATION TESTS (if environment available)
# ============================================================================

if [ "$INTEGRATION_AVAILABLE" = true ]; then
    print_step "🔗 Step 3: Running integration tests"
    
    print_info "Integration tests use REAL Kafka, Redis, and PostgreSQL"
    print_info "Running tests marked as 'integration'..."
    echo ""
    
    if PYTHONPATH=. \
       KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
       REDIS_URL=redis://localhost:6379/0 \
       ACTIVE_IMMUNE_POSTGRES_HOST=localhost \
       ACTIVE_IMMUNE_POSTGRES_PORT=5432 \
       ACTIVE_IMMUNE_POSTGRES_DB=immunis_memory_test \
       ACTIVE_IMMUNE_POSTGRES_USER=immune_user \
       ACTIVE_IMMUNE_POSTGRES_PASSWORD=immune_pass_test \
       VERTICE_LYMPHNODE_SHARED_SECRET=test-secret \
       python -m pytest api/core_integration/ -v -m integration --tb=short -q; then
        print_success "Integration tests passed!"
        INTEGRATION_PASSED=true
    else
        print_error "Integration tests failed!"
        INTEGRATION_PASSED=false
    fi
else
    print_step "🔗 Step 3: Integration tests (SKIPPED)"
    print_warning "Test environment not available - skipping integration tests"
    INTEGRATION_PASSED="skipped"
fi

# ============================================================================
# STEP 4: SERVICE HEALTH CHECK (optional)
# ============================================================================

print_step "💚 Step 4: Service health check"

print_info "Checking if Active Immune Core API is running..."

if curl -sf http://localhost:8200/health > /dev/null 2>&1; then
    print_success "API is running and healthy"
    print_info "Health check endpoint: http://localhost:8200/health"
    API_HEALTHY=true
else
    print_warning "API is not running (this is optional for validation)"
    print_info ""
    print_info "To start the API:"
    print_info "  python -m uvicorn api.main:app --reload --port 8200"
    print_info ""
    API_HEALTHY=false
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_step "📊 Validation Summary"

echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│ Test Results                                            │"
echo "├─────────────────────────────────────────────────────────┤"

if [ "$UNIT_PASSED" = true ]; then
    echo -e "│ Unit Tests:         ${GREEN}✅ PASSED${NC}                         │"
else
    echo -e "│ Unit Tests:         ${RED}❌ FAILED${NC}                         │"
fi

if [ "$INTEGRATION_PASSED" = true ]; then
    echo -e "│ Integration Tests:  ${GREEN}✅ PASSED${NC}                         │"
elif [ "$INTEGRATION_PASSED" = "skipped" ]; then
    echo -e "│ Integration Tests:  ${YELLOW}⏭️  SKIPPED${NC}                        │"
else
    echo -e "│ Integration Tests:  ${RED}❌ FAILED${NC}                         │"
fi

if [ "$API_HEALTHY" = true ]; then
    echo -e "│ API Health Check:   ${GREEN}✅ HEALTHY${NC}                        │"
else
    echo -e "│ API Health Check:   ${YELLOW}⚠️  NOT RUNNING${NC} (optional)         │"
fi

echo "└─────────────────────────────────────────────────────────┘"
echo ""

# ============================================================================
# EXIT STATUS
# ============================================================================

if [ "$UNIT_PASSED" = false ]; then
    print_error "❌ E2E Validation FAILED - Unit tests failed"
    echo ""
    echo "Fix unit test failures and try again."
    exit 1
elif [ "$INTEGRATION_PASSED" = false ]; then
    print_error "❌ E2E Validation FAILED - Integration tests failed"
    echo ""
    echo "Fix integration test failures and try again."
    exit 1
elif [ "$INTEGRATION_PASSED" = "skipped" ]; then
    print_warning "⚠️  E2E Validation PARTIAL - Integration tests skipped"
    echo ""
    print_info "Unit tests passed, but integration tests were not run."
    print_info "For full validation, start test environment:"
    print_info "  make test-env-up"
    print_info ""
    print_success "✅ Unit tests: ALL PASSED"
    exit 0
else
    print_success "═══════════════════════════════════════════════════════"
    print_success "✅ E2E Validation: SUCCESS!"
    print_success "═══════════════════════════════════════════════════════"
    echo ""
    print_info "All tests passed! System is PRODUCTION-READY."
    print_info ""
    print_info "Test Results:"
    print_info "  ✅ Unit tests:        PASSED"
    print_info "  ✅ Integration tests: PASSED"
    if [ "$API_HEALTHY" = true ]; then
        print_info "  ✅ API health check:  PASSED"
    fi
    echo ""
    print_success "🎉 Active Immune Core is ready for deployment!"
    exit 0
fi
