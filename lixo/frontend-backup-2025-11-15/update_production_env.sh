#!/bin/bash
# Script to update .env.production with GKE LoadBalancer IPs
# Padrão Pagani: "O simples funciona"

set -euo pipefail

KUBECONFIG=/tmp/kubeconfig

echo "📡 Fetching GKE Service IPs..."

# Get LoadBalancer IP
API_GW_IP=$(kubectl --kubeconfig=$KUBECONFIG get svc api-gateway -n vertice -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "✅ API Gateway LoadBalancer: $API_GW_IP"
echo ""
echo "💾 Updating .env.production with GKE IPs..."

# Update .env.production
sed -i "s|VITE_API_GATEWAY_URL=.*|VITE_API_GATEWAY_URL=http://$API_GW_IP:8000|" .env.production
sed -i "s|VITE_OSINT_API_URL=.*|VITE_OSINT_API_URL=http://$API_GW_IP:8000|" .env.production
sed -i "s|VITE_CONSCIOUSNESS_WS_URL=.*|VITE_CONSCIOUSNESS_WS_URL=ws://$API_GW_IP:8000/stream/consciousness/ws|" .env.production
sed -i "s|VITE_APV_WS_URL=.*|VITE_APV_WS_URL=ws://$API_GW_IP:8000/stream/apv/ws|" .env.production

echo "✅ .env.production updated successfully!"
echo ""
echo "📋 Production URLs:"
echo "  API Gateway: http://$API_GW_IP:8000"
echo ""
echo "🚀 Ready to build for production: npm run build"
