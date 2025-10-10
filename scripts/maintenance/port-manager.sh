#!/bin/bash

###############################################################################
# PORT MANAGER - Solução Definitiva para Conflitos de Porta
###############################################################################
#
# Funcionalidades:
# 1. Detecta portas em uso
# 2. Libera portas automaticamente
# 3. Valida disponibilidade antes de subir serviços
# 4. Gera relatório de portas
# 5. Modo interativo e automático
#
# Uso:
#   ./port-manager.sh check        # Verifica conflitos
#   ./port-manager.sh free         # Libera portas automaticamente
#   ./port-manager.sh report       # Gera relatório
#   ./port-manager.sh start        # Inicia serviços com validação
#
###############################################################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║        VÉRTICE - PORT MANAGER v1.0                         ║"
    echo "║        Gerenciador Inteligente de Portas                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Lista de portas críticas do Vértice
CRITICAL_PORTS=(
    "8099:API Gateway"
    "8001:Maximus Core"
    "8016:Maximus Orchestrator"
    "8008:Maximus Predict"
    "8010:ADR Core"
    "6379:Redis"
    "5432:PostgreSQL"
    "6333:Qdrant"
    "9090:Prometheus"
    "3000:Grafana"
    "8032:Network Recon"
    "8033:Vuln Intel"
    "8034:Web Attack"
    "8035:C2 Orchestration"
    "8036:BAS"
    "8037:Offensive Gateway"
    "8000:IP Intelligence"
    "8002:OSINT Service"
    "8003:Google OSINT"
    "8004:SINESP"
    "8005:Immunis API"
    "8006:Nmap Service"
    "8007:Domain Service"
    "8009:Social Engineering"
    "8011:Malware Analysis"
    "8012:SSL Monitor"
    "8013:Threat Intel"
    "8020:HCL Analyzer"
    "8021:HCL Executor"
    "8022:HCL KB"
    "8023:HCL Monitor"
    "8024:HCL Planner"
    "8200:EUREKA"
    "8201:ORÁCULO"
    "8202:PREDICT"
)

# Verifica se porta está em uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || \
       ss -tlnp 2>/dev/null | grep -q ":$port "; then
        return 0  # Porta em uso
    else
        return 1  # Porta livre
    fi
}

# Obtém processo usando porta
get_process_using_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null | head -1)

    if [ -n "$pid" ]; then
        local process=$(ps -p $pid -o comm= 2>/dev/null)
        local cmd=$(ps -p $pid -o args= 2>/dev/null | cut -c1-50)
        echo "$pid|$process|$cmd"
    else
        # Tenta com ss
        ss -tlnp 2>/dev/null | grep ":$port " | awk -F'users:' '{print $2}' | head -1
    fi
}

