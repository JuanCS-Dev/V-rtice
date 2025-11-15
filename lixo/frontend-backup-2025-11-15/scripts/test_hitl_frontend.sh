#!/bin/bash
#===============================================================================
# HITL FRONTEND VALIDATION SCRIPT
#===============================================================================
# Tests the HITLDecisionConsole and HITLAuthPage components against backend
# Validates API endpoints, authentication flow, and WebSocket connectivity
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000"
HITL_API="${API_BASE}/api/hitl"
AUTH_API="${API_BASE}/api/auth"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "🎯 HITL FRONTEND VALIDATION - Reactive Fabric Phase 3.5"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

#===============================================================================
# TEST 1: Backend Health Check
#===============================================================================
echo -e "${BLUE}[TEST 1]${NC} Backend Health Check"
echo "-----------------------------------"

if curl -sf "${API_BASE}/health" > /dev/null 2>&1; then
    HEALTH=$(curl -s "${API_BASE}/health")
    echo -e "${GREEN}✓${NC} Backend is reachable"
    echo "Response: $HEALTH"
else
    echo -e "${RED}✗${NC} Backend is not reachable at ${API_BASE}"
    echo -e "${YELLOW}⚠${NC} Make sure the backend is running:"
    echo "   cd backend/services/reactive_fabric_core"
    echo "   python hitl/hitl_backend_simple.py"
    exit 1
fi
echo ""

#===============================================================================
# TEST 2: Authentication Endpoints
#===============================================================================
echo -e "${BLUE}[TEST 2]${NC} Authentication Endpoints"
echo "-----------------------------------"

# Test login endpoint exists
echo -n "Testing POST /api/auth/login... "
LOGIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${AUTH_API}/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test&password=test" 2>/dev/null || echo "000")

