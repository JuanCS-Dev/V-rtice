#!/bin/bash
# Fix port mismatches no docker-compose.yml
# Remove healthcheck overrides incorretos e corrige port mappings

COMPOSE_FILE="/home/juan/vertice-dev/docker-compose.yml"
BACKUP_FILE="${COMPOSE_FILE}.backup_port_fix_$(date +%Y%m%d_%H%M%S)"

# Backup
cp "$COMPOSE_FILE" "$BACKUP_FILE"
echo "✅ Backup criado: $BACKUP_FILE"

# Fix bas_service: 8536:8036 → 8536:8008
sed -i 's|"8536:8036"|"8536:8008"|g' "$COMPOSE_FILE"

# Fix c2_orchestration_service: 8535:8035 → 8535:8009
sed -i 's|"8535:8035"|"8535:8009"|g' "$COMPOSE_FILE"

# Fix network_monitor_service: 8120:80 → 8120:8044
sed -i 's|"8120:80"|"8120:8044"|g' "$COMPOSE_FILE"

# Fix maximus_predict: 8126:80 → 8126:8040
sed -i '/maximus_predict:/,/restart:/ s|"8126:80"|"8126:8040"|g' "$COMPOSE_FILE"

# Fix narrative_analysis_service: 8015:8015 → 8015:8042
sed -i '/narrative_analysis_service:/,/restart:/ s|"8015:8015"|"8015:8042"|g' "$COMPOSE_FILE"

# Fix predictive_threat_hunting_service: 8016:8016 → 8016:8050
sed -i '/predictive_threat_hunting_service:/,/restart:/ s|"8016:8016"|"8016:8050"|g' "$COMPOSE_FILE"

echo "✅ Port mappings corrigidos"
echo ""
echo "Serviços corrigidos:"
echo "  - bas_service: 8536:8036 → 8536:8008"
echo "  - c2_orchestration_service: 8535:8035 → 8535:8009"
echo "  - network_monitor_service: 8120:80 → 8120:8044"
echo "  - maximus_predict: 8126:80 → 8126:8040"
echo "  - narrative_analysis_service: 8015:8015 → 8015:8042"
echo "  - predictive_threat_hunting_service: 8016:8016 → 8016:8050"
