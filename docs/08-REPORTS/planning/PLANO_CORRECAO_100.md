# PLANO DE CORREÇÃO - 100% ABSOLUTO
**Missão:** Atingir 100% coverage, 100% conformidade, 0 warnings, 0 falhas

**Data:** 2025-10-17  
**Executor:** Tático  
**Status:** 🔴 INICIANDO

---

## SITUAÇÃO ATUAL

### Coverage Backend
- **Atual:** 24.30% (1927 miss / 2469 total)
- **Meta:** 100.00%
- **Gap:** -75.70%

### Módulos Críticos
| Módulo | Coverage | Miss | Target |
|--------|----------|------|--------|
| backend/shared/ | 24.30% | 1927 | 100% |
| backend/libs/ | ~95% | TBD | 100% |
| backend/services/ | ~13% | TBD | 100% |

### Docker Services
- ⚠️ maximus-predict: Up 12h, unhealthy
- ⚠️ 13 support services: unhealthy/down
- **Target:** 16/16 healthy

---

## FASE 1: ANÁLISE PROFUNDA (1h)

### 1.1 Mapear Coverage Completo
```bash
# Backend shared
pytest backend/tests/ --cov=backend/shared --cov-report=json:coverage_shared_detailed.json

# Backend libs  
pytest backend/libs/vertice_core/tests/ --cov=backend/libs/vertice_core --cov-report=json:coverage_core_detailed.json
pytest backend/libs/vertice_api/tests/ --cov=backend/libs/vertice_api --cov-report=json:coverage_api_detailed.json
pytest backend/libs/vertice_db/tests/ --cov=backend/libs/vertice_db --cov-report=json:coverage_db_detailed.json

# Backend services
for svc in api_gateway osint_service maximus_core_service; do
    pytest backend/services/$svc/tests/ --cov=backend/services/$svc --cov-report=json:coverage_${svc}.json
done
```

### 1.2 Identificar Missing Lines
```bash
# Gerar relatório detalhado
pytest backend/ --cov=backend --cov-report=html:htmlcov_full --cov-report=term-missing > coverage_full_report.txt
```

### 1.3 Categorizar Gaps
- **Tipo A:** Código sem testes (precisa criar)
- **Tipo B:** Edge cases não cobertos (precisa adicionar)
- **Tipo C:** Exception paths não testados (precisa adicionar)
- **Tipo D:** Código morto (pode remover)

---

## FASE 2: BACKEND/SHARED (Target: 100%)

### 2.1 Priorização por Impacto
**Ordem de Execução:**
1. `exceptions.py` (57.83% → 100%) - 95 lines missing
2. `validators.py` (92.89% → 100%) - 11 lines missing
3. `sanitizers.py` (85.60% → 100%) - 18 lines missing
4. `vulnerability_scanner.py` (77.66% → 100%) - 27 lines missing
5. Demais (0% → 100%) - 1776 lines missing

### 2.2 Estratégia por Módulo

#### exceptions.py (95 lines)
**Missing Lines:** 90, 100→102, 136-137, 144-145, 152-154, etc.
**Ações:**
- Criar testes para cada exception class
- Testar inheritance chain
- Testar custom messages
- Testar exception attributes

**Tempo Estimado:** 2h

#### validators.py (11 lines)
**Missing Lines:** 170-171, 186-187, 221, 261, 396, 407, 411, 452, 639
**Ações:**
- Testar edge cases (empty strings, null, unicode)
- Testar validation failures
- Testar regex patterns

**Tempo Estimado:** 1h

#### sanitizers.py (18 lines)
**Missing Lines:** 205, 223, 270, 295, 336, 410, 435, 466, etc.
**Ações:**
- Testar XSS patterns
- Testar SQL injection patterns
- Testar path traversal
- Testar edge cases

**Tempo Estimado:** 1h

#### vulnerability_scanner.py (27 lines)
**Missing Lines:** 97, 104→103, 122, 153, 156, etc.
**Ações:**
- Testar CVE detection
- Testar severity classification
- Testar async scanning
- Mock external API calls

**Tempo Estimado:** 2h

