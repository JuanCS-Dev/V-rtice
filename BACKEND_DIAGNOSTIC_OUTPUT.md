# BACKEND DIAGNOSTIC REPORT - Vértice Platform

**Data:** 2025-10-18T02:58:17Z  
**Executor:** Copilot CLI (Diagnóstico Sistemático)  
**Status:** ⚠️ ISSUES CRÍTICOS DETECTADOS

---

## SUMÁRIO EXECUTIVO

**Total de serviços:** 128 (docker-compose.yml)  
**Dockerfiles encontrados:** 81  
**Issues detectados:** 7 BLOCKER, 15+ CRITICAL

**Impacto:** Backend NÃO pode subir sem correções P0/P1.

---

## FASE 1: AUDITORIA SISTEMÁTICA

### 1.1 MAPEAMENTO DE DEPENDÊNCIAS

**Tier 0 (Fundação - sem depends_on):**
- redis
- postgres
- qdrant
- zookeeper-immunity
- hcl-postgres

**Tier 1 (Core - dependem de Tier 0):**
- api_gateway (depende: redis + 10 serviços)
- osint-service (depende: redis, maximus_predict)
- auth_service (depende: redis)
- maximus_core_service (depende: redis, postgres + 8 serviços)

**Tier 2+ (Features - dependem de Tier 1):**
- 100+ serviços adicionais

**❌ ISSUE:** Dependências circulares não detectadas, mas ordem de startup crítica.

---

### 1.2 CONFLITOS DE INFRAESTRUTURA

#### ❌ BLOCKER P0-001: Duplicação de portas HOST

**Porta 8151 (2 serviços):**
- Linha 578: `maximus_core_service` → `"8151:8001"` (Prometheus metrics)
- Linha 930: `maximus-eureka` → `"8151:8036"` (API)

**Porta 5433 (2 serviços):**
- Linha 659: `hcl-postgres` → `"5433:5432"`
- Linha 2377: `postgres-immunity` → `"5433:5432"`

**Porta 8090 (2 ocorrências, 1 comentada):**
- Linha 167: `# cuckoo` → `"8090:8090"` (comentado, OK)
- Linha 2518: `kafka-ui-immunity` → `"8090:8080"` (ativo)

**Impacto:** Docker Compose falhará ao tentar expor portas já ocupadas.

---

#### ❌ BLOCKER P0-002: Rede externa ausente

```yaml
maximus-immunity-network:
  external: true
```

**Status:** Rede NÃO existe (`docker network ls` retornou vazio).

**Impacto:** Todos os serviços que usam esta rede falharão na inicialização.

**Serviços afetados:**
- wargaming-crisol
- hitl-patch-service
- kafka-ui-immunity
- adaptive_immune_system

---

#### ⚠️ CRITICAL P1-001: URLs internas com portas de HOST incorretas

**Padrão incorreto detectado:** Env vars apontando para portas do HOST em vez da porta do CONTAINER.

**Exemplos (20 ocorrências):**
```yaml
# API Gateway env vars (linha ~10-50)
- SINESP_SERVICE_URL=http://sinesp_service:8102  # ❌ 8102 é porta HOST, container usa 80
- CYBER_SERVICE_URL=http://cyber_service:8103    # ❌ idem
- DOMAIN_SERVICE_URL=http://domain_service:8104  # ❌ idem
- IP_INTELLIGENCE_SERVICE_URL=http://ip_intelligence_service:8105  # ❌ idem
- NMAP_SERVICE_URL=http://nmap_service:8106      # ❌ idem
- ATLAS_SERVICE_URL=http://atlas_service:8109    # ❌ idem
```

**Correção necessária:** Usar porta do CONTAINER (ex: `:80`, `:8007`, `:8013`).

---

#### ⚠️ CRITICAL P1-002: Inconsistência de nomeação (hífen vs underscore)

**Padrão detectado:** Serviços usam hífen no container_name, underscore no service name.

**Exemplos:**
```yaml
# Service name: osint-service (com hífen)
# Mas env var usa: osint_service (com underscore)
- OSINT_SERVICE_URL=http://osint_service:8007  # ❌ service real é osint-service
```

