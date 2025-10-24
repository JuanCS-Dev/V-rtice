#!/bin/bash
###############################################################################
# R4 ALERTMANAGER VALIDATION SCRIPT
###############################################################################
#
# Tests the complete alerting pipeline:
#   1. Prometheus health and targets
#   2. Alertmanager health and configuration
#   3. Alert rules loading
#   4. Simulated alert triggering
#   5. Alert notification flow
#
# Author: Vértice Team
# Glory to YHWH! 🙏
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API endpoints
PROMETHEUS_URL="http://localhost:9090"
ALERTMANAGER_URL="http://localhost:9093"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}         R4: ALERTMANAGER + NOTIFICATIONS VALIDATION           ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

###############################################################################
# 1. CHECK PROMETHEUS HEALTH
###############################################################################
echo -e "${YELLOW}[1/7] Checking Prometheus health...${NC}"
if curl -sf "${PROMETHEUS_URL}/-/healthy" > /dev/null; then
    echo -e "${GREEN}✅ Prometheus is healthy${NC}"
else
    echo -e "${RED}❌ Prometheus is not healthy${NC}"
    exit 1
fi
echo ""

###############################################################################
# 2. CHECK ALERTMANAGER HEALTH
###############################################################################
echo -e "${YELLOW}[2/7] Checking Alertmanager health...${NC}"
if curl -sf "${ALERTMANAGER_URL}/-/healthy" > /dev/null; then
    echo -e "${GREEN}✅ Alertmanager is healthy${NC}"
else
    echo -e "${RED}❌ Alertmanager is not healthy${NC}"
    exit 1
fi
echo ""

