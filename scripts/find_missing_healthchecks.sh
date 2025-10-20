#!/usr/bin/env bash
# Script to find services missing healthchecks in docker-compose.yml

set -euo pipefail

DOCKER_COMPOSE_FILE="${1:-docker-compose.yml}"

echo "🔍 Scanning $DOCKER_COMPOSE_FILE for services without healthchecks..."
echo ""

# Extract all service names
services=$(grep -E "^  [a-z_-]+:" "$DOCKER_COMPOSE_FILE" | sed 's/:$//' | awk '{print $1}')

missing_count=0
missing_services=()

for service in $services; do
    # Skip volume entries
    if echo "$service" | grep -q "_data$\|_db$\|_config$\|_volume$"; then
        continue
    fi

    # Extract service block and check for healthcheck
    service_block=$(awk "/^  $service:/,/^  [a-z]/" "$DOCKER_COMPOSE_FILE")

    if ! echo "$service_block" | grep -q "healthcheck:"; then
        echo "❌ $service - NO HEALTHCHECK"
        missing_services+=("$service")
        ((missing_count++))
    else
        echo "✅ $service - has healthcheck"
    fi
done

echo ""
echo "========================================="
echo "Summary:"
echo "  Total services missing healthchecks: $missing_count"
echo ""

if [ $missing_count -gt 0 ]; then
    echo "Services without healthchecks:"
    printf '  - %s\n' "${missing_services[@]}"
    exit 1
else
    echo "✅ All services have healthchecks!"
    exit 0
fi
