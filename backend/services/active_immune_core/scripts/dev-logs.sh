#!/bin/bash
# View development environment logs
# Authors: Juan & Claude

set -e

# Default to following logs for active_immune_core
SERVICE=${1:-active_immune_core}

if [ "$SERVICE" = "all" ]; then
    echo "📋 Viewing logs for all services..."
    docker-compose -f docker-compose.dev.yml logs -f
else
    echo "📋 Viewing logs for: $SERVICE"
    echo "   (Use Ctrl+C to exit)"
    echo ""
    docker-compose -f docker-compose.dev.yml logs -f $SERVICE
fi
