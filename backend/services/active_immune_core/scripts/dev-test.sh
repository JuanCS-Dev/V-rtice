#!/bin/bash
# Run tests in development environment
# Authors: Juan & Claude

set -e

echo "🧪 Running tests in development container..."
echo ""

# Check if container is running
if ! docker ps | grep -q active_immune_core_dev; then
    echo "❌ Error: Development container is not running"
    echo "Please run ./scripts/dev-up.sh first"
    exit 1
fi

# Run tests inside container
docker exec -it active_immune_core_dev python -m pytest "${@:-.}" -v

echo ""
echo "✅ Tests completed"
