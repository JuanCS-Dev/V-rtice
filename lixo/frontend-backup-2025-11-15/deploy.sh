#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Vértice Frontend - Manual Cloud Run Deployment Script
# ═══════════════════════════════════════════════════════════════════════════
# Usage:
#   ./deploy.sh [environment]
#
# Arguments:
#   environment: dev|staging|production (default: dev)
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated: gcloud auth login
#   2. Project configured: gcloud config set project YOUR_PROJECT_ID
#   3. Cloud Run API enabled: gcloud services enable run.googleapis.com
#   4. Container Registry enabled: gcloud services enable containerregistry.googleapis.com

set -e

# ───────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────────────────────────────────

ENV="${1:-dev}"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-vertice-cybersecurity}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="vertice-frontend-${ENV}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/vertice-frontend:${ENV}-$(date +%Y%m%d-%H%M%S)"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "🚀 Vértice Frontend - Cloud Run Deployment"
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Environment:  ${ENV}"
echo "Project:      ${PROJECT_ID}"
echo "Region:       ${REGION}"
echo "Service:      ${SERVICE_NAME}"
echo "Image:        ${IMAGE_NAME}"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# VALIDATION
# ───────────────────────────────────────────────────────────────────────────

if ! command -v gcloud &> /dev/null; then
    echo "❌ ERROR: gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "❌ ERROR: Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

if [[ ! "$ENV" =~ ^(dev|staging|production)$ ]]; then
    echo "❌ ERROR: Invalid environment. Must be: dev, staging, or production"
    exit 1
fi

# ───────────────────────────────────────────────────────────────────────────
# STEP 1: BUILD DOCKER IMAGE
# ───────────────────────────────────────────────────────────────────────────

echo "📦 STEP 1/3: Building Docker image..."
echo ""

docker build \
    -t "${IMAGE_NAME}" \
    -t "gcr.io/${PROJECT_ID}/vertice-frontend:${ENV}-latest" \
    --build-arg NODE_ENV=production \
    -f Dockerfile \
    .

echo ""
echo "✅ Image built successfully"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# STEP 2: PUSH TO CONTAINER REGISTRY
# ───────────────────────────────────────────────────────────────────────────

echo "☁️  STEP 2/3: Pushing image to Google Container Registry..."
echo ""

docker push "${IMAGE_NAME}"
docker push "gcr.io/${PROJECT_ID}/vertice-frontend:${ENV}-latest"

echo ""
echo "✅ Image pushed successfully"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# STEP 3: DEPLOY TO CLOUD RUN
# ───────────────────────────────────────────────────────────────────────────

echo "🚢 STEP 3/3: Deploying to Cloud Run..."
echo ""

# Set environment variables based on environment
case "$ENV" in
    production)
        ENV_VARS="VITE_ENV=production"
        ENV_VARS="${ENV_VARS},VITE_API_GATEWAY_URL=${VITE_API_GATEWAY_URL:-https://api.vertice.example.com}"
        ENV_VARS="${ENV_VARS},VITE_MAXIMUS_CORE_URL=${VITE_MAXIMUS_CORE_URL:-https://maximus-core.vertice.example.com}"
        MIN_INSTANCES=1
        MAX_INSTANCES=10
        ;;
    staging)
        ENV_VARS="VITE_ENV=staging"
        ENV_VARS="${ENV_VARS},VITE_API_GATEWAY_URL=${VITE_API_GATEWAY_URL:-https://staging-api.vertice.example.com}"
        ENV_VARS="${ENV_VARS},VITE_MAXIMUS_CORE_URL=${VITE_MAXIMUS_CORE_URL:-https://staging-maximus.vertice.example.com}"
        MIN_INSTANCES=0
        MAX_INSTANCES=5
        ;;
    *)
        ENV_VARS="VITE_ENV=development"
        ENV_VARS="${ENV_VARS},VITE_API_GATEWAY_URL=${VITE_API_GATEWAY_URL:-https://dev-api.vertice.example.com}"
        ENV_VARS="${ENV_VARS},VITE_MAXIMUS_CORE_URL=${VITE_MAXIMUS_CORE_URL:-https://dev-maximus.vertice.example.com}"
        MIN_INSTANCES=0
        MAX_INSTANCES=3
        ;;
esac

gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --min-instances="${MIN_INSTANCES}" \
    --max-instances="${MAX_INSTANCES}" \
    --port=8080 \
    --set-env-vars="${ENV_VARS}"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --format="value(status.url)")

echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📊 View logs: gcloud run logs tail ${SERVICE_NAME} --region=${REGION}"
echo "🔍 Describe service: gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