#### Módulos 0% (1776 lines)
**Módulos:**
- api_docs_portal.py (86 lines)
- audit_logger.py (112 lines)
- base_config.py (121 lines)
- constants.py (254 lines)
- container_health.py (146 lines)
- enums.py (322 lines)
- error_handlers.py (72 lines)
- rate_limiter.py (124 + 103 lines)
- openapi_config.py (35 lines)
- response_models.py (94 lines)
- vault_client.py (156 lines)
- websocket_gateway.py (175 lines)

**Estratégia:**
- Agrupar por tipo (config, models, handlers)
- Criar test factories
- Usar parametrized tests
- Mock dependencies externas

**Tempo Estimado:** 16h

---

## FASE 3: BACKEND/LIBS (Target: 100%)

### 3.1 vertice_core
**Atual:** ~77% (conforme TRACK1_RELATORIO)
**Gap:** 23%
**Ações:**
- Cobrir tracing edge cases
- Testar metrics collectors
- Testar exception paths em logging

**Tempo Estimado:** 3h

### 3.2 vertice_api
**Atual:** ~95% (conforme último report)
**Gap:** 5%
**Ações:**
- Completar dependencies.py (ausente)
- Completar versioning.py (ausente)
- Testar error handlers

**Tempo Estimado:** 4h

### 3.3 vertice_db
**Atual:** ~98% (conforme último report)
**Gap:** 2%
**Ações:**
- Completar session.py (ausente)
- Testar transaction rollbacks
- Testar connection pool

**Tempo Estimado:** 3h

---

## FASE 4: BACKEND/SERVICES (Target: 100%)

### 4.1 Service Template
**Status:** ✅ Baseline (95%+)
**Ações:** Validar apenas

### 4.2 api_gateway
**Atual:** ~13% (estimado)
**Ações:**
- Migrar para Clean Architecture
- Criar testes unitários completos
- Criar integration tests

**Tempo Estimado:** 8h

### 4.3 osint_service
**Atual:** ~13% (estimado)
**Ações:**
- Migrar para Clean Architecture
- Testar cada analyzer
- Mock external APIs

**Tempo Estimado:** 12h

### 4.4 maximus_core_service
**Atual:** ~5% (estimado, monolito)
**Ações:**
- **NÃO TESTAR MONOLITO**
- Decomposição primeiro (Track 3)
- Testar bounded contexts separadamente

**Tempo Estimado:** Fora de escopo (Track 3)

### 4.5 Demais Services
**Lista:**
- vertice-vuln-scanner
- vertice-malware-analysis
- vertice-nmap
- vertice-threat-intel
- vertice-ip-intel
- vertice-domain
- vertice-ssl-monitor
- active_immune_core
- consciousness_api

**Estratégia:**
- Priorizar por criticidade
- Usar template como base
- Paralelizar quando possível

**Tempo Estimado:** 40h

---

## FASE 5: DOCKER SERVICES (Target: 16/16 healthy)

### 5.1 Diagnosticar Unhealthy
```bash
# Checar logs de cada serviço
for svc in maximus-predict osint_service vuln-scanner malware-analysis nmap threat-intel ip-intel domain ssl-monitor; do
    docker-compose logs --tail=50 vertice-$svc 2>&1 | grep -E "ERROR|FATAL|unhealthy"
done
```

### 5.2 Categorizar Problemas
- **Tipo A:** Dependência não disponível (DB, Redis, etc.)
- **Tipo B:** Config incorreta (.env, ports)
- **Tipo C:** Código com bug
- **Tipo D:** Health check mal configurado

### 5.3 Corrigir Sistematicamente
**Por serviço:**
1. Identificar root cause
2. Aplicar fix
3. Restart service
4. Validar health
5. Documentar

**Tempo Estimado:** 6h

---

## FASE 6: VALIDAÇÃO FINAL (Target: 100% Pass)

### 6.1 Coverage Total
```bash
# Backend completo
pytest backend/ \
    --cov=backend \
    --cov-report=term-missing \
    --cov-report=html:htmlcov_final \
    --cov-report=json:coverage_final.json \
    --cov-fail-under=100

# Libs isoladas
for lib in vertice_core vertice_api vertice_db; do
    pytest backend/libs/$lib/tests/ \
        --cov=backend/libs/$lib \
        --cov-fail-under=100
done
```

### 6.2 Lint & Type Check
```bash
# Ruff (zero warnings)
ruff check backend/ --select ALL --ignore E501,ANN401

# Mypy (zero errors)
mypy backend/ --strict --no-error-summary

# Bandit (zero issues)
bandit -r backend/ -ll
```

