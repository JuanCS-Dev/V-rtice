#!/bin/bash
#
# Rollback script for HITL API
#
# Usage:
#   ./scripts/rollback.sh <environment> [backup_timestamp]
#
# Examples:
#   ./scripts/rollback.sh staging
#   ./scripts/rollback.sh production 20251013_143022

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-}"
BACKUP_TIMESTAMP="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Validate arguments
if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment> [backup_timestamp]"
    echo "Example: $0 staging"
    exit 1
fi

echo "=========================================================="
echo "Rollback HITL API"
echo "=========================================================="
echo "Environment: $ENVIRONMENT"
echo "=========================================================="
echo

# Function to find latest backup
find_latest_backup() {
    local backup_dir="$PROJECT_ROOT/backups"

    if [ ! -d "$backup_dir" ]; then
        echo "No backups found"
        return 1
    fi

    local latest=$(ls -1t "$backup_dir" | head -1)
    echo "$latest"
}

# Function to rollback using docker
rollback_docker() {
    echo "→ Rolling back deployment..."

    # Get previous image
    local previous_image=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep adaptive-immune | sed -n '2p')

    if [ -z "$previous_image" ]; then
        echo -e "${RED}✗ No previous image found${NC}"
        return 1
    fi

    echo "Previous image: $previous_image"

    # Stop current container
    echo "→ Stopping current container..."
    docker-compose stop adaptive_immune_system || true

    # Start with previous image
    echo "→ Starting previous version..."
    export ADAPTIVE_IMMUNE_IMAGE="$previous_image"
    docker-compose up -d adaptive_immune_system

    # Wait for startup
    sleep 5

    # Check health
    if curl -sf "http://localhost:8003/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Rollback successful${NC}"
        return 0
    else
        echo -e "${RED}✗ Rollback health check failed${NC}"
        return 1
    fi
}

# Function to check if rollback was successful
verify_rollback() {
    echo
    echo "→ Verifying rollback..."

    # Test 1: Health check
    echo -n "  Test 1: Health check... "
    if curl -sf "http://localhost:8003/health" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi

    # Test 2: API endpoint
    echo -n "  Test 2: API endpoint... "
    if curl -sf "http://localhost:8003/hitl/reviews" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi

    # Test 3: Check logs for errors
    echo -n "  Test 3: Error logs... "
    ERROR_COUNT=$(docker logs vertice-adaptive-immune --since 1m 2>&1 | grep -i error | wc -l)
    if [ "$ERROR_COUNT" -lt 5 ]; then
        echo -e "${GREEN}✓${NC} ($ERROR_COUNT errors)"
    else
        echo -e "${YELLOW}⚠${NC} ($ERROR_COUNT errors)"
    fi

    echo -e "${GREEN}✅ Rollback verified${NC}"
    return 0
}

# Function to create incident report
create_incident_report() {
    local report_file="$PROJECT_ROOT/incidents/incident_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p "$PROJECT_ROOT/incidents"

    cat > "$report_file" <<EOF
INCIDENT REPORT
===============

Date: $(date)
Environment: $ENVIRONMENT
Action: Rollback
Reason: Deployment failure or manual rollback

Timeline:
---------
$(date): Rollback initiated
$(date): Previous version restored
$(date): Health checks completed

Current Status:
--------------
Container: $(docker ps --filter name=adaptive-immune --format "{{.Status}}")
Image: $(docker ps --filter name=adaptive-immune --format "{{.Image}}")

Logs (last 50 lines):
--------------------
$(docker logs vertice-adaptive-immune --tail 50 2>&1)

Next Steps:
-----------
1. Investigate root cause of failure
2. Fix issues in code/config
3. Re-deploy with fixes
4. Update documentation

EOF

    echo "Incident report created: $report_file"
}

# Main execution
main() {
    echo "Step 1: Finding backup..."
    if [ -z "$BACKUP_TIMESTAMP" ]; then
        BACKUP_TIMESTAMP=$(find_latest_backup)
        echo "Using latest backup: $BACKUP_TIMESTAMP"
    fi

    echo
    echo "Step 2: Rolling back..."
    if rollback_docker; then
        echo
        echo "Step 3: Verifying rollback..."
        if verify_rollback; then
            echo
            echo "Step 4: Creating incident report..."
            create_incident_report

            echo
            echo "=========================================================="
            echo -e "${GREEN}✅ Rollback completed successfully${NC}"
            echo "=========================================================="
            echo "Environment: $ENVIRONMENT"
            echo "Status: HEALTHY"
            echo "Incident report: incidents/incident_*.txt"
            echo "=========================================================="
            exit 0
        else
            echo
            echo "=========================================================="
            echo -e "${RED}❌ Rollback verification failed${NC}"
            echo "=========================================================="
            echo "Manual intervention required"
            echo "=========================================================="
            exit 1
        fi
    else
        echo
        echo "=========================================================="
        echo -e "${RED}❌ Rollback failed${NC}"
        echo "=========================================================="
        echo "Manual intervention required"
        echo "Check container logs:"
        echo "  docker logs vertice-adaptive-immune"
        echo "=========================================================="
        exit 1
    fi
}

# Run main
main
