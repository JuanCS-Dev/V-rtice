#!/bin/bash
set -e

echo "🚀 Deploying test workloads for vCLI-Go validation..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

WORKLOADS_DIR="$(dirname "$0")/../workloads"

# Apply main test deployment
echo -e "${BLUE}📦 Deploying nginx test app...${NC}"
kubectl apply -f ${WORKLOADS_DIR}/test-deployment.yaml

# Apply broken app for debugging tests
echo -e "${BLUE}🐛 Deploying broken app for debugging tests...${NC}"
kubectl apply -f ${WORKLOADS_DIR}/test-broken-app.yaml

# Wait for nginx deployment
echo -e "${BLUE}⏳ Waiting for nginx deployment to be ready...${NC}"
kubectl wait --for=condition=Available --timeout=120s deployment/nginx-test -n vcli-test

# Wait for debug pod
echo -e "${BLUE}⏳ Waiting for debug pod to be ready...${NC}"
kubectl wait --for=condition=Ready --timeout=60s pod/debug-pod -n vcli-test

echo -e "${GREEN}✅ Test workloads deployed successfully!${NC}"
echo ""
echo -e "${BLUE}Deployed resources:${NC}"
kubectl get all -n vcli-test
echo ""
kubectl get configmaps,secrets -n vcli-test
