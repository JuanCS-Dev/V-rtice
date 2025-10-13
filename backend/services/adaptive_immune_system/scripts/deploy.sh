#!/bin/bash
#
# Deployment script for HITL API
# Supports: staging, production
#
# Usage:
#   ./scripts/deploy.sh <environment> <image_tag>
#
# Examples:
#   ./scripts/deploy.sh staging ghcr.io/user/adaptive-immune:main-abc123
#   ./scripts/deploy.sh production ghcr.io/user/adaptive-immune:v1.0.0

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-}"
IMAGE_TAG="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Validate arguments
if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <environment> <image_tag>"
    echo "Example: $0 staging ghcr.io/user/adaptive-immune:main-abc123"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "Error: Environment must be 'staging' or 'production'"
    exit 1
fi

echo "=========================================================="
echo "Deploying HITL API"
echo "=========================================================="
echo "Environment: $ENVIRONMENT"
echo "Image: $IMAGE_TAG"
echo "=========================================================="
echo

# Function to check health
check_health() {
    local url=$1
    local max_attempts=30
    local attempt=1

    echo -n "Checking health at $url... "

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
            return 0
        fi

        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}✗ Health check failed${NC}"
    return 1
}

# Function to backup current deployment
backup_deployment() {
    echo "Creating deployment backup..."

    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup docker-compose state
    docker-compose ps > "$backup_dir/docker-ps.txt" || true
    docker images | grep adaptive-immune > "$backup_dir/images.txt" || true

    echo "Backup saved to: $backup_dir"
}

# Function to deploy
deploy() {
    local env=$1
    local image=$2

    echo "→ Pulling image..."
    docker pull "$image"

    echo "→ Updating docker-compose..."
    # Update docker-compose to use new image
    export ADAPTIVE_IMMUNE_IMAGE="$image"

    echo "→ Stopping old container..."
    docker-compose stop adaptive_immune_system || true

    echo "→ Starting new container..."
    docker-compose up -d adaptive_immune_system

    echo "→ Waiting for container to start..."
    sleep 5

    # Check health
    local health_url="http://localhost:8003"
    if [ "$env" = "staging" ]; then
        health_url="http://staging-adaptive-immune.example.com"
    elif [ "$env" = "production" ]; then
        health_url="https://adaptive-immune.example.com"
    fi

    if check_health "$health_url"; then
        echo -e "${GREEN}✅ Deployment successful${NC}"
        return 0
    else
        echo -e "${RED}❌ Deployment failed (health check)${NC}"
        return 1
    fi
}

# Function to run post-deployment tests
run_post_deploy_tests() {
    echo
    echo "→ Running post-deployment tests..."

    # Test 1: Basic health check
    echo -n "  Test 1: Health check... "
    if curl -sf "http://localhost:8003/health" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi

    # Test 2: Ready check
    echo -n "  Test 2: Readiness check... "
    if curl -sf "http://localhost:8003/health/ready" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠${NC} (non-blocking)"
    fi

    # Test 3: API response
    echo -n "  Test 3: API response... "
    if curl -sf "http://localhost:8003/hitl/reviews" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Post-deployment tests passed${NC}"
    return 0
}

# Main execution
main() {
    echo "Step 1: Creating backup..."
    backup_deployment

    echo
    echo "Step 2: Deploying..."
    if deploy "$ENVIRONMENT" "$IMAGE_TAG"; then
        echo
        echo "Step 3: Running tests..."
        if run_post_deploy_tests; then
            echo
            echo "=========================================================="
            echo -e "${GREEN}✅ Deployment completed successfully${NC}"
            echo "=========================================================="
            echo "Environment: $ENVIRONMENT"
            echo "Image: $IMAGE_TAG"
            echo "Status: HEALTHY"
            echo "=========================================================="
            exit 0
        else
            echo
            echo "=========================================================="
            echo -e "${RED}❌ Post-deployment tests failed${NC}"
            echo "=========================================================="
            echo "Consider rolling back with:"
            echo "  ./scripts/rollback.sh $ENVIRONMENT"
            echo "=========================================================="
            exit 1
        fi
    else
        echo
        echo "=========================================================="
        echo -e "${RED}❌ Deployment failed${NC}"
        echo "=========================================================="
        echo "Rolling back..."
        "$SCRIPT_DIR/rollback.sh" "$ENVIRONMENT"
        exit 1
    fi
}

# Run main
main
