#!/bin/bash
set -x # Enable debugging
# 🧹 Script Executor de Limpeza do Projeto Vértice
# Data: 2025-10-03
# Executor: Gemini CLI
# Supervisão: Claude Code



# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="/home/juan/vertice-dev"
LEGADO_DIR="$BASE_DIR/LEGADO"
DOCS_DIR="$BASE_DIR/docs"

# Contador de operações
MOVED_COUNT=0
CREATED_COUNT=0
ERROR_COUNT=0

# Função de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((ERROR_COUNT++))
}

# Verificação de segurança
check_safe_path() {
    local path=$1

    # Lista de padrões proibidos
    if [[ "$path" =~ vertice-terminal ]] || \
       [[ "$path" =~ maximus.*service ]] || \
       [[ "$path" =~ hcl_.*service ]] || \
       [[ "$path" =~ rte_service ]] || \
       [[ "$path" =~ \.env ]] || \
       [[ "$path" =~ docker-compose\.yml ]] || \
       [[ "$path" =~ Makefile ]]; then
        return 1
    fi

    return 0
}

# Mover arquivo com segurança
safe_move() {
    local source=$1
    local dest_dir=$2

    if [ ! -f "$source" ]; then
        log_warning "Arquivo não encontrado: $source"
        return 1
    fi

    if ! check_safe_path "$source"; then
        log_error "OPERAÇÃO BLOQUEADA! Tentativa de mover arquivo protegido: $source"
        return 1
    fi

    if [ ! -d "$dest_dir" ]; then
        log_error "Diretório destino não existe: $dest_dir"
        return 1
    fi

    log_info "Movendo: $(basename $source) -> $dest_dir"
    mv "$source" "$dest_dir/" && ((MOVED_COUNT++))
    log_success "Arquivo movido com sucesso"
}

# Criar diretório
create_dir() {
    local dir=$1

    if [ -d "$dir" ]; then
        log_info "Diretório já existe: $dir"
        return 0
    fi

    log_info "Criando diretório: $dir"
    mkdir -p "$dir"
    ((CREATED_COUNT++))
    log_success "Diretório criado"
}

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🧹 LIMPEZA DO PROJETO VÉRTICE - INICIANDO  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# FASE 1: Criar estrutura
echo -e "${BLUE}═══ FASE 1: Criando Estrutura ═══${NC}"

create_dir "$LEGADO_DIR"
create_dir "$LEGADO_DIR/documentacao_antiga"
create_dir "$LEGADO_DIR/codigo_deprecated"
create_dir "$LEGADO_DIR/analises_temporarias"
create_dir "$LEGADO_DIR/scripts_antigos"

create_dir "$DOCS_DIR/00-VISAO-GERAL"
create_dir "$DOCS_DIR/01-ARQUITETURA"
create_dir "$DOCS_DIR/02-MAXIMUS-AI"
create_dir "$DOCS_DIR/03-BACKEND"
create_dir "$DOCS_DIR/04-FRONTEND"
create_dir "$DOCS_DIR/05-TESTES"
create_dir "$DOCS_DIR/06-DEPLOYMENT"
create_dir "$DOCS_DIR/07-RELATORIOS"
create_dir "$DOCS_DIR/08-ROADMAPS"

echo ""

# FASE 2: Mover documentação
echo -e "${BLUE}═══ FASE 2: Organizando Documentação ═══${NC}"

# 00-VISAO-GERAL
safe_move "$BASE_DIR/PROJECT_STATE.md" "$DOCS_DIR/00-VISAO-GERAL" || true

# 01-ARQUITETURA
safe_move "$BASE_DIR/AI_FIRST_ARCHITECTURE.md" "$DOCS_DIR/01-ARQUITETURA" || true
safe_move "$BASE_DIR/VERTICE_CLI_TERMINAL_BLUEPRINT.md" "$DOCS_DIR/01-ARQUITETURA" || true

# 02-MAXIMUS-AI
safe_move "$BASE_DIR/MAXIMUS_AI_ROADMAP_2025_REFACTORED.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/MAXIMUS_AI_2.0_IMPLEMENTATION_COMPLETE.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/MAXIMUS_INTEGRATION_COMPLETE.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/MAXIMUS_INTEGRATION_GUIDE.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/MAXIMUS_DASHBOARD_STATUS.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/MAXIMUS_FRONTEND_IMPLEMENTATION.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/ORACULO_EUREKA_INTEGRATION_VISION.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/REASONING_ENGINE_INTEGRATION.md" "$DOCS_DIR/02-MAXIMUS-AI" || true
safe_move "$BASE_DIR/MEMORY_SYSTEM_IMPLEMENTATION.md" "$DOCS_DIR/02-MAXIMUS-AI" || true

