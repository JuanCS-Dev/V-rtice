#!/bin/bash
# Validate Deterministic Docker Builds
#
# This script builds the Docker image multiple times and verifies
# that the installed packages are IDENTICAL across all builds.
#
# Following Doutrina Vértice - Article II: NO PLACEHOLDER

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="active-immune-core"
TAG="determinism-test"
ITERATIONS="${1:-3}"  # Default 3 iterations, override with argument

echo "🔬 Validating Deterministic Docker Builds"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Image: $IMAGE_NAME:$TAG"
echo "Iterations: $ITERATIONS"
echo ""

cd "$PROJECT_ROOT"

# Clean up old test artifacts
rm -f /tmp/active-immune-packages-*.txt
rm -f /tmp/determinism-test-*.log

# Array to store package list hashes
declare -a PACKAGE_HASHES

for i in $(seq 1 "$ITERATIONS"); do
    echo "[$i/$ITERATIONS] Building Docker image..."

    # Build image with no cache to ensure fresh build
    docker build \
        --no-cache \
        --tag "$IMAGE_NAME:$TAG-$i" \
        --file Dockerfile \
        . > "/tmp/determinism-test-$i.log" 2>&1

    echo "[$i/$ITERATIONS] Extracting installed packages..."

    # Extract package list from container
    docker run --rm "$IMAGE_NAME:$TAG-$i" \
        pip list --format=freeze > "/tmp/active-immune-packages-$i.txt"

    # Calculate hash of package list
    HASH=$(sha256sum "/tmp/active-immune-packages-$i.txt" | awk '{print $1}')
    PACKAGE_HASHES+=("$HASH")

    echo "[$i/$ITERATIONS] Package list hash: $HASH"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Validating Determinism..."
echo ""

# Compare all hashes
FIRST_HASH="${PACKAGE_HASHES[0]}"
ALL_IDENTICAL=true

for i in "${!PACKAGE_HASHES[@]}"; do
    CURRENT_HASH="${PACKAGE_HASHES[$i]}"
    if [ "$CURRENT_HASH" != "$FIRST_HASH" ]; then
        ALL_IDENTICAL=false
        echo "❌ FAILURE: Build $((i+1)) has different packages!"
        echo "   Expected: $FIRST_HASH"
        echo "   Got:      $CURRENT_HASH"

        # Show diff
        echo ""
        echo "Diff between build 1 and build $((i+1)):"
        diff "/tmp/active-immune-packages-1.txt" "/tmp/active-immune-packages-$((i+1)).txt" || true
    else
        echo "✅ Build $((i+1)): IDENTICAL (hash: $CURRENT_HASH)"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$ALL_IDENTICAL" = true ]; then
    echo "🎉 SUCCESS: All $ITERATIONS builds are DETERMINISTIC!"
    echo ""
    echo "Package count: $(wc -l < "/tmp/active-immune-packages-1.txt") packages"
    echo "Hash: $FIRST_HASH"
    echo ""
    echo "Artifacts saved:"
    for i in $(seq 1 "$ITERATIONS"); do
        echo "  - /tmp/active-immune-packages-$i.txt"
    done

    # Cleanup Docker images
    echo ""
    echo "Cleaning up test images..."
    for i in $(seq 1 "$ITERATIONS"); do
        docker rmi "$IMAGE_NAME:$TAG-$i" > /dev/null 2>&1 || true
    done

    exit 0
else
    echo "❌ FAILURE: Builds are NON-DETERMINISTIC!"
    echo ""
    echo "This indicates dependency drift is possible."
    echo "Review the diffs above and check:"
    echo "  1. Lock file is being used (requirements.txt.lock)"
    echo "  2. --no-deps flag is set in Dockerfile"
    echo "  3. No version ranges in lock file (should all be ==)"
    echo ""
    echo "Build logs saved to /tmp/determinism-test-*.log"

    exit 1
fi
