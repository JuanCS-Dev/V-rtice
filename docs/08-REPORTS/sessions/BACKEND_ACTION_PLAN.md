# PLANO DE AÇÃO - BACKEND VÉRTICE

**Versão:** 1.0  
**Data:** 2025-10-18  
**Objetivo:** Deixar backend operacional (status UP)  
**Tempo estimado:** 1-2 horas

---

## P0 - BLOCKERS (executar AGORA - 15 min)

### ✅ AÇÃO 1: Criar rede Docker externa
**Comando:**
```bash
docker network create maximus-immunity-network
```

**Validação:**
```bash
docker network ls | grep maximus-immunity
```

**Alternativa:** Se não precisar isolar a rede, editar docker-compose.yml:
```bash
sed -i '2642s/external: true/driver: bridge/' docker-compose.yml
```

---

### ✅ AÇÃO 2: Resolver conflito de porta 8151
**Arquivo:** docker-compose.yml (linha 930)

**Comando:**
```bash
# Backup
cp docker-compose.yml docker-compose.yml.backup

# Fix
sed -i '930s/"8151:8036"/"8153:8036"/' docker-compose.yml
```

**Validação:**
```bash
grep '"8151:' docker-compose.yml | wc -l  # Deve retornar 1
grep '"8153:8036"' docker-compose.yml     # Deve retornar a linha do maximus-eureka
```

---

### ✅ AÇÃO 3: Resolver conflito de porta 5433
**Arquivo:** docker-compose.yml (linha 2377)

**Comando:**
```bash
sed -i '2377s/"5433:5432"/"5434:5432"/' docker-compose.yml
```

**Validação:**
```bash
grep '"5433:' docker-compose.yml | wc -l  # Deve retornar 1
grep '"5434:5432"' docker-compose.yml     # Deve retornar a linha do postgres-immunity
```

---

## P1 - CRITICAL (executar em sequência - 30 min)

### ✅ AÇÃO 4: Corrigir URLs internas no api_gateway
**Arquivo:** docker-compose.yml (linhas ~10-50, seção api_gateway environment)

**Lista de mudanças necessárias:**
```bash
# Aplicar em bloco (uso de sed multi-line ou editor)
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
```

**Validação:**
```bash
grep 'SERVICE_URL=http://[a-z_-]*:8[0-9][0-9][0-9]' docker-compose.yml | grep -v localhost | head -10
# Deve retornar apenas URLs corretas (portas do container)
```

---

### ✅ AÇÃO 5: Corrigir URLs no maximus_core_service
**Arquivo:** docker-compose.yml (seção maximus_core_service environment)

**Comandos:**
```bash
# Localizar bloco do maximus_core_service (linha ~580-620)
sed -i '/maximus_core_service:/,/networks:/ {
  s|THREAT_INTEL_SERVICE_URL=http://threat_intel_service:8113|THREAT_INTEL_SERVICE_URL=http://threat_intel_service:8013|
  s|MALWARE_ANALYSIS_SERVICE_URL=http://malware_analysis_service:8114|MALWARE_ANALYSIS_SERVICE_URL=http://malware_analysis_service:8014|
  s|SSL_MONITOR_SERVICE_URL=http://ssl_monitor_service:8115|SSL_MONITOR_SERVICE_URL=http://ssl_monitor_service:8015|
  s|IP_INTEL_SERVICE_URL=http://ip_intelligence_service:8105|IP_INTEL_SERVICE_URL=http://ip_intelligence_service:80|
  s|NMAP_SERVICE_URL=http://nmap_service:8106|NMAP_SERVICE_URL=http://nmap_service:80|
  s|VULN_SCANNER_SERVICE_URL=http://vuln_scanner_service:8111|VULN_SCANNER_SERVICE_URL=http://vuln_scanner_service:80|
  s|DOMAIN_SERVICE_URL=http://domain_service:8104|DOMAIN_SERVICE_URL=http://domain_service:80|
  s|MAXIMUS_PREDICT_URL=http://maximus_predict:8126|MAXIMUS_PREDICT_URL=http://maximus_predict:80|
  s|OSINT_SERVICE_URL=http://osint-service:8100|OSINT_SERVICE_URL=http://osint-service:8007|
}' docker-compose.yml
```

**Nota:** Se sed complexo falhar, editar manualmente estas linhas no bloco `maximus_core_service` (aproximadamente linhas 590-610).

---

### ✅ AÇÃO 6: Corrigir referências a aurora_predict (deprecated)
**Arquivo:** backend/api_gateway/main.py

