#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:-projeto-vertice}"
CLUSTER_NAME="${GKE_CLUSTER:-vertice-us-cluster}"
CLUSTER_ZONE="${GKE_ZONE:-us-east1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/vcli-go"
NAMESPACE="${K8S_NAMESPACE:-default}"

echo "🚀 Redeploy vcli-go para GKE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Deletar pods existentes (força pull da nova imagem)
echo "🗑️  Deletando pods existentes..."
kubectl delete pods -n ${NAMESPACE} -l app=vcli-go 2>/dev/null || echo "Nenhum pod encontrado"

# Step 2: Restart deployment
echo "🔄 Restartando deployment..."
kubectl rollout restart deployment/vcli-go -n ${NAMESPACE}

# Step 3: Aguardar rollout
echo "⏳ Aguardando rollout..."
kubectl rollout status deployment/vcli-go -n ${NAMESPACE} --timeout=5m

# Step 4: Verificar pods
echo "✅ Verificando pods:"
kubectl get pods -n ${NAMESPACE} -l app=vcli-go

echo ""
echo "🎉 Redeploy concluído!"
echo "Nova imagem: ${IMAGE_NAME}:latest (sha256:b51443527c22)"
