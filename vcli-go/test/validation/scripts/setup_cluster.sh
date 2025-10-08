#!/bin/bash
set -e

echo "🚀 Setting up Kind cluster for vCLI-Go validation..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

CLUSTER_NAME="vcli-validation"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
KUBECONFIG_FILE="${PROJECT_ROOT}/test/validation/kubeconfig"

# Use local kubeconfig
export KUBECONFIG="${KUBECONFIG_FILE}"
mkdir -p "$(dirname "${KUBECONFIG_FILE}")"

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo -e "${RED}❌ kind not found. Please install kind first.${NC}"
    echo "Visit: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

# Delete existing cluster if exists
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo -e "${BLUE}🗑️  Deleting existing cluster...${NC}"
    kind delete cluster --name ${CLUSTER_NAME}
fi

# Create Kind cluster
echo -e "${BLUE}📦 Creating Kind cluster...${NC}"
cat <<EOF | kind create cluster --name ${CLUSTER_NAME} --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 8443
    protocol: TCP
EOF

# Wait for cluster to be ready
echo -e "${BLUE}⏳ Waiting for cluster to be ready...${NC}"
kubectl wait --for=condition=Ready nodes --all --timeout=120s

# Install metrics-server
echo -e "${BLUE}📊 Installing metrics-server...${NC}"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics-server for Kind (insecure TLS)
kubectl patch -n kube-system deployment metrics-server --type=json -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'

# Wait for metrics-server to be ready
echo -e "${BLUE}⏳ Waiting for metrics-server to be ready...${NC}"
kubectl wait --for=condition=Available --timeout=120s deployment/metrics-server -n kube-system

# Create test namespaces
echo -e "${BLUE}🏗️  Creating test namespaces...${NC}"
kubectl create namespace vcli-test || true
kubectl create namespace vcli-test-2 || true

# Verify cluster is working
echo -e "${BLUE}✅ Verifying cluster...${NC}"
kubectl cluster-info
kubectl get nodes
kubectl top nodes || echo "⚠️  Metrics not ready yet (expected)"

echo -e "${GREEN}✅ Cluster setup complete!${NC}"
echo -e "${GREEN}Cluster name: ${CLUSTER_NAME}${NC}"
echo -e "${GREEN}Kubeconfig: ${KUBECONFIG_FILE}${NC}"
echo ""
echo -e "${BLUE}To use this cluster:${NC} export KUBECONFIG=${KUBECONFIG_FILE}"
echo -e "${BLUE}To delete cluster:${NC} kind delete cluster --name ${CLUSTER_NAME}"