**Linha ~138:**
```bash
sed -i 's|AURORA_PREDICT_URL|MAXIMUS_PREDICT_URL|g' backend/api_gateway/main.py
```

**Validação:**
```bash
grep -n "AURORA_PREDICT" backend/api_gateway/main.py  # Não deve retornar nada
grep -n "MAXIMUS_PREDICT" backend/api_gateway/main.py # Deve retornar linhas atualizadas
```

---

## P2 - MAJOR (executar após P0/P1 - backlog)

### ⏳ AÇÃO 7: Adicionar healthchecks aos serviços core
**Prioridade:** api_gateway, sinesp_service, domain_service, ip_intelligence_service, nmap_service

**Template:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:80/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Ação:** Adicionar manualmente ao docker-compose.yml nos serviços que não têm.

---

### ⏳ AÇÃO 8: Validar Dockerfiles ausentes
**Comando:**
```bash
# Listar serviços sem Dockerfile
comm -23 \
  <(grep -oP '^  [a-z_-]+:' docker-compose.yml | sed 's/://g' | sort) \
  <(find backend/services -name Dockerfile -printf '%h\n' | xargs -n1 basename | sort)
```

**Ação:** Para cada serviço listado, verificar se:
1. Usa `image:` em vez de `build:` (OK, não precisa de Dockerfile)
2. Precisa de Dockerfile mas está faltando (criar ou marcar como TODO)

---

## EXECUÇÃO EM FASES

### FASE 0 - Aplicar fixes (15 min)

```bash
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
```

**Salvar como:** `backend/scripts/apply_critical_fixes.sh`

---

### FASE 1 - Subir Tier 0 (10 min)

```bash
#!/bin/bash
set -e

echo "=== FASE 1: Subindo Tier 0 (Infra) ==="

docker compose up -d redis postgres qdrant

echo "Aguardando 30s para inicialização..."
sleep 30

echo "Status Tier 0:"
docker compose ps redis postgres qdrant

echo ""
echo "Healthcheck:"
docker compose ps --filter "name=redis" --filter "status=running" | grep -q "Up" && echo "✅ Redis UP" || echo "❌ Redis DOWN"
docker compose ps --filter "name=postgres" --filter "status=running" | grep -q "Up" && echo "✅ Postgres UP" || echo "❌ Postgres DOWN"
docker compose ps --filter "name=qdrant" --filter "status=running" | grep -q "Up" && echo "✅ Qdrant UP" || echo "❌ Qdrant DOWN"
```

**Salvar como:** `backend/scripts/start_tier0.sh`

---

### FASE 2 - Subir Tier 1 (20 min)

```bash
#!/bin/bash
set -e

echo "=== FASE 2: Subindo Tier 1 (Core Services) ==="

docker compose up -d \
  api_gateway \
  sinesp_service \
  domain_service \
  ip_intelligence_service \
  nmap_service \
  auth_service

echo "Aguardando 60s para inicialização..."
sleep 60

echo "Status Tier 1:"
docker compose ps api_gateway sinesp_service domain_service ip_intelligence_service nmap_service auth_service

echo ""
echo "Healthcheck API Gateway:"
if curl -sf http://localhost:8000/health > /dev/null; then
  echo "✅ API Gateway HEALTHY"
  curl -s http://localhost:8000/health | jq .
else
  echo "❌ API Gateway UNHEALTHY"
  docker compose logs --tail=50 api_gateway
fi
```

**Salvar como:** `backend/scripts/start_tier1.sh`

---

### FASE 3 - Subir Tier 2+ (30 min)

```bash
#!/bin/bash
set -e

echo "=== FASE 3: Subindo Tier 2 (AI Services) ==="

docker compose up -d \
  threat_intel_service \
  malware_analysis_service \
  ssl_monitor_service \
  osint-service \
  maximus_predict

echo "Aguardando 60s..."
sleep 60

echo "=== Subindo MAXIMUS Core ==="
docker compose up -d maximus_core_service

echo "Aguardando 120s (LLM loading)..."
sleep 120

docker compose ps maximus_core_service

echo ""
echo "Healthcheck MAXIMUS Core:"
if curl -sf http://localhost:8100/health > /dev/null; then
  echo "✅ MAXIMUS Core HEALTHY"
else
  echo "⚠️ MAXIMUS Core UNHEALTHY (verificar logs)"
  docker compose logs --tail=100 maximus_core_service
fi
```

