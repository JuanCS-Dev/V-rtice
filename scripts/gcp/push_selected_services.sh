#!/bin/bash
set -e

# 🧬 FASE 3: Build e Push das Imagens do Sistema Nervoso Central
# Builds e publica os 12 serviços customizados no Artifact Registry

# Configurações
PROJECT_ID="projeto-vertice"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/$PROJECT_ID/vertice-images"

# Array dos 12 serviços customizados (postgres/redis/kafka são imagens oficiais)
SERVICES=(
    # CAMADA 1 - Fundação
    "api_gateway"
    "auth_service"

    # CAMADA 2 - Consciência
    "maximus_core_service"
    "maximus_orchestrator_service"
    "maximus_eureka"
    "maximus_oraculo"
    "maximus_predict"

    # CAMADA 3 - Imunologia
    "immunis_api_service"
    "active_immune_core"
    "adaptive_immune_system"
    "ai_immune_system"
    "reflex_triage_engine"
)

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧬 INICIANDO BUILD DO DNA DO VÉRTICE${NC}"
echo "Registry: $REGISTRY"
echo "Total de serviços customizados: ${#SERVICES[@]}"
echo ""

# Contador
TOTAL=${#SERVICES[@]}
CURRENT=0
FAILED=()

# Build e Push de cada serviço
for SERVICE in "${SERVICES[@]}"; do
    CURRENT=$((CURRENT + 1))

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🧬 [$CURRENT/$TOTAL] Processando: $SERVICE${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    SERVICE_DIR="backend/services/$SERVICE"
    IMAGE_TAG="$REGISTRY/$SERVICE:latest"

    # Verifica se o diretório existe
    if [ ! -d "$SERVICE_DIR" ]; then
        echo -e "${RED}❌ Diretório não encontrado: $SERVICE_DIR${NC}"
        FAILED+=("$SERVICE")
        continue
    fi

    # Verifica se o Dockerfile existe
    if [ ! -f "$SERVICE_DIR/Dockerfile" ]; then
        echo -e "${RED}❌ Dockerfile não encontrado: $SERVICE_DIR/Dockerfile${NC}"
        FAILED+=("$SERVICE")
        continue
    fi

    echo "📦 Building image: $IMAGE_TAG"

    # Build da imagem
    if docker build -t "$IMAGE_TAG" "$SERVICE_DIR"; then
        echo -e "${GREEN}✅ Build concluído: $SERVICE${NC}"

        echo "📤 Pushing to registry..."

        # Push para registry
        if docker push "$IMAGE_TAG"; then
            echo -e "${GREEN}✅ Push concluído: $SERVICE${NC}"
        else
            echo -e "${RED}❌ Falha no push: $SERVICE${NC}"
            FAILED+=("$SERVICE")
        fi
    else
        echo -e "${RED}❌ Falha no build: $SERVICE${NC}"
        FAILED+=("$SERVICE")
    fi

    echo ""
done

# Sumário
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 SUMÁRIO DO BUILD${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Total processados: $TOTAL"
echo "Sucesso: $((TOTAL - ${#FAILED[@]}))"
echo "Falhas: ${#FAILED[@]}"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Serviços que falharam:${NC}"
    for FAILED_SERVICE in "${FAILED[@]}"; do
        echo "  - $FAILED_SERVICE"
    done
    exit 1
else
    echo ""
    echo -e "${GREEN}✅ TODOS OS SERVIÇOS FORAM PUBLICADOS COM SUCESSO!${NC}"
    echo -e "${GREEN}🧬 O DNA do Vértice está pronto para deployment${NC}"
fi
