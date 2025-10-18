#!/bin/bash
set -e

echo "=== FASE 0: Aplicando fixes BLOCKER/CRITICAL ==="

# Backup
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)

# P0-001: Criar rede
if ! docker network ls | grep -q maximus-immunity; then
  echo "Criando rede maximus-immunity-network..."
  docker network create maximus-immunity-network
fi

# P0-002: Fix porta 8151
echo "Fix porta 8151 (maximus-eureka)..."
sed -i '930s/"8151:8036"/"8153:8036"/' docker-compose.yml

# P0-003: Fix porta 5433
echo "Fix porta 5433 (postgres-immunity)..."
sed -i '2377s/"5433:5432"/"5434:5432"/' docker-compose.yml

# P1-001: Fix URLs api_gateway (bloco)
echo "Fix URLs internas (api_gateway)..."
sed -i 's|SINESP_SERVICE_URL=http://sinesp_service:8102|SINESP_SERVICE_URL=http://sinesp_service:80|' docker-compose.yml
sed -i 's|CYBER_SERVICE_URL=http://cyber_service:8103|CYBER_SERVICE_URL=http://cyber_service:80|' docker-compose.yml
sed -i 's|DOMAIN_SERVICE_URL=http://domain_service:8104|DOMAIN_SERVICE_URL=http://domain_service:80|' docker-compose.yml
sed -i 's|IP_INTELLIGENCE_SERVICE_URL=http://ip_intelligence_service:8105|IP_INTELLIGENCE_SERVICE_URL=http://ip_intelligence_service:80|' docker-compose.yml
sed -i 's|NMAP_SERVICE_URL=http://nmap_service:8106|NMAP_SERVICE_URL=http://nmap_service:80|' docker-compose.yml
sed -i 's|OSINT_SERVICE_URL=http://osint_service:8007|OSINT_SERVICE_URL=http://osint-service:8007|' docker-compose.yml
sed -i 's|GOOGLE_OSINT_SERVICE_URL=http://google_osint_service:8101|GOOGLE_OSINT_SERVICE_URL=http://google_osint_service:8031|' docker-compose.yml
sed -i 's|MAXIMUS_PREDICT_URL=http://maximus_predict:8126|MAXIMUS_PREDICT_URL=http://maximus_predict:80|' docker-compose.yml
sed -i 's|ATLAS_SERVICE_URL=http://atlas_service:8109|ATLAS_SERVICE_URL=http://atlas_service:8000|' docker-compose.yml
sed -i 's|AUTH_SERVICE_URL=http://auth_service:8110|AUTH_SERVICE_URL=http://auth_service:80|' docker-compose.yml
sed -i 's|VULN_SCANNER_SERVICE_URL=http://vuln_scanner_service:8111|VULN_SCANNER_SERVICE_URL=http://vuln_scanner_service:80|' docker-compose.yml
sed -i 's|SOCIAL_ENG_SERVICE_URL=http://social_eng_service:8112|SOCIAL_ENG_SERVICE_URL=http://social_eng_service:80|' docker-compose.yml
sed -i 's|THREAT_INTEL_SERVICE_URL=http://threat_intel_service:8113|THREAT_INTEL_SERVICE_URL=http://threat_intel_service:8013|' docker-compose.yml
sed -i 's|MALWARE_ANALYSIS_SERVICE_URL=http://malware_analysis_service:8114|MALWARE_ANALYSIS_SERVICE_URL=http://malware_analysis_service:8014|' docker-compose.yml
sed -i 's|SSL_MONITOR_SERVICE_URL=http://ssl_monitor_service:8115|SSL_MONITOR_SERVICE_URL=http://ssl_monitor_service:8015|' docker-compose.yml
sed -i 's|MAXIMUS_CORE_SERVICE_URL=http://maximus_core_service:8150|MAXIMUS_CORE_SERVICE_URL=http://maximus_core_service:8100|' docker-compose.yml

echo "✅ Fixes aplicados com sucesso!"
echo ""
echo "Validação:"
echo "- Porta 8151: $(grep -c '"8151:' docker-compose.yml) ocorrência(s) (esperado: 1)"
echo "- Porta 5433: $(grep -c '"5433:' docker-compose.yml) ocorrência(s) (esperado: 1)"
echo "- Rede: $(docker network ls | grep maximus-immunity | wc -l) rede(s) (esperado: 1)"
