#!/bin/bash
set -e

echo "=== FASE 2: Subindo Tier 1 (Core Services) ==="

docker compose up -d \
  api_gateway \
  sinesp_service \
  domain_service \
  ip_intelligence_service \
  nmap_service \
  auth_service

echo "Aguardando 60s para inicialização..."
sleep 60

echo "Status Tier 1:"
docker compose ps api_gateway sinesp_service domain_service ip_intelligence_service nmap_service auth_service

echo ""
echo "Healthcheck API Gateway:"
if curl -sf http://localhost:8000/health > /dev/null; then
  echo "✅ API Gateway HEALTHY"
  curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
else
  echo "❌ API Gateway UNHEALTHY"
  docker compose logs --tail=50 api_gateway
fi