### 6.3 Build & Deploy
```bash
# Build libs
for lib in vertice_core vertice_api vertice_db; do
    cd backend/libs/$lib
    python -m build
    cd -
done

# Build services (Docker)
docker-compose build --no-cache

# Deploy
docker-compose up -d

# Validar health
docker-compose ps | grep -v "Up (healthy)" && exit 1 || echo "✅ ALL HEALTHY"
```

---

## CRONOGRAMA EXECUTIVO

| Fase | Duração | Prioridade | Status |
|------|---------|------------|--------|
| 1. Análise Profunda | 1h | CRÍTICO | 🔴 TODO |
| 2. Backend/Shared | 22h | CRÍTICO | 🔴 TODO |
| 3. Backend/Libs | 10h | CRÍTICO | 🔴 TODO |
| 4. Backend/Services | 60h | ALTO | 🔴 TODO |
| 5. Docker Services | 6h | MÉDIO | 🔴 TODO |
| 6. Validação Final | 3h | CRÍTICO | 🔴 TODO |
| **TOTAL** | **102h** | - | **0%** |

**Estimativa:** 13 dias úteis (8h/dia)

---

## REGRAS DE EXECUÇÃO (DOUTRINA)

### Artigo I - Cláusula 3.3 (Validação Tripla)
**Obrigatório após cada módulo:**
1. ✅ Ruff check (zero warnings)
2. ✅ Mypy (zero errors)
3. ✅ Pytest --cov-fail-under=100

**Reportar APENAS se falhar.**

### Artigo II - Seção 2 (Regra dos 99%)
**MODIFICAÇÃO TEMPORÁRIA:**
- Durante correção: target = 100% (não 99%)
- Justificativa: Missão explícita do Arquiteto-Chefe

### Artigo VI - Seção 6 (Silêncio Operacional)
**Durante execução:**
- ❌ NÃO narrar cada arquivo testado
- ✅ Reportar apenas:
  - 25% completo
  - 50% completo
  - 75% completo
  - 100% completo
  - Bloqueadores críticos

---

## BLOQUEADORES CONHECIDOS

### B1: Dependências Externas
**Problema:** vault_client, redis, external APIs
**Solução:** Mock com pytest-mock + responses

### B2: Async Code
**Problema:** Event loops, fixtures async
**Solução:** pytest-asyncio + asyncio.run()

### B3: Docker in Tests
**Problema:** container_health precisa Docker
**Solução:** testcontainers-python OU mock subprocess

### B4: Database Tests
**Problema:** SQLAlchemy async sessions
**Solução:** pytest-postgresql + factories

---

## CRITÉRIOS DE SUCESSO

### ✅ Coverage
- [ ] Backend/shared: 100.00%
- [ ] Backend/libs: 100.00%
- [ ] Backend/services (migrados): 100.00%
- [ ] **TOTAL BACKEND:** 100.00%

### ✅ Qualidade
- [ ] Ruff: 0 warnings (ALL rules)
- [ ] Mypy: 0 errors (strict mode)
- [ ] Bandit: 0 issues (high confidence)
- [ ] Pytest: 0 failures, 0 skips

### ✅ Infraestrutura
- [ ] Docker: 16/16 services healthy
- [ ] Builds: 100% success
- [ ] Logs: 0 errors/fatals

### ✅ Documentação
- [ ] Coverage reports gerados
- [ ] ADRs atualizados
- [ ] README.md completo

---

## PRÓXIMA AÇÃO

**AGUARDANDO APROVAÇÃO DO ARQUITETO-CHEFE**

**Pergunta:** Iniciar FASE 1 (Análise Profunda) agora?

**Comandos preparados:**
```bash
# 1. Mapear coverage detalhado
pytest backend/tests/ --cov=backend --cov-report=json:coverage_backend_detailed.json --cov-report=term-missing > coverage_analysis.txt

# 2. Gerar HTML report
pytest backend/tests/ --cov=backend --cov-report=html:htmlcov_full

# 3. Categorizar gaps
python scripts/analyze_coverage_gaps.py coverage_backend_detailed.json > gaps_categorized.md
```

---

**FIM DO PLANO DE CORREÇÃO**
