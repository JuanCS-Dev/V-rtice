#!/bin/bash
set -e

# 🧬 DEPLOY DO ORGANISMO VÉRTICE NO GKE
# Script de deploy sequencial respeitando dependências entre camadas

# Adicionar gcloud SDK ao PATH
export PATH="/home/maximus/Documentos/V-rtice/google-cloud-sdk/bin:$PATH"

KUBECTL="/home/maximus/Documentos/V-rtice/google-cloud-sdk/bin/kubectl"
MANIFESTS="/home/maximus/Documentos/V-rtice/k8s"
CLUSTER_NAME="vertice-us-cluster"
REGION="us-east1"

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧬 INICIANDO DEPLOY DO ORGANISMO VÉRTICE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verificar conexão com cluster
echo -e "${YELLOW}📡 Verificando conexão com cluster...${NC}"
if ! $KUBECTL cluster-info &> /dev/null; then
    echo -e "${YELLOW}⚙️  Configurando kubectl para o cluster...${NC}"
    /home/maximus/Documentos/V-rtice/google-cloud-sdk/bin/gcloud container clusters get-credentials \
        $CLUSTER_NAME --region=$REGION
fi
echo -e "${GREEN}✅ Conectado ao cluster $CLUSTER_NAME${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# FASE 1: NAMESPACE, CONFIGMAPS E SECRETS
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🏗️  FASE 1: Configuração Base${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}📦 Criando namespace...${NC}"
$KUBECTL apply -f $MANIFESTS/namespaces/vertice-namespace.yaml
echo ""

echo -e "${YELLOW}🔐 Criando secrets...${NC}"
$KUBECTL apply -f $MANIFESTS/secrets/vertice-core-secrets.yaml
echo ""

echo -e "${YELLOW}⚙️  Criando configmaps...${NC}"
$KUBECTL apply -f $MANIFESTS/configmaps/global-config.yaml
echo ""

echo -e "${GREEN}✅ Configuração base completa${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# FASE 2: CAMADA 1 - FUNDAÇÃO (Infraestrutura)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🏛️  CAMADA 1 - FUNDAÇÃO${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. PostgreSQL
echo -e "${YELLOW}[1/5] 🗄️  Deployando PostgreSQL...${NC}"
$KUBECTL apply -f $MANIFESTS/camada-1-fundacao/postgres-statefulset.yaml
echo -e "      Aguardando PostgreSQL ficar ready..."
$KUBECTL wait --for=condition=ready pod -l app=postgres -n vertice --timeout=300s
echo -e "${GREEN}      ✅ PostgreSQL RUNNING${NC}"
echo ""

# 2. Redis
echo -e "${YELLOW}[2/5] 📮 Deployando Redis...${NC}"
$KUBECTL apply -f $MANIFESTS/camada-1-fundacao/redis-deployment.yaml
echo -e "      Aguardando Redis ficar ready..."
$KUBECTL wait --for=condition=ready pod -l app=redis -n vertice --timeout=180s
echo -e "${GREEN}      ✅ Redis RUNNING${NC}"
echo ""

# 3. Kafka
echo -e "${YELLOW}[3/5] 📡 Deployando Kafka + Zookeeper...${NC}"
$KUBECTL apply -f $MANIFESTS/camada-1-fundacao/kafka-statefulset.yaml
echo -e "      Aguardando Kafka ficar ready..."
$KUBECTL wait --for=condition=ready pod -l app=kafka -n vertice --timeout=300s
echo -e "${GREEN}      ✅ Kafka RUNNING${NC}"
echo ""

# 4. Auth Service
echo -e "${YELLOW}[4/5] 🔐 Deployando Auth Service...${NC}"
$KUBECTL apply -f $MANIFESTS/camada-1-fundacao/auth-service-deployment.yaml
echo -e "      Aguardando Auth Service ficar ready..."
$KUBECTL wait --for=condition=ready pod -l app=auth-service -n vertice --timeout=180s
echo -e "${GREEN}      ✅ Auth Service RUNNING${NC}"
echo ""

# 5. API Gateway
echo -e "${YELLOW}[5/5] 🚪 Deployando API Gateway...${NC}"
$KUBECTL apply -f $MANIFESTS/camada-1-fundacao/api-gateway-deployment.yaml
echo -e "      Aguardando API Gateway ficar ready..."
$KUBECTL wait --for=condition=ready pod -l app=api-gateway -n vertice --timeout=180s
echo -e "${GREEN}      ✅ API Gateway RUNNING${NC}"
echo ""

echo -e "${GREEN}✅ CAMADA 1 - FUNDAÇÃO COMPLETA${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# FASE 3: CAMADA 2 - CONSCIÊNCIA (MAXIMUS)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧠 CAMADA 2 - CONSCIÊNCIA (MAXIMUS)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Deployando 5 serviços MAXIMUS em paralelo...${NC}"
$KUBECTL apply -f $MANIFESTS/camada-2-consciencia/
echo -e "Aguardando todos os serviços ficarem ready..."
$KUBECTL wait --for=condition=ready pod -l tier=consciencia -n vertice --timeout=300s
echo -e "${GREEN}✅ CAMADA 2 - CONSCIÊNCIA COMPLETA${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# FASE 4: CAMADA 3 - IMUNOLOGIA
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🛡️  CAMADA 3 - SISTEMA IMUNOLÓGICO${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Deployando 5 serviços de imunologia em paralelo...${NC}"
$KUBECTL apply -f $MANIFESTS/camada-3-imunologia/
echo -e "Aguardando todos os serviços ficarem ready..."
$KUBECTL wait --for=condition=ready pod -l tier=imunologia -n vertice --timeout=300s
echo -e "${GREEN}✅ CAMADA 3 - IMUNOLOGIA COMPLETA${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# VALIDAÇÃO FINAL
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 VALIDAÇÃO FINAL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}Status de todos os pods:${NC}"
$KUBECTL get pods -n vertice
echo ""

echo -e "${YELLOW}Services expostos:${NC}"
$KUBECTL get svc -n vertice
echo ""

# Obter IP externo do API Gateway
echo -e "${YELLOW}🔍 Obtendo IP do API Gateway...${NC}"
GATEWAY_IP=$($KUBECTL get svc api-gateway -n vertice -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "aguardando...")
if [ "$GATEWAY_IP" != "aguardando..." ]; then
    echo -e "${GREEN}✅ API Gateway disponível em: http://$GATEWAY_IP:8000${NC}"
    echo -e "${YELLOW}   Testando health check...${NC}"
    sleep 5
    if curl -f "http://$GATEWAY_IP:8000/health" -m 10 2>/dev/null; then
        echo -e "${GREEN}   ✅ Health check OK!${NC}"
    else
        echo -e "${YELLOW}   ⏳ Health check ainda não disponível (pode levar alguns minutos)${NC}"
    fi
else
    echo -e "${YELLOW}⏳ LoadBalancer ainda provisionando IP externo...${NC}"
    echo -e "   Execute: kubectl get svc api-gateway -n vertice -w${NC}"
fi
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ORGANISMO VÉRTICE ESTÁ VIVO NA NUVEM!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}Comandos úteis:${NC}"
echo -e "  Monitor pods:    kubectl get pods -n vertice -w"
echo -e "  Logs serviço:    kubectl logs -f -l app=<service-name> -n vertice"
echo -e "  Describe pod:    kubectl describe pod <pod-name> -n vertice"
echo -e "  Shell em pod:    kubectl exec -it <pod-name> -n vertice -- /bin/bash"
echo ""
