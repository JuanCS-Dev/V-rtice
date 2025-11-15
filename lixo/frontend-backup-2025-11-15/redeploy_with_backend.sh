#!/bin/bash
# Redeploy frontend with backend URLs configured

set -e

echo "=========================================="
echo "REDEPLOYING FRONTEND WITH BACKEND URLs"
echo "=========================================="
echo ""

# Load production env vars
export VITE_API_GATEWAY_URL="http://34.148.161.131:8000"
export VITE_MAXIMUS_CORE_URL="http://34.148.161.131:8038"
export VITE_AUTH_SERVICE_URL="http://34.148.161.131:8600"

echo "Building frontend with production config..."
npm run build

echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy vertice-frontend \
  --source=. \
  --region=us-east1 \
  --project=projeto-vertice \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="VITE_API_GATEWAY_URL=$VITE_API_GATEWAY_URL,VITE_MAXIMUS_CORE_URL=$VITE_MAXIMUS_CORE_URL" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3

echo ""
echo "=========================================="
echo "✅ FRONTEND REDEPLOYED"
echo "=========================================="
echo ""
echo "Frontend URL: https://vertice-frontend-vuvnhfmzpa-ue.a.run.app"
echo "API Gateway: $VITE_API_GATEWAY_URL"
echo ""
echo "Test it:"
echo "curl https://vertice-frontend-vuvnhfmzpa-ue.a.run.app"