# 03-BACKEND
safe_move "$BASE_DIR/BACKEND_VALIDATION_REPORT.md" "$DOCS_DIR/03-BACKEND" || true
safe_move "$BASE_DIR/REAL_SERVICES_INTEGRATION_REPORT.md" "$DOCS_DIR/03-BACKEND" || true
safe_move "$BASE_DIR/ANALISE_SINESP_SERVICE.md" "$DOCS_DIR/03-BACKEND" || true

# 04-FRONTEND
safe_move "$BASE_DIR/FRONTEND_TEST_REPORT.md" "$DOCS_DIR/04-FRONTEND" || true
safe_move "$BASE_DIR/WORLD_CLASS_TOOLS_FRONTEND_INTEGRATION.md" "$DOCS_DIR/04-FRONTEND" || true

# 05-TESTES
safe_move "$BASE_DIR/FINAL_TESTING_REPORT.md" "$DOCS_DIR/05-TESTES" || true
safe_move "$BASE_DIR/GUIA_DE_TESTES.md" "$DOCS_DIR/05-TESTES" || true
safe_move "$BASE_DIR/TESTE_FERRAMENTAS_COMPLETO.md" "$DOCS_DIR/05-TESTES" || true
safe_move "$BASE_DIR/TEST_MAXIMUS_LOCALLY.md" "$DOCS_DIR/05-TESTES" || true
safe_move "$BASE_DIR/VALIDATION_REPORT.md" "$DOCS_DIR/05-TESTES" || true
safe_move "$BASE_DIR/VALIDACAO_COMPLETA.md" "$DOCS_DIR/05-TESTES" || true
safe_move "$BASE_DIR/CLI_VALIDATION.md" "$DOCS_DIR/05-TESTES" || true

# 06-DEPLOYMENT
safe_move "$BASE_DIR/DOCKER_COMPOSE_FIXES.md" "$DOCS_DIR/06-DEPLOYMENT" || true
safe_move "$BASE_DIR/DEBUG_GUIDE.md" "$DOCS_DIR/06-DEPLOYMENT" || true
safe_move "$BASE_DIR/AURORA_DEPLOYMENT.md" "$DOCS_DIR/06-DEPLOYMENT" || true

# 07-RELATORIOS
safe_move "$BASE_DIR/EXECUTIVE_SUMMARY.md" "$DOCS_DIR/07-RELATORIOS" || true
safe_move "$BASE_DIR/EPIC_COMPLETED.md" "$DOCS_DIR/07-RELATORIOS" || true
safe_move "$BASE_DIR/BUG_FIX_REPORT.md" "$DOCS_DIR/07-RELATORIOS" || true
safe_move "$BASE_DIR/ADR_INTEGRATION_COMPLETE.md" "$DOCS_DIR/07-RELATORIOS" || true
safe_move "$BASE_DIR/FASE_1_ADR_CORE_IMPLEMENTADO.md" "$DOCS_DIR/07-RELATORIOS" || true
safe_move "$BASE_DIR/FASE_3_TOOL_EXPANSION.md" "$DOCS_DIR/07-RELATORIOS" || true

# 08-ROADMAPS
safe_move "$BASE_DIR/RoadMap.md" "$DOCS_DIR/08-ROADMAPS" || true
safe_move "$BASE_DIR/AURORA_2025_STRATEGIC_ROADMAP.md" "$DOCS_DIR/08-ROADMAPS" || true
safe_move "$BASE_DIR/VERTICE_UPGRADE_PLAN.md" "$DOCS_DIR/08-ROADMAPS" || true

echo ""

# FASE 3: Mover para LEGADO
echo -e "${BLUE}═══ FASE 3: Arquivando Documentos Antigos ═══${NC}"