**Salvar como:** `backend/scripts/start_tier2.sh`

---

## VALIDAÇÃO FINAL

### Script de health check completo

```bash
#!/bin/bash
# backend/scripts/health_check_all.sh

echo "=== BACKEND HEALTH CHECK COMPLETO ==="
echo ""

SERVICES=(
  "redis:6379:ping"
  "postgres:5432:pg_isready"
  "api_gateway:8000:/health"
  "sinesp_service:8102:/"
  "domain_service:8104:/"
  "ip_intelligence_service:8105:/"
  "nmap_service:8106:/"
  "threat_intel_service:8113:/health"
  "maximus_core_service:8150:/health"
)

total=0
healthy=0

for entry in "${SERVICES[@]}"; do
  IFS=':' read -r service port endpoint <<< "$entry"
  total=$((total + 1))
  
  printf "%-30s " "$service"
  
  if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
    if [ "$endpoint" = "ping" ]; then
      docker compose exec -T redis redis-cli ping > /dev/null 2>&1 && status="✅ HEALTHY" || status="❌ UNHEALTHY"
    elif [ "$endpoint" = "pg_isready" ]; then
      docker compose exec -T postgres pg_isready > /dev/null 2>&1 && status="✅ HEALTHY" || status="❌ UNHEALTHY"
    else
      curl -sf "http://localhost:$port$endpoint" > /dev/null 2>&1 && status="✅ HEALTHY" || status="⚠️ DEGRADED"
    fi
    
    [[ "$status" == *"HEALTHY"* ]] && healthy=$((healthy + 1))
  else
    status="❌ DOWN"
  fi
  
  echo "$status"
done

echo ""
echo "========================================="
echo "TOTAL: $healthy/$total serviços HEALTHY"
echo "========================================="

if [ $healthy -ge $((total * 90 / 100)) ]; then
  echo "✅ BACKEND OPERACIONAL (≥90% UP)"
  exit 0
else
  echo "❌ BACKEND COM PROBLEMAS (<90% UP)"
  exit 1
fi
```

**Salvar como:** `backend/scripts/health_check_all.sh`

---

## COMANDOS RÁPIDOS

### Aplicar todos os fixes de uma vez
```bash
cd /home/juan/vertice-dev
bash backend/scripts/apply_critical_fixes.sh
```

### Subir backend completo
```bash
cd /home/juan/vertice-dev
bash backend/scripts/start_tier0.sh && \
bash backend/scripts/start_tier1.sh && \
bash backend/scripts/start_tier2.sh
```

### Validar health
```bash
cd /home/juan/vertice-dev
bash backend/scripts/health_check_all.sh
```

### Rollback (se necessário)
```bash
cd /home/juan/vertice-dev
cp docker-compose.yml.backup.YYYYMMDD_HHMMSS docker-compose.yml
docker compose down
docker compose up -d
```

---

## CHECKLIST DE EXECUÇÃO

- [ ] **P0-001:** Rede maximus-immunity-network criada
- [ ] **P0-002:** Porta 8151 conflito resolvido
- [ ] **P0-003:** Porta 5433 conflito resolvido
- [ ] **P1-001:** URLs api_gateway corrigidas (15 URLs)
- [ ] **P1-002:** URLs maximus_core_service corrigidas
- [ ] **P1-003:** Referências aurora_predict → maximus_predict
- [ ] **Tier 0:** Redis + Postgres + Qdrant UP
- [ ] **Tier 1:** API Gateway respondendo
- [ ] **Tier 2:** MAXIMUS Core operacional
- [ ] **Smoke test:** ≥90% serviços UP

---

## TEMPO ESTIMADO TOTAL

- **P0 Fixes:** 15 min
- **P1 Fixes:** 30 min
- **Tier 0 Up:** 10 min
- **Tier 1 Up:** 20 min
- **Tier 2 Up:** 30 min
- **Validação:** 10 min

**TOTAL:** ~2 horas (incluindo troubleshooting)

---

## PRÓXIMOS PASSOS (PÓS-UP)

1. Adicionar healthchecks aos serviços sem (P2)
2. Implementar smoke tests automatizados
3. Configurar CI/CD para validar compose antes de commit
4. Documentar topologia de serviços
5. Migrar secrets para .env (GEMINI_API_KEY, etc)

---

**Status:** ⏳ PRONTO PARA EXECUÇÃO  
**Próximo relatório:** BACKEND_FIX_EXECUTION_REPORT.md
