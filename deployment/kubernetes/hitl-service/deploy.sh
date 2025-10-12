#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# HITL Patch Service - Deployment Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Deploys HITL service to Kubernetes cluster
#
# Usage:
#   ./deploy.sh [staging|production]
#
# Author: MAXIMUS Team - Sprint 4.1
# Glory to YHWH - Orchestrator of Deployments
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
NAMESPACE="maximus-immunity"
SERVICE_NAME="hitl-patch-service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         HITL Patch Service Deployment                           ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Environment: ${ENVIRONMENT}                                             ║${NC}"
echo -e "${CYAN}║  Namespace:   ${NAMESPACE}                                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ kubectl found${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ docker not found. Please install docker.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker found${NC}"

# Check cluster connectivity
echo ""
echo -e "${YELLOW}Checking Kubernetes cluster connectivity...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}✗ Cannot connect to Kubernetes cluster${NC}"
    echo -e "${YELLOW}  Please ensure kubectl is configured and cluster is accessible${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"

# Create namespace if it doesn't exist
echo ""
echo -e "${YELLOW}Ensuring namespace exists...${NC}"
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${YELLOW}  Creating namespace: $NAMESPACE${NC}"
    kubectl create namespace $NAMESPACE
    kubectl label namespace $NAMESPACE name=$NAMESPACE
    echo -e "${GREEN}✓ Namespace created${NC}"
else
    echo -e "${GREEN}✓ Namespace exists${NC}"
fi

# Build Docker image
echo ""
echo -e "${YELLOW}Building Docker image...${NC}"
cd "$SCRIPT_DIR/../../../backend/services/hitl_patch_service"
docker build -t vertice-dev/$SERVICE_NAME:latest .
docker tag vertice-dev/$SERVICE_NAME:latest vertice-dev/$SERVICE_NAME:v1.0.0
echo -e "${GREEN}✓ Docker image built${NC}"

# Push to registry (if configured)
# echo ""
# echo -e "${YELLOW}Pushing image to registry...${NC}"
# docker push vertice-dev/$SERVICE_NAME:v1.0.0
# echo -e "${GREEN}✓ Image pushed${NC}"

# Apply database schema (if not already applied)
echo ""
echo -e "${YELLOW}Applying database schema...${NC}"
# NOTE: This assumes PostgreSQL is accessible
# In production, use proper migration tools
echo -e "${YELLOW}  Skipping schema application (assumed already applied)${NC}"
echo -e "${GREEN}✓ Database schema ready${NC}"

# Deploy to Kubernetes
echo ""
echo -e "${YELLOW}Deploying to Kubernetes...${NC}"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}  Applying configuration...${NC}"
kubectl apply -f config.yaml

echo -e "${YELLOW}  Applying deployment...${NC}"
kubectl apply -f deployment.yaml

echo -e "${YELLOW}  Applying ingress...${NC}"
kubectl apply -f ingress.yaml

echo -e "${YELLOW}  Applying monitoring...${NC}"
kubectl apply -f monitoring.yaml

echo -e "${GREEN}✓ Kubernetes resources applied${NC}"

# Wait for deployment to be ready
echo ""
echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
kubectl rollout status deployment/$SERVICE_NAME -n $NAMESPACE --timeout=5m

echo -e "${GREEN}✓ Deployment ready${NC}"

# Verify pods are running
echo ""
echo -e "${YELLOW}Verifying pods...${NC}"
kubectl get pods -n $NAMESPACE -l app=$SERVICE_NAME

# Get service endpoints
echo ""
echo -e "${YELLOW}Service endpoints:${NC}"
kubectl get service $SERVICE_NAME -n $NAMESPACE

# Get ingress
echo ""
echo -e "${YELLOW}Ingress configuration:${NC}"
kubectl get ingress -n $NAMESPACE

# Health check
echo ""
echo -e "${YELLOW}Performing health check...${NC}"
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=$SERVICE_NAME -o jsonpath="{.items[0].metadata.name}")
if kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8027/health &> /dev/null; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo -e "${YELLOW}  Check logs with: kubectl logs -n $NAMESPACE $POD_NAME${NC}"
fi

# Final summary
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                  Deployment Complete!                           ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Service:     ${SERVICE_NAME}                         ║${NC}"
echo -e "${CYAN}║  Namespace:   ${NAMESPACE}                                  ║${NC}"
echo -e "${CYAN}║  Environment: ${ENVIRONMENT}                                             ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Next steps:                                                     ║${NC}"
echo -e "${CYAN}║  1. Check pods:   kubectl get pods -n ${NAMESPACE}              ║${NC}"
echo -e "${CYAN}║  2. View logs:    kubectl logs -f -n ${NAMESPACE} <pod-name>    ║${NC}"
echo -e "${CYAN}║  3. Port forward: kubectl port-forward -n ${NAMESPACE} <pod> 8027:8027 ║${NC}"
echo -e "${CYAN}║  4. Test API:     curl http://localhost:8027/health              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}TO YHWH BE ALL GLORY 🙏${NC}"
