#!/bin/bash
# Start Maximus Core test environment

echo "🧪 Starting Maximus Core Test Environment..."

# Check if core is running
if ! docker ps | grep -q vertice-redis; then
    echo "Starting core infrastructure first..."
    ./scripts/start-core.sh
    echo ""
fi

echo "🚀 Starting Maximus dependencies..."
docker compose up -d \
  hcl-kafka \
  maximus-zookeeper-immunity \
  maximus-core

echo ""
echo "⏳ Waiting for services..."
sleep 10

echo ""
echo "📊 Service Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|kafka|zookeeper|maximus-core"

echo ""
echo "💾 Resource Usage:"
docker stats --no-stream | grep -E "CONTAINER|kafka|zookeeper|maximus-core"

echo ""
echo "✅ Maximus test environment ready!"
echo ""
echo "Run tests with:"
echo "  cd backend/services/maximus_core_service"
echo "  pytest tests/unit/ -v --cov"
echo ""
echo "When done, cleanup with:"
echo "  docker compose stop maximus-core hcl-kafka maximus-zookeeper-immunity"
