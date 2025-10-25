#!/bin/bash
set -e

# Configurações
PROJECT_ID="${GCP_PROJECT_ID:-projeto-vertice}"
REGION="${GCP_REGION:-us-central1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/vcli-go"
SERVICE_NAME="vcli-go"

echo "🚀 Iniciando redeploy..."

# Step 1: Build nova imagem
echo "📦 Building imagem..."
docker build -t ${IMAGE_NAME}:latest .

# Step 2: Tag com timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${TIMESTAMP}

# Step 3: Push para registry
echo "⬆️  Pushing para GCR..."
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:${TIMESTAMP}

# Step 4: Update Cloud Run
echo "🔄 Atualizando Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:${TIMESTAMP} \
  --region ${REGION} \
  --platform managed

# Step 5: Obter URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format='value(status.url)')

echo "🎉 Redeploy completo!"
echo "Service URL: $SERVICE_URL"
