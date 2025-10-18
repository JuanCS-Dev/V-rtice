#!/bin/bash
set -e

echo "=== FASE 1: Subindo Tier 0 (Infra) ==="

docker compose up -d redis postgres qdrant

echo "Aguardando 30s para inicialização..."
sleep 30

echo "Status Tier 0:"
docker compose ps redis postgres qdrant

echo ""
echo "Healthcheck:"
docker compose ps --filter "name=redis" --filter "status=running" | grep -q "Up" && echo "✅ Redis UP" || echo "❌ Redis DOWN"
docker compose ps --filter "name=postgres" --filter "status=running" | grep -q "Up" && echo "✅ Postgres UP" || echo "❌ Postgres DOWN"
docker compose ps --filter "name=qdrant" --filter "status=running" | grep -q "Up" && echo "✅ Qdrant UP" || echo "❌ Qdrant DOWN"