safe_move "$BASE_DIR/MAXIMUS_AI_ROADMAP_2025.md" "$LEGADO_DIR/documentacao_antiga" || true
safe_move "$BASE_DIR/AURORA_2.0_BLUEPRINT_COMPLETE.md" "$LEGADO_DIR/documentacao_antiga" || true
safe_move "$BASE_DIR/AURORA_2.0_MANIFESTO.md" "$LEGADO_DIR/documentacao_antiga" || true
safe_move "$BASE_DIR/AURORA_MASTERPIECE_PLAN.md" "$LEGADO_DIR/documentacao_antiga" || true
safe_move "$BASE_DIR/oraculo_ideias_1758635739.md" "$LEGADO_DIR/documentacao_antiga" || true

echo ""

# FASE 4: Scripts antigos
echo -e "${BLUE}═══ FASE 4: Arquivando Scripts Temporários ═══${NC}"

safe_move "$BASE_DIR/auto_analyzer.py" "$LEGADO_DIR/scripts_antigos" || true

echo ""

# FASE 5: Diretórios de análise
echo -e "${BLUE}═══ FASE 5: Arquivando Análises Temporárias ═══${NC}"

if [ -d "$BASE_DIR/backend_analysis" ]; then
    log_info "Movendo backend_analysis/"
    mv "$BASE_DIR/backend_analysis" "$LEGADO_DIR/analises_temporarias/" && ((MOVED_COUNT++))
fi

if [ -d "$BASE_DIR/frontend_performance_analysis" ]; then
    log_info "Movendo frontend_performance_analysis/"
    mv "$BASE_DIR/frontend_performance_analysis" "$LEGADO_DIR/analises_temporarias/" && ((MOVED_COUNT++))
fi

if [ -d "$BASE_DIR/frontend_security_analysis" ]; then
    log_info "Movendo frontend_security_analysis/"
    mv "$BASE_DIR/frontend_security_analysis" "$LEGADO_DIR/analises_temporarias/" && ((MOVED_COUNT++))
fi

if [ -d "$BASE_DIR/docker_security_analysis" ]; then
    log_info "Movendo docker_security_analysis/"
    mv "$BASE_DIR/docker_security_analysis" "$LEGADO_DIR/analises_temporarias/" && ((MOVED_COUNT++))
fi

echo ""

# FASE 6: Validação
echo -e "${BLUE}═══ FASE 6: Validação de Integridade ═══${NC}"

log_info "Verificando vertice-terminal..."
if [ -d "$BASE_DIR/vertice-terminal" ]; then
    log_success "vertice-terminal está intacto"
else
    log_error "vertice-terminal NÃO ENCONTRADO!"
fi

log_info "Verificando serviços MAXIMUS..."
MAXIMUS_COUNT=$(ls -d $BASE_DIR/backend/services/maximus* 2>/dev/null | wc -l)
log_info "Serviços MAXIMUS encontrados: $MAXIMUS_COUNT (esperado: 7)"

log_info "Verificando serviços HCL..."
HCL_COUNT=$(ls -d $BASE_DIR/backend/services/hcl_* 2>/dev/null | wc -l)
log_info "Serviços HCL encontrados: $HCL_COUNT (esperado: 5)"

log_info "Contando arquivos MD no root..."
MD_ROOT_COUNT=$(find $BASE_DIR -maxdepth 1 -name "*.md" | wc -l)
log_info "Arquivos MD no root: $MD_ROOT_COUNT"

echo ""

# Relatório Final
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🎉 LIMPEZA CONCLUÍDA COM SUCESSO! 🎉     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 ESTATÍSTICAS:${NC}"
echo -e "  📁 Diretórios criados: ${GREEN}$CREATED_COUNT${NC}"
echo -e "  📦 Arquivos/Diretórios movidos: ${GREEN}$MOVED_COUNT${NC}"
echo -e "  ❌ Erros encontrados: ${RED}$ERROR_COUNT${NC}"
echo ""
echo -e "${BLUE}📂 ESTRUTURA CRIADA:${NC}"
echo -e "  ✓ $DOCS_DIR/ (documentação organizada)"
echo -e "  ✓ $LEGADO_DIR/ (arquivos antigos)"
echo ""
echo -e "${YELLOW}⚠️  PRÓXIMOS PASSOS:${NC}"
echo -e "  1. Revisar $DOCS_DIR/"
echo -e "  2. Criar INDEX.md"
echo -e "  3. Criar LEGADO/README.md"
echo -e "  4. Verificar README.md no root"
echo ""
