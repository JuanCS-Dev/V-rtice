#!/bin/bash
# Quick script to expose API Gateway via LoadBalancer (simpler than Ingress)

set -e

KUBECONFIG="/tmp/kubeconfig"
NAMESPACE="vertice"

echo "==========================================="
echo "EXPOSING API GATEWAY VIA LOADBALANCER"
echo "==========================================="
echo ""

# Patch api-gateway service to LoadBalancer type
echo "Changing api-gateway service to LoadBalancer type..."
kubectl patch service api-gateway -n $NAMESPACE --kubeconfig="$KUBECONFIG" -p '{"spec":{"type":"LoadBalancer"}}'

echo ""
echo "Waiting for external IP (this takes 1-2 minutes)..."
sleep 60

echo ""
echo "=== API Gateway Service Status ==="
kubectl get service api-gateway -n $NAMESPACE --kubeconfig="$KUBECONFIG"

EXTERNAL_IP=$(kubectl get service api-gateway -n $NAMESPACE --kubeconfig="$KUBECONFIG" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$EXTERNAL_IP" ]; then
  echo ""
  echo "⚠️  External IP not yet assigned. Wait a bit longer and check with:"
  echo "kubectl get service api-gateway -n vertice --kubeconfig=/tmp/kubeconfig"
else
  echo ""
  echo "==========================================="
  echo "✅ API GATEWAY EXPOSED"
  echo "==========================================="
  echo ""
  echo "API Gateway URL: http://$EXTERNAL_IP:8000"
  echo ""
  echo "Test it:"
  echo "curl http://$EXTERNAL_IP:8000/health"
  echo ""
  echo "Next: Update frontend with this URL:"
  echo "VITE_API_GATEWAY_URL=http://$EXTERNAL_IP:8000"
fi
