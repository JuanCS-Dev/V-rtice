#!/bin/bash
# 🔍 Port Mapping Audit Script
# Detecta mismatches entre docker-compose.yml e Dockerfiles
#
# Uso: ./audit_ports.sh
# Output: audit_report_TIMESTAMP.csv

set -euo pipefail

COMPOSE_FILE="/home/juan/vertice-dev/docker-compose.yml"
SERVICES_DIR="/home/juan/vertice-dev/backend/services"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="/home/juan/vertice-dev/docs/backend/diagnosticos/port_audit_${TIMESTAMP}.csv"

echo "🔍 Iniciando auditoria de port mappings..."
echo ""

# Header CSV
echo "service_name,compose_external,compose_internal,dockerfile_expose,dockerfile_cmd_port,mismatch,status" > "$REPORT_FILE"

# Lista de serviços do Active Immune System
SERVICES=(
    "adaptive_immunity_service"
    "memory_consolidation_service"
    "immunis_treg_service"
    "immunis_macrophage_service"
    "immunis_neutrophil_service"
    "immunis_bcell_service"
    "immunis_dendritic_service"
    "immunis_nk_cell_service"
    "immunis_helper_t_service"
    "immunis_cytotoxic_t_service"
    "active_immune_core"
)

for service in "${SERVICES[@]}"; do
    echo "📦 Analisando: $service"

    # Extrair port mapping do docker-compose
    compose_ports=$(grep -A 30 "${service}:" "$COMPOSE_FILE" | grep -m 1 "^\s*-\s*[0-9]" | tr -d ' -' || echo "")

    if [ -z "$compose_ports" ]; then
        compose_external="N/A"
        compose_internal="N/A"
    else
        compose_external=$(echo "$compose_ports" | cut -d: -f1)
        compose_internal=$(echo "$compose_ports" | cut -d: -f2)
    fi

    # Encontrar Dockerfile
    dockerfile="${SERVICES_DIR}/${service}/Dockerfile"

    if [ ! -f "$dockerfile" ]; then
        echo "  ⚠️  Dockerfile não encontrado"
        echo "${service},${compose_external},${compose_internal},NOT_FOUND,NOT_FOUND,UNKNOWN,⚠️" >> "$REPORT_FILE"
        continue
    fi

    # Extrair EXPOSE do Dockerfile
    dockerfile_expose=$(grep "^EXPOSE" "$dockerfile" | awk '{print $2}' || echo "N/A")

    # Extrair porta do CMD (uvicorn --port ou python run.py com port=)
    dockerfile_cmd_port=$(grep -E "CMD.*--port|port=" "$dockerfile" | grep -oP '(--port\s+\K\d+|port=\K\d+)' | head -1 || echo "N/A")

    # Se não encontrou no CMD, tentar no run.py ou main.py
    if [ "$dockerfile_cmd_port" = "N/A" ]; then
        run_file="${SERVICES_DIR}/${service}/run.py"
        if [ -f "$run_file" ]; then
            dockerfile_cmd_port=$(grep -oP 'port=\K\d+' "$run_file" | head -1 || echo "N/A")
        fi
    fi

    # Detectar mismatch
    mismatch="NO"
    status="✅"

    if [ "$compose_internal" != "N/A" ] && [ "$dockerfile_expose" != "N/A" ]; then
        if [ "$compose_internal" != "$dockerfile_expose" ]; then
            mismatch="YES"
            status="❌"
        fi
    fi

    if [ "$compose_internal" != "N/A" ] && [ "$dockerfile_cmd_port" != "N/A" ]; then
        if [ "$compose_internal" != "$dockerfile_cmd_port" ]; then
            mismatch="YES"
            status="❌"
        fi
    fi

    # Adicionar ao CSV
    echo "${service},${compose_external},${compose_internal},${dockerfile_expose},${dockerfile_cmd_port},${mismatch},${status}" >> "$REPORT_FILE"

    # Output colorido
    if [ "$mismatch" = "YES" ]; then
        echo "  ❌ MISMATCH: compose=${compose_internal} dockerfile=${dockerfile_expose}/${dockerfile_cmd_port}"
    else
        echo "  ✅ OK: todas as portas alinham (${compose_internal})"
    fi
done

echo ""
echo "✅ Auditoria completa!"
echo "📄 Relatório salvo em: $REPORT_FILE"
echo ""
echo "📊 Resumo:"
total=$(( ${#SERVICES[@]} ))
mismatches=$(grep -c "YES" "$REPORT_FILE" || echo "0")
ok=$(( total - mismatches ))

echo "  Total de serviços: $total"
echo "  ✅ OK: $ok"
echo "  ❌ Mismatches: $mismatches"

if [ "$mismatches" -gt 0 ]; then
    echo ""
    echo "🔥 Serviços com mismatch:"
    grep "YES" "$REPORT_FILE" | cut -d, -f1 | while read svc; do
        echo "  - $svc"
    done
fi
