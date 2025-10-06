#!/bin/bash
# Start development environment
# Authors: Juan & Claude

set -e

echo "🚀 Starting Active Immune Core Development Environment..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📋 Creating .env from .env.example..."
        cp .env.example .env
        echo "✅ .env created (please review and update as needed)"
        echo ""
    else
        echo "⚠️  Warning: .env.example not found"
    fi
fi

# Start services
echo "🐳 Starting Docker Compose services..."
docker-compose -f docker-compose.dev.yml up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check service health
echo ""
echo "🔍 Checking service status:"
docker-compose -f docker-compose.dev.yml ps

echo ""
echo "✅ Development environment is running!"
echo ""
echo "📍 Services:"
echo "   - Active Immune Core API: http://localhost:8200"
echo "   - API Documentation:      http://localhost:8200/docs"
echo "   - Health Check:           http://localhost:8200/health"
echo "   - Metrics:                http://localhost:8200/metrics"
echo "   - Prometheus:             http://localhost:9090"
echo "   - Grafana:                http://localhost:3000 (admin/admin)"
echo "   - Kafka:                  localhost:9094"
echo "   - Redis:                  localhost:6379"
echo "   - PostgreSQL:             localhost:5432"
echo ""
echo "💡 Useful commands:"
echo "   - View logs:    ./scripts/dev-logs.sh"
echo "   - Run tests:    ./scripts/dev-test.sh"
echo "   - Stop all:     ./scripts/dev-down.sh"
echo "   - Shell access: ./scripts/dev-shell.sh"
echo ""
