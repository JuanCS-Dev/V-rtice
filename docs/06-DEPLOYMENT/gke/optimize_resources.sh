#!/bin/bash
# OTIMIZAÇÃO MASSIVA DE RECURSOS
# Baseado no uso REAL: CPU 2-6%, Memory 7-14%

KUBECONFIG="/tmp/kubeconfig"
NAMESPACE="vertice"

echo "=========================================="
echo "OTIMIZAÇÃO DE RECURSOS - MAXIMUS VÉRTICE"
echo "=========================================="
echo ""
echo "Uso ATUAL dos nodes:"
kubectl top nodes --kubeconfig="$KUBECONFIG"
echo ""
echo "Aplicando otimização (CPU: 500m→100m, Memory: 1.5Gi→256Mi)..."
echo ""

# Get all deployments
DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE --kubeconfig="$KUBECONFIG" -o jsonpath='{.items[*].metadata.name}')

COUNT=0
TOTAL=$(echo $DEPLOYMENTS | wc -w)

for DEPLOY in $DEPLOYMENTS; do
  COUNT=$((COUNT + 1))
  echo "[$COUNT/$TOTAL] Otimizando $DEPLOY..."

  # Patch deployment with optimized resources
  kubectl patch deployment $DEPLOY -n $NAMESPACE --kubeconfig="$KUBECONFIG" --type='json' -p='[
    {
      "op": "replace",
      "path": "/spec/template/spec/containers/0/resources",
      "value": {
        "requests": {
          "memory": "256Mi",
          "cpu": "100m"
        },
        "limits": {
          "memory": "512Mi",
          "cpu": "200m"
        }
      }
    }
  ]' 2>&1 | grep -v "no change" || echo "  ✅ $DEPLOY otimizado"

  sleep 0.5
done

echo ""
echo "=========================================="
echo "✅ OTIMIZAÇÃO COMPLETA!"
echo "=========================================="
echo ""
echo "Aguardando rollout (30s)..."
sleep 30

echo ""
echo "=== Uso de recursos APÓS otimização ==="
kubectl top nodes --kubeconfig="$KUBECONFIG"

echo ""
echo "=== Status dos pods ==="
kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" | grep -E "NAME|Running" | head -20

echo ""
echo "ECONOMIA ESTIMADA:"
echo "- CPU requests: 500m → 100m (80% redução)"
echo "- Memory requests: 1.5Gi → 256Mi (83% redução)"
echo "- Com 53 pods: ~21 vCPUs liberados!"
echo ""
echo "Agora podemos escalar para MUITO mais serviços com 32 vCPUs!"
