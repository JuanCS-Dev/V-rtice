#!/bin/bash
# Start only core infrastructure services

echo "🚀 Starting Core Infrastructure..."

docker compose up -d \
  vertice-redis \
  vertice-postgres \
  vertice-qdrant \
  vertice-grafana

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

echo ""
echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|redis|postgres|qdrant|grafana"

echo ""
echo "💾 Resource Usage:"
docker stats --no-stream | grep -E "CONTAINER|redis|postgres|qdrant|grafana"

echo ""
echo "✅ Core infrastructure ready!"
echo "   Redis: localhost:6379"
echo "   PostgreSQL: localhost:5432"
echo "   Qdrant: localhost:6333"
echo "   Grafana: http://localhost:3000"