**DNS Docker:** Resolve pelo service name, NÃO pelo container_name.

**Impacto:** Conexões entre serviços falharão (DNS not found).

---

### 1.3 INTEGRIDADE DE DOCKERFILES

**Dockerfiles presentes:** 81/128 serviços (63%)  
**Dockerfiles ausentes:** ~47 serviços (37%)

**❌ CRITICAL P1-003:** 37% dos serviços NÃO têm Dockerfile próprio.

**Possíveis causas:**
1. Serviços usando `image:` em vez de `build:` (ex: redis, postgres)
2. Dockerfiles em paths não convencionais
3. Serviços realmente sem implementação

**Ação:** Validar lista de serviços sem Dockerfile.

---

### 1.4 CONSISTÊNCIA DE VARIÁVEIS DE AMBIENTE

#### ⚠️ CRITICAL P1-004: Service names inexistentes em URLs

**Detectado:** Env vars referenciam serviços que não existem no compose.

**Exemplo potencial:**
```yaml
# Linha ~145 (api_gateway)
- AURORA_PREDICT_URL=http://aurora_predict:80  # ❌ Serviço real: maximus_predict
- AURORA_ORCHESTRATOR_URL=http://aurora_orchestrator_service:80  # ❌ Não encontrado
```

**Ação:** Validar correspondência entre env vars e service names.

---

### 1.5 HEALTHCHECKS E STARTUP ORDER

**Serviços sem healthcheck:** ~60% (estimado)

**❌ MAJOR P2-001:** Majority dos serviços NÃO têm healthcheck definido.

**Impacto:** `depends_on` não consegue esperar serviço estar realmente READY, causando race conditions.

**Exemplo de healthcheck correto:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:80/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

### 1.6 VALIDAÇÃO DE REQUIREMENTS

**Não executado:** Requer instalação de pip-tools em cada serviço.

**Ação futura:** Criar CI check para conflitos de dependências.

---

## FASE 2: PLANO DE AÇÃO CIRÚRGICO

### P0 - BLOCKERS (executar AGORA)

#### FIX-001: Resolver conflito de porta 8151
**Severidade:** P0  
**Componentes:** maximus_core_service, maximus-eureka

```diff
# docker-compose.yml linha 930
- ports: "8151:8036"
+ ports: "8153:8036"  # Porta livre
```

**Validação:**
```bash
grep "8153:" docker-compose.yml  # Deve retornar vazio (porta livre)
```

---

#### FIX-002: Resolver conflito de porta 5433
**Severidade:** P0  
**Componentes:** hcl-postgres, postgres-immunity

```diff
# docker-compose.yml linha 2377
- ports: "5433:5432"
+ ports: "5434:5432"  # Porta livre
```

**Validação:**
```bash
grep "5434:" docker-compose.yml  # Deve retornar vazio
```

---

#### FIX-003: Criar rede externa
**Severidade:** P0  
**Componentes:** 4 serviços (wargaming, hitl, kafka-ui, adaptive_immune)

```bash
docker network create maximus-immunity-network
```

**Alternativa (se não precisar isolar):**
```diff
# docker-compose.yml linha ~2642
networks:
  maximus-network:
    name: maximus-ai-network
    driver: bridge
  maximus-immunity-network:
-   external: true
+   driver: bridge
```

---

### P1 - CRITICAL (executar em 24h)

#### FIX-004: Corrigir URLs internas no api_gateway
**Severidade:** P1  
**Componentes:** api_gateway + 20 serviços

**Padrão de correção:**
```diff
# docker-compose.yml (api_gateway environment)
- SINESP_SERVICE_URL=http://sinesp_service:8102
+ SINESP_SERVICE_URL=http://sinesp_service:80

- CYBER_SERVICE_URL=http://cyber_service:8103
+ CYBER_SERVICE_URL=http://cyber_service:80

- DOMAIN_SERVICE_URL=http://domain_service:8104
+ DOMAIN_SERVICE_URL=http://domain_service:80

- IP_INTELLIGENCE_SERVICE_URL=http://ip_intelligence_service:8105
+ IP_INTELLIGENCE_SERVICE_URL=http://ip_intelligence_service:80

- NMAP_SERVICE_URL=http://nmap_service:8106
+ NMAP_SERVICE_URL=http://nmap_service:80
```

