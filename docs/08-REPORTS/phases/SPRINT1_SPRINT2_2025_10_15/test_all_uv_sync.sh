#!/bin/bash
# Test UV sync on all services

cd /home/juan/vertice-dev/backend/services

SUCCESS=0
FAILED=0
FAILED_SERVICES=()

for dir in */; do
    service="${dir%/}"

    # Skip if no pyproject.toml
    if [ ! -f "$service/pyproject.toml" ]; then
        continue
    fi

    echo -n "Testing $service... "

    cd "$service"

    # Try uv sync with timeout
    if timeout 30 uv sync > /dev/null 2>&1; then
        echo "✅"
        ((SUCCESS++))
    else
        echo "❌"
        ((FAILED++))
        FAILED_SERVICES+=("$service")
    fi

    cd ..
done

echo ""
echo "========================================"
echo "UV SYNC RESULTS"
echo "========================================"
echo "✅ Success: $SUCCESS"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "Failed services:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "  - $service"
    done
fi

echo ""
echo "Total: $((SUCCESS + FAILED)) services tested"