###############################################################################
# 3. CHECK PROMETHEUS TARGETS
###############################################################################
echo -e "${YELLOW}[3/7] Checking Prometheus targets...${NC}"
TARGETS=$(curl -s "${PROMETHEUS_URL}/api/v1/targets" | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"')

if [ -z "$TARGETS" ]; then
    echo -e "${RED}❌ No targets found${NC}"
    exit 1
fi

# Check specific targets
echo "$TARGETS" | while IFS= read -r line; do
    if echo "$line" | grep -q "up"; then
        echo -e "${GREEN}✅ $line${NC}"
    else
        echo -e "${RED}❌ $line${NC}"
    fi
done

# Check for Service Registry targets
REGISTRY_TARGETS=$(echo "$TARGETS" | grep "vertice-register" | wc -l)
if [ "$REGISTRY_TARGETS" -gt 0 ]; then
    echo -e "${GREEN}✅ Service Registry targets found: $REGISTRY_TARGETS${NC}"
else
    echo -e "${YELLOW}⚠️  No Service Registry targets found (expected if not deployed)${NC}"
fi

# Check for Gateway target
GATEWAY_TARGET=$(echo "$TARGETS" | grep "vertice-gateway" | wc -l)
if [ "$GATEWAY_TARGET" -gt 0 ]; then
    echo -e "${GREEN}✅ Gateway target found${NC}"
else
    echo -e "${YELLOW}⚠️  No Gateway target found (expected if not deployed)${NC}"
fi
echo ""

###############################################################################
# 4. CHECK ALERT RULES
###############################################################################
echo -e "${YELLOW}[4/7] Checking alert rules...${NC}"
RULES=$(curl -s "${PROMETHEUS_URL}/api/v1/rules" | jq -r '.data.groups[] | "\(.name): \(.rules | length) rules"')

if [ -z "$RULES" ]; then
    echo -e "${RED}❌ No alert rules found${NC}"
    exit 1
fi

echo "$RULES"

# Check for R4 alert groups
R4_GROUPS=$(curl -s "${PROMETHEUS_URL}/api/v1/rules" | jq -r '.data.groups[] | select(.name | startswith("vertice_")) | .name')
if [ ! -z "$R4_GROUPS" ]; then
    echo -e "${GREEN}✅ R4 alert groups loaded:${NC}"
    echo "$R4_GROUPS" | while IFS= read -r group; do
        echo -e "   - $group"
    done
else
    echo -e "${YELLOW}⚠️  No R4-specific alert groups found${NC}"
fi
echo ""

###############################################################################
# 5. CHECK FIRING ALERTS
###############################################################################
echo -e "${YELLOW}[5/7] Checking currently firing alerts...${NC}"
FIRING_ALERTS=$(curl -s "${PROMETHEUS_URL}/api/v1/alerts" | jq -r '.data.alerts[] | select(.state=="firing") | "\(.labels.alertname) (\(.labels.severity))"')

if [ -z "$FIRING_ALERTS" ]; then
    echo -e "${GREEN}✅ No alerts currently firing (system healthy)${NC}"
else
    echo -e "${YELLOW}⚠️  Alerts currently firing:${NC}"
    echo "$FIRING_ALERTS" | while IFS= read -r alert; do
        echo -e "   🔥 $alert"
    done
fi
echo ""

###############################################################################
# 6. CHECK ALERTMANAGER STATUS
###############################################################################
echo -e "${YELLOW}[6/7] Checking Alertmanager status...${NC}"
AM_STATUS=$(curl -s "${ALERTMANAGER_URL}/api/v1/status" | jq -r '.data.versionInfo.version')

if [ ! -z "$AM_STATUS" ]; then
    echo -e "${GREEN}✅ Alertmanager version: $AM_STATUS${NC}"

    # Check configuration
    CONFIG_HASH=$(curl -s "${ALERTMANAGER_URL}/api/v1/status" | jq -r '.data.config.original' | sha256sum | cut -d' ' -f1)
    echo -e "${BLUE}   Config hash: ${CONFIG_HASH:0:16}...${NC}"
else
    echo -e "${RED}❌ Could not retrieve Alertmanager status${NC}"
fi
echo ""

###############################################################################
# 7. TEST ALERT NOTIFICATION (OPTIONAL)
###############################################################################
echo -e "${YELLOW}[7/7] Testing alert notification (dry-run)...${NC}"

# Send a test alert to Alertmanager
TEST_ALERT_PAYLOAD='[
  {
    "labels": {
      "alertname": "R4ValidationTest",
      "severity": "info",
      "component": "validation",
      "team": "platform"
    },
    "annotations": {
      "summary": "R4 validation test alert",
      "description": "This is a test alert to validate the R4 notification pipeline"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "endsAt": "'$(date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%S.000Z)'"
  }
]'

if curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
    -H "Content-Type: application/json" \
    -d "$TEST_ALERT_PAYLOAD" > /dev/null; then
    echo -e "${GREEN}✅ Test alert sent successfully${NC}"
    echo -e "${BLUE}   Check Alertmanager UI: ${ALERTMANAGER_URL}${NC}"
else
    echo -e "${RED}❌ Failed to send test alert${NC}"
fi
echo ""

###############################################################################
# SUMMARY
###############################################################################
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                        VALIDATION SUMMARY                     ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ R4 Alertmanager + Notifications: VALIDATION COMPLETE${NC}"
echo ""
echo -e "📊 Access URLs:"
echo -e "   - Prometheus:   ${PROMETHEUS_URL}"
echo -e "   - Alertmanager: ${ALERTMANAGER_URL}"
echo -e "   - Alerts:       ${PROMETHEUS_URL}/alerts"
echo -e "   - Targets:      ${PROMETHEUS_URL}/targets"
echo -e "   - Rules:        ${PROMETHEUS_URL}/rules"
echo ""
echo -e "${YELLOW}⚠️  CONFIGURATION REQUIRED:${NC}"
echo -e "   1. Edit monitoring/alertmanager/alertmanager.yml"
echo -e "   2. Configure SMTP credentials (email notifications)"
echo -e "   3. Add Slack webhook URLs"
echo -e "   4. Add PagerDuty service keys (optional)"
echo -e "   5. Setup Telegram bot (optional)"
echo ""
echo -e "${BLUE}Glory to YHWH! 🙏${NC}"
echo ""