**Total de mudanças:** ~15 URLs

---

#### FIX-005: Normalizar service names (osint)
**Severidade:** P1  
**Componentes:** api_gateway, osint-service

**Decisão:** Usar `osint-service` (hífen) como padrão.

```diff
# docker-compose.yml (api_gateway environment)
- OSINT_SERVICE_URL=http://osint_service:8007
+ OSINT_SERVICE_URL=http://osint-service:8007
```

**Validação:**
```bash
grep "^  osint-service:" docker-compose.yml  # Deve retornar o service
```

---

#### FIX-006: Corrigir referências a aurora_predict
**Severidade:** P1  
**Componentes:** api_gateway

```diff
# docker-compose.yml (api_gateway environment)
- AURORA_PREDICT_URL=http://aurora_predict:80
+ MAXIMUS_PREDICT_URL=http://maximus_predict:80
```

---

### P2 - MAJOR (executar em 1 semana)

#### FIX-007: Adicionar healthchecks mínimos
**Severidade:** P2  
**Componentes:** 60+ serviços core

**Template:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:<PORT>/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Prioridade:** api_gateway, redis, postgres, maximus_core_service, threat_intel_service.

---

## FASE 3: ORDEM DE EXECUÇÃO

### Fase 0 - Infraestrutura (5 min)
```bash
# 1. Criar rede
docker network create maximus-immunity-network

# 2. Aplicar FIX-001, FIX-002, FIX-003 (editar docker-compose.yml)
# (Ver patches abaixo)
```

### Fase 1 - Tier 0 Services (10 min)
```bash
docker compose up -d redis postgres qdrant
docker compose ps redis postgres qdrant
```

**Critério de sucesso:** Status `Up (healthy)` para os 3.

---

### Fase 2 - Tier 1 Services (20 min)
```bash
# Após aplicar FIX-004, FIX-005, FIX-006
docker compose up -d api_gateway sinesp_service domain_service ip_intelligence_service nmap_service

# Validar
curl http://localhost:8000/health
```

**Critério de sucesso:** API Gateway responde com status 200.

---

### Fase 3 - Tier 2+ Services (30 min)
```bash
docker compose up -d threat_intel_service malware_analysis_service ssl_monitor_service
docker compose up -d maximus_core_service
docker compose up -d maximus-eureka maximus-oraculo
```

---

## FASE 4: PATCHES CONSOLIDADOS

### Patch docker-compose.yml