# Verifica todas as portas críticas
check_all_ports() {
    banner
    echo -e "${BLUE}🔍 Verificando portas críticas...${NC}\n"

    local conflicts=0
    local free=0

    for entry in "${CRITICAL_PORTS[@]}"; do
        IFS=':' read -r port service <<< "$entry"

        if check_port "$port"; then
            conflicts=$((conflicts + 1))
            local process_info=$(get_process_using_port "$port")
            echo -e "${RED}❌ CONFLITO${NC} - Porta $port ($service) em uso"
            echo -e "   ${YELLOW}Processo: $process_info${NC}"
        else
            free=$((free + 1))
            echo -e "${GREEN}✅ LIVRE${NC}   - Porta $port ($service)"
        fi
    done

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Total: ${GREEN}$free livres${NC} | ${RED}$conflicts conflitos${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $conflicts
}

# Libera porta automaticamente
free_port() {
    local port=$1
    local service=$2
    local force=${3:-false}

    if ! check_port "$port"; then
        echo -e "${GREEN}✓${NC} Porta $port já está livre"
        return 0
    fi

    local pid=$(lsof -ti:$port 2>/dev/null | head -1)

    if [ -z "$pid" ]; then
        echo -e "${YELLOW}⚠${NC} Não foi possível identificar processo na porta $port"
        return 1
    fi

    local process=$(ps -p $pid -o comm= 2>/dev/null)

    if [ "$force" = true ]; then
        echo -e "${YELLOW}🔨 Liberando porta $port ($service)...${NC}"
        kill -9 $pid 2>/dev/null
        sleep 0.5

        if ! check_port "$port"; then
            echo -e "${GREEN}✓${NC} Porta $port liberada com sucesso"
            return 0
        else
            echo -e "${RED}✗${NC} Falha ao liberar porta $port"
            return 1
        fi
    else
        echo -e "${YELLOW}?${NC} Porta $port em uso por PID $pid ($process)"
        echo -e "   Use: ${CYAN}./port-manager.sh free${NC} para liberar automaticamente"
        return 1
    fi
}

# Libera todas as portas em conflito
free_all_ports() {
    banner
    echo -e "${YELLOW}🔨 Modo: LIBERAR PORTAS AUTOMATICAMENTE${NC}\n"

    read -p "⚠️  Isso vai MATAR processos usando portas do Vértice. Continuar? (s/N): " confirm

    if [[ ! "$confirm" =~ ^[Ss]$ ]]; then
        echo -e "${BLUE}ℹ${NC} Operação cancelada pelo usuário"
        exit 0
    fi

    echo ""
    local freed=0

    for entry in "${CRITICAL_PORTS[@]}"; do
        IFS=':' read -r port service <<< "$entry"

        if check_port "$port"; then
            if free_port "$port" "$service" true; then
                freed=$((freed + 1))
            fi
        fi
    done

    echo ""
    echo -e "${GREEN}✓${NC} $freed portas liberadas"
}

# Gera relatório detalhado
generate_report() {
    banner
    echo -e "${BLUE}📊 Gerando relatório de portas...${NC}\n"

    local report_file="port-report-$(date +%Y%m%d-%H%M%S).txt"

    {
        echo "═══════════════════════════════════════════════════════════"
        echo "  VÉRTICE - RELATÓRIO DE PORTAS"
        echo "  Gerado em: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "═══════════════════════════════════════════════════════════"
        echo ""

        for entry in "${CRITICAL_PORTS[@]}"; do
            IFS=':' read -r port service <<< "$entry"

            if check_port "$port"; then
                echo "[OCUPADA] Porta $port - $service"
                local process_info=$(get_process_using_port "$port")
                echo "          Processo: $process_info"
            else
                echo "[LIVRE]   Porta $port - $service"
            fi
        done

        echo ""
        echo "═══════════════════════════════════════════════════════════"

        # Docker containers
        echo ""
        echo "CONTAINERS DOCKER ATIVOS:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker não disponível"

    } > "$report_file"

    cat "$report_file"
    echo ""
    echo -e "${GREEN}✓${NC} Relatório salvo em: ${CYAN}$report_file${NC}"
}

# Inicia serviços com validação
start_services() {
    banner
    echo -e "${BLUE}🚀 Iniciando serviços com validação de portas...${NC}\n"

    # Primeiro verifica conflitos
    echo "Passo 1: Verificando conflitos..."
    check_all_ports
    local conflicts=$?

    if [ $conflicts -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Conflitos detectados!${NC}"
        read -p "Deseja liberar automaticamente? (s/N): " confirm

        if [[ "$confirm" =~ ^[Ss]$ ]]; then
            free_all_ports
        else
            echo -e "${RED}✗${NC} Não é possível iniciar com portas em conflito"
            exit 1
        fi
    fi

    echo ""
    echo "Passo 2: Iniciando serviços Docker..."

    # Para containers existentes
    echo "  → Parando containers existentes..."
    docker compose down 2>/dev/null || true

    # Inicia serviços
    echo "  → Iniciando serviços..."
    docker compose up -d

    # Aguarda inicialização
    echo "  → Aguardando inicialização (30s)..."
    sleep 30

    echo ""
    echo -e "${GREEN}✓${NC} Serviços iniciados!"
    echo ""
    docker compose ps
}

# Health check de serviços críticos
health_check() {
    banner
    echo -e "${BLUE}🏥 Health Check dos Serviços Críticos...${NC}\n"

    local services=(
        "http://localhost:8099/health:API Gateway"
        "http://localhost:8001/health:Maximus Core"
        "http://localhost:8016/health:Maximus Orchestrator"
    )

    for entry in "${services[@]}"; do
        IFS=':' read -r url service <<< "$entry"

        echo -n "Verificando $service... "

        if curl -s -f -m 5 "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ OK${NC}"
        else
            echo -e "${RED}✗ FALHOU${NC}"
        fi
    done
}

# Menu principal
show_menu() {
    banner
    echo -e "${CYAN}Escolha uma opção:${NC}\n"
    echo "  1) 🔍 Verificar portas em conflito"
    echo "  2) 🔨 Liberar portas automaticamente"
    echo "  3) 📊 Gerar relatório detalhado"
    echo "  4) 🚀 Iniciar serviços (com validação)"
    echo "  5) 🏥 Health check dos serviços"
    echo "  6) 🚪 Sair"
    echo ""
    read -p "Opção: " choice

    case $choice in
        1) check_all_ports ;;
        2) free_all_ports ;;
        3) generate_report ;;
        4) start_services ;;
        5) health_check ;;
        6) exit 0 ;;
        *) echo -e "${RED}Opção inválida${NC}" ;;
    esac
}

# Main
main() {
    case "${1:-menu}" in
        check)
            check_all_ports
            ;;
        free)
            free_all_ports
            ;;
        report)
            generate_report
            ;;
        start)
            start_services
            ;;
        health)
            health_check
            ;;
        menu|*)
            while true; do
                show_menu
                echo ""
                read -p "Pressione ENTER para continuar..."
                clear
            done
            ;;
    esac
}

main "$@"
