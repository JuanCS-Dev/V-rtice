#!/bin/bash
# Health Check Script for Vértice GKE Deployment
# Padrão Pagani: "O simples funciona"

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KUBECONFIG="${KUBECONFIG:-/tmp/kubeconfig}"
NAMESPACE="vertice"
PROJECT="projeto-vertice"
CLUSTER="vertice-us-cluster"
REGION="us-east1"

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Vértice Health Check - GKE Deployment      ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" == "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" == "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# 1. Check kubectl config
echo -e "${BLUE}[1/6] Verificando configuração kubectl...${NC}"
if [ -f "$KUBECONFIG" ]; then
    print_status "OK" "Kubeconfig encontrado: $KUBECONFIG"
else
    print_status "ERROR" "Kubeconfig não encontrado. Executando gcloud get-credentials..."
    gcloud container clusters get-credentials $CLUSTER --region=$REGION --project=$PROJECT
    export KUBECONFIG=/tmp/kubeconfig
fi
echo ""

# 2. Check cluster connectivity
echo -e "${BLUE}[2/6] Testando conectividade com cluster...${NC}"
if KUBECONFIG=$KUBECONFIG kubectl get nodes &>/dev/null; then
    NODE_COUNT=$(KUBECONFIG=$KUBECONFIG kubectl get nodes --no-headers | wc -l)
    print_status "OK" "Cluster acessível - $NODE_COUNT nós ativos"
else
    print_status "ERROR" "Não foi possível conectar ao cluster"
    exit 1
fi
echo ""

# 3. Check pod status
echo -e "${BLUE}[3/6] Analisando status dos pods...${NC}"
TOTAL_PODS=$(KUBECONFIG=$KUBECONFIG kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
RUNNING_PODS=$(KUBECONFIG=$KUBECONFIG kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep -c "Running" || true)
PENDING_PODS=$(KUBECONFIG=$KUBECONFIG kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep -c "Pending" || true)
FAILED_PODS=$(KUBECONFIG=$KUBECONFIG kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep -cE "Error|CrashLoopBackOff|ImagePullBackOff" || true)

if [ $TOTAL_PODS -eq 0 ]; then
    print_status "ERROR" "Nenhum pod encontrado no namespace $NAMESPACE"
else
    HEALTH_PERCENT=$((RUNNING_PODS * 100 / TOTAL_PODS))
    print_status "OK" "Total de pods: $TOTAL_PODS"
    print_status "OK" "Pods Running: $RUNNING_PODS (${HEALTH_PERCENT}%)"

    if [ $PENDING_PODS -gt 0 ]; then
        print_status "WARN" "Pods Pending: $PENDING_PODS"
    fi

    if [ $FAILED_PODS -gt 0 ]; then
        print_status "WARN" "Pods com problemas: $FAILED_PODS"
        echo -e "\n${YELLOW}Pods problemáticos:${NC}"
        KUBECONFIG=$KUBECONFIG kubectl get pods -n $NAMESPACE --no-headers | grep -E "Error|CrashLoopBackOff|ImagePullBackOff" | awk '{print "  - " $1 " (" $3 ")"}'
    fi
fi
echo ""

# 4. Check services
echo -e "${BLUE}[4/6] Verificando serviços...${NC}"
SERVICES=$(KUBECONFIG=$KUBECONFIG kubectl get svc -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
print_status "OK" "Serviços ativos: $SERVICES"
echo ""

# 5. Check resource usage
echo -e "${BLUE}[5/6] Verificando uso de recursos...${NC}"
if KUBECONFIG=$KUBECONFIG kubectl top nodes &>/dev/null; then
    echo -e "${GREEN}Uso de CPU/Memória dos nós:${NC}"
    KUBECONFIG=$KUBECONFIG kubectl top nodes | head -6
else
    print_status "WARN" "Metrics Server não disponível"
fi
echo ""

# 6. Check recent events
echo -e "${BLUE}[6/6] Verificando eventos recentes...${NC}"
WARNING_EVENTS=$(KUBECONFIG=$KUBECONFIG kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' 2>/dev/null | grep -c "Warning" || true)
if [ $WARNING_EVENTS -gt 0 ]; then
    print_status "WARN" "Eventos de Warning encontrados: $WARNING_EVENTS"
    echo -e "\n${YELLOW}Últimos 5 warnings:${NC}"
    KUBECONFIG=$KUBECONFIG kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | grep "Warning" | tail -5
else
    print_status "OK" "Nenhum evento de Warning recente"
fi
echo ""

# Summary
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              RESUMO DO HEALTH CHECK           ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "Cluster: ${GREEN}$CLUSTER${NC}"
echo -e "Namespace: ${GREEN}$NAMESPACE${NC}"
echo -e "Saúde geral: ${GREEN}${HEALTH_PERCENT}%${NC} dos pods Running"
echo ""

if [ $HEALTH_PERCENT -ge 80 ]; then
    echo -e "${GREEN}✓ Sistema operacional!${NC}"
    exit 0
elif [ $HEALTH_PERCENT -ge 50 ]; then
    echo -e "${YELLOW}⚠ Sistema parcialmente operacional${NC}"
    exit 0
else
    echo -e "${RED}✗ Sistema com problemas críticos${NC}"
    exit 1
fi