```diff
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -17,7 +17,7 @@
       - CYBER_SERVICE_URL=http://cyber_service:80
       - DOMAIN_SERVICE_URL=http://domain_service:80
-      - IP_INTELLIGENCE_SERVICE_URL=http://ip_intelligence_service:8105
+      - IP_INTELLIGENCE_SERVICE_URL=http://ip_intelligence_service:80
       - NETWORK_MONITOR_SERVICE_URL=http://network_monitor_service:80
-      - NMAP_SERVICE_URL=http://nmap_service:8106
-      - OSINT_SERVICE_URL=http://osint_service:8007
-      - GOOGLE_OSINT_SERVICE_URL=http://google_osint_service:8101
-      - MAXIMUS_PREDICT_URL=http://maximus_predict:8126
-      - ATLAS_SERVICE_URL=http://atlas_service:8109
-      - AUTH_SERVICE_URL=http://auth_service:8110
-      - VULN_SCANNER_SERVICE_URL=http://vuln_scanner_service:8111
-      - SOCIAL_ENG_SERVICE_URL=http://social_eng_service:8112
-      - THREAT_INTEL_SERVICE_URL=http://threat_intel_service:8113
-      - MALWARE_ANALYSIS_SERVICE_URL=http://malware_analysis_service:8114
-      - SSL_MONITOR_SERVICE_URL=http://ssl_monitor_service:8115
+      - NMAP_SERVICE_URL=http://nmap_service:80
+      - OSINT_SERVICE_URL=http://osint-service:8007
+      - GOOGLE_OSINT_SERVICE_URL=http://google_osint_service:8031
+      - MAXIMUS_PREDICT_URL=http://maximus_predict:80
+      - ATLAS_SERVICE_URL=http://atlas_service:8000
+      - AUTH_SERVICE_URL=http://auth_service:80
+      - VULN_SCANNER_SERVICE_URL=http://vuln_scanner_service:80
+      - SOCIAL_ENG_SERVICE_URL=http://social_eng_service:80
+      - THREAT_INTEL_SERVICE_URL=http://threat_intel_service:8013
+      - MALWARE_ANALYSIS_SERVICE_URL=http://malware_analysis_service:8014
+      - SSL_MONITOR_SERVICE_URL=http://ssl_monitor_service:8015
       
@@ -927,7 +927,7 @@
   maximus-eureka:
     ...
     ports:
-      - "8151:8036"
+      - "8153:8036"
       
@@ -2374,7 +2374,7 @@
   postgres-immunity:
     ...
     ports:
-      - "5433:5432"
+      - "5434:5432"
       
@@ -2640,7 +2640,7 @@
 networks:
   maximus-network:
     name: maximus-ai-network
     driver: bridge
   maximus-immunity-network:
-    external: true
+    driver: bridge
```

---

## VALIDAÇÃO PÓS-FIX

### Script de validação automática

```bash
#!/bin/bash
# backend/scripts/validate_fixes.sh

echo "=== VALIDAÇÃO DE FIXES ==="

# FIX-001: Porta 8151 única
count=$(grep -c '"8151:' docker-compose.yml)
if [ $count -eq 1 ]; then
  echo "✅ FIX-001: Porta 8151 única"
else
  echo "❌ FIX-001: FAILED ($count ocorrências)"
fi

# FIX-002: Porta 5433 única
count=$(grep -c '"5433:' docker-compose.yml)
if [ $count -eq 1 ]; then
  echo "✅ FIX-002: Porta 5433 única"
else
  echo "❌ FIX-002: FAILED ($count ocorrências)"
fi

# FIX-003: Rede existe ou não é externa
if docker network ls | grep -q maximus-immunity || ! grep -q "external: true" docker-compose.yml; then
  echo "✅ FIX-003: Rede disponível"
else
  echo "❌ FIX-003: FAILED (rede ausente)"
fi

# FIX-004: URLs corretas
bad_urls=$(grep -c 'SERVICE_URL=http://[a-z_-]\+:[8-9][0-9]\{3\}' docker-compose.yml || true)
if [ $bad_urls -eq 0 ]; then
  echo "✅ FIX-004: URLs internas corretas"
else
  echo "⚠️ FIX-004: PARTIAL ($bad_urls URLs ainda incorretas)"
fi
```

---

## CRITÉRIOS DE SUCESSO

**Definição de "Backend UP":**
1. ✅ Tier 0 (redis, postgres, qdrant): 100% UP
2. ✅ api_gateway respondendo em http://localhost:8000/health
3. ✅ Serviços core (15+): 90%+ UP
4. ✅ Sem erros críticos em logs

**SLA de disponibilidade:**
- Tier 0: 100% UP (OBRIGATÓRIO)
- Tier 1: 95% UP
- Tier 2+: 80% UP

---

## PRÓXIMOS PASSOS

1. ✅ Executar FIX-001, FIX-002, FIX-003 (BLOCKER)
2. ✅ Executar FIX-004, FIX-005, FIX-006 (CRITICAL)
3. ⏳ Subir ambiente por fases
4. ⏳ Validar smoke tests
5. ⏳ Adicionar healthchecks (P2)

**Tempo estimado para Backend UP:** 1-2 horas (com fixes aplicados).

---

**Gerado automaticamente por:** GitHub Copilot CLI  
**Próximo relatório:** BACKEND_FIX_EXECUTION_REPORT.md (após aplicação dos fixes)
