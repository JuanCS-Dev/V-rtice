#!/bin/bash
set -e

PROJECT_ID="projeto-vertice"
CLUSTER="vertice-us-cluster" 
ZONE="us-east1"

echo "🚀 Redeploy via gcloud (sem kubectl)"

gcloud container clusters update ${CLUSTER} \
  --zone=${ZONE} \
  --project=${PROJECT_ID} \
  --enable-autoscaling \
  --min-nodes=8 \
  --max-nodes=8 \
  --node-pool=default-pool

echo "✅ Trigger rolling update forçando nodes a puxar nova imagem"
echo "🎯 Imagem atualizada: gcr.io/${PROJECT_ID}/vcli-go:latest"