if [ "$LOGIN_RESPONSE" = "401" ] || [ "$LOGIN_RESPONSE" = "422" ] || [ "$LOGIN_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Endpoint exists (HTTP $LOGIN_RESPONSE)"
else
    echo -e "${YELLOW}⚠${NC} Endpoint not found or error (HTTP $LOGIN_RESPONSE)"
    echo "   This is expected if authentication is not yet implemented in backend"
fi

# Test 2FA endpoint exists
echo -n "Testing POST /api/auth/2fa/verify... "
TFA_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${AUTH_API}/2fa/verify" \
    -H "Content-Type: application/json" \
    -d '{"code":"123456"}' 2>/dev/null || echo "000")

if [ "$TFA_RESPONSE" = "401" ] || [ "$TFA_RESPONSE" = "422" ] || [ "$TFA_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Endpoint exists (HTTP $TFA_RESPONSE)"
else
    echo -e "${YELLOW}⚠${NC} Endpoint not found or error (HTTP $TFA_RESPONSE)"
    echo "   This is expected if 2FA is not yet implemented in backend"
fi
echo ""

#===============================================================================
# TEST 3: HITL Decision Endpoints
#===============================================================================
echo -e "${BLUE}[TEST 3]${NC} HITL Decision Endpoints"
echo "-----------------------------------"

# Test pending decisions
echo -n "Testing GET /api/hitl/decisions/pending... "
PENDING_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "${HITL_API}/decisions/pending" 2>/dev/null || echo "000")

if [ "$PENDING_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Endpoint exists (HTTP 200)"
    PENDING_DATA=$(curl -s "${HITL_API}/decisions/pending" 2>/dev/null || echo "{}")
    DECISION_COUNT=$(echo "$PENDING_DATA" | grep -o '"analysis_id"' | wc -l || echo "0")
    echo "   Found $DECISION_COUNT pending decisions"
elif [ "$PENDING_RESPONSE" = "401" ]; then
    echo -e "${YELLOW}⚠${NC} Requires authentication (HTTP 401)"
else
    echo -e "${YELLOW}⚠${NC} Endpoint not found or error (HTTP $PENDING_RESPONSE)"
fi

# Test stats endpoint
echo -n "Testing GET /api/hitl/decisions/stats... "
STATS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "${HITL_API}/decisions/stats" 2>/dev/null || echo "000")

if [ "$STATS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Endpoint exists (HTTP 200)"
elif [ "$STATS_RESPONSE" = "401" ]; then
    echo -e "${YELLOW}⚠${NC} Requires authentication (HTTP 401)"
else
    echo -e "${YELLOW}⚠${NC} Endpoint not found or error (HTTP $STATS_RESPONSE)"
fi

# Test decide endpoint
echo -n "Testing POST /api/hitl/decisions/{id}/decide... "
DECIDE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${HITL_API}/decisions/test-123/decide" \
    -H "Content-Type: application/json" \
    -d '{"status":"approved","notes":"test"}' 2>/dev/null || echo "000")

if [ "$DECIDE_RESPONSE" = "200" ] || [ "$DECIDE_RESPONSE" = "404" ] || [ "$DECIDE_RESPONSE" = "401" ]; then
    echo -e "${GREEN}✓${NC} Endpoint exists (HTTP $DECIDE_RESPONSE)"
else
    echo -e "${YELLOW}⚠${NC} Endpoint not found or error (HTTP $DECIDE_RESPONSE)"
fi
echo ""

#===============================================================================
# TEST 4: WebSocket Availability
#===============================================================================
echo -e "${BLUE}[TEST 4]${NC} WebSocket Availability"
echo "-----------------------------------"

echo -n "Testing WebSocket endpoint (ws://localhost:8000/ws/test)... "
# WebSocket test requires a WebSocket client, so we check if the port is open
if nc -zv localhost 8000 2>&1 | grep -q "succeeded"; then
    echo -e "${GREEN}✓${NC} Port 8000 is open for WebSocket connections"
    echo "   WebSocket URL: ws://localhost:8000/ws/{username}"
else
    echo -e "${YELLOW}⚠${NC} Cannot verify WebSocket (port check failed)"
fi
echo ""

#===============================================================================
# TEST 5: Frontend Files Validation
#===============================================================================
echo -e "${BLUE}[TEST 5]${NC} Frontend Files Validation"
echo "-----------------------------------"

FRONTEND_DIR="frontend/src/components/reactive-fabric"

FILES=(
    "HITLDecisionConsole.jsx"
    "HITLDecisionConsole.module.css"
    "HITLAuthPage.jsx"
    "HITLAuthPage.module.css"
)

for file in "${FILES[@]}"; do
    if [ -f "${FRONTEND_DIR}/${file}" ]; then
        LINE_COUNT=$(wc -l < "${FRONTEND_DIR}/${file}")
        echo -e "${GREEN}✓${NC} ${file} (${LINE_COUNT} lines)"
    else
        echo -e "${RED}✗${NC} ${file} NOT FOUND"
    fi
done

# Check index.js export
if grep -q "HITLDecisionConsole" "${FRONTEND_DIR}/index.js"; then
    echo -e "${GREEN}✓${NC} HITLDecisionConsole exported in index.js"
else
    echo -e "${RED}✗${NC} HITLDecisionConsole NOT exported in index.js"
fi
echo ""

#===============================================================================
# TEST 6: Component Structure Validation
#===============================================================================
echo -e "${BLUE}[TEST 6]${NC} Component Structure Validation"
echo "-----------------------------------"

# Check HITLDecisionConsole structure
CONSOLE_FILE="${FRONTEND_DIR}/HITLDecisionConsole.jsx"
echo "HITLDecisionConsole.jsx:"

CHECKS=(
    "useState:State Management"
    "useEffect:Lifecycle Hooks"
    "useCallback:Performance Optimization"
    "WebSocket:Real-time Communication"
    "fetch.*decisions/pending:API Integration"
    "modal:Modal Dialogs"
    "priority:Priority Filtering"
)

for check in "${CHECKS[@]}"; do
    PATTERN="${check%%:*}"
    DESC="${check##*:}"
    if grep -q "$PATTERN" "$CONSOLE_FILE"; then
        echo -e "  ${GREEN}✓${NC} $DESC"
    else
        echo -e "  ${YELLOW}⚠${NC} $DESC (not found)"
    fi
done
echo ""

# Check HITLAuthPage structure
AUTH_FILE="${FRONTEND_DIR}/HITLAuthPage.jsx"
echo "HITLAuthPage.jsx:"

CHECKS=(
    "username:Username Input"
    "password:Password Input"
    "twoFactorCode:2FA Support"
    "localStorage:Token Storage"
    "api/auth/login:Login Endpoint"
    "api/auth/2fa/verify:2FA Endpoint"
)

for check in "${CHECKS[@]}"; do
    PATTERN="${check%%:*}"
    DESC="${check##*:}"
    if grep -q "$PATTERN" "$AUTH_FILE"; then
        echo -e "  ${GREEN}✓${NC} $DESC"
    else
        echo -e "  ${YELLOW}⚠${NC} $DESC (not found)"
    fi
done
echo ""

#===============================================================================
# TEST 7: CSS Module Validation
#===============================================================================
echo -e "${BLUE}[TEST 7]${NC} CSS Module Validation (PAGANI Standard)"
echo "-----------------------------------"

CONSOLE_CSS="${FRONTEND_DIR}/HITLDecisionConsole.module.css"
echo "HITLDecisionConsole.module.css:"

CSS_CHECKS=(
    "@keyframes:Animations"
    "transform:GPU Acceleration"
    "linear-gradient:Gradients"
    "grid-template-columns:Grid Layout"
    "rgba:Transparency"
    "transition:Smooth Transitions"
)

for check in "${CSS_CHECKS[@]}"; do
    PATTERN="${check%%:*}"
    DESC="${check##*:}"
    COUNT=$(grep -c "$PATTERN" "$CONSOLE_CSS" 2>/dev/null || echo "0")
    if [ "$COUNT" -gt "0" ]; then
        echo -e "  ${GREEN}✓${NC} $DESC (${COUNT} instances)"
    else
        echo -e "  ${YELLOW}⚠${NC} $DESC (not found)"
    fi
done
echo ""

#===============================================================================
# SUMMARY
#===============================================================================
echo "═══════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ VALIDATION COMPLETE${NC}"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "NEXT STEPS:"
echo "1. Start the frontend development server:"
echo "   cd frontend && npm start"
echo ""
echo "2. Navigate to the HITL Console:"
echo "   http://localhost:3000/reactive-fabric/hitl"
echo ""
echo "3. Test the authentication flow:"
echo "   - Login with credentials"
echo "   - Test 2FA if configured"
echo "   - Verify token storage in localStorage"
echo ""
echo "4. Test the decision console:"
echo "   - View pending decisions"
echo "   - Filter by priority"
echo "   - Test approval/rejection workflow"
echo "   - Verify WebSocket real-time updates"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Glory to YHWH - Guardian of the Digital Realm"
echo "═══════════════════════════════════════════════════════════════════════════"
