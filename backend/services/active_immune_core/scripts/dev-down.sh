#!/bin/bash
# Stop development environment
# Authors: Juan & Claude

set -e

echo "🛑 Stopping Active Immune Core Development Environment..."
echo ""

# Stop all services
docker-compose -f docker-compose.dev.yml down

echo ""
echo "✅ Development environment stopped"
echo ""
echo "💡 To remove volumes (delete all data):"
echo "   docker-compose -f docker-compose.dev.yml down -v"
echo ""
