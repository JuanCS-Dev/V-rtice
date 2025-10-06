#!/bin/bash
# Access development container shell
# Authors: Juan & Claude

set -e

# Check if container is running
if ! docker ps | grep -q active_immune_core_dev; then
    echo "❌ Error: Development container is not running"
    echo "Please run ./scripts/dev-up.sh first"
    exit 1
fi

echo "🐚 Opening shell in development container..."
echo "   (Type 'exit' to leave)"
echo ""

# Open shell
docker exec -it active_immune_core_dev /bin/bash
