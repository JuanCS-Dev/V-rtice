# PLANO ABSOLUTO - 100% BACKEND COVERAGE

**Data:** 2025-10-17 23:40 UTC  
**Executor:** Sob Doutrina v2.7  
**Meta:** 100% ABSOLUTO em CADA arquivo Python do backend

---

## ESCOPO DEFINITIVO

### INCLUÍDO:
```
backend/shared/          → 20 arquivos
backend/libs/            → 3 libs (vertice_api, vertice_core, vertice_db)
backend/services/        → 83+ serviços
backend/modules/         → tegumentar system
backend/api_gateway/     → gateway principal
backend/api_docs_portal.py
```

### EXCLUÍDO:
```
backend/consciousness/   → Projeto autônomo (próprio docker-compose)
```

---

## FASE 1: BACKEND/SHARED - 10 MÓDULOS SEM TESTES

### TRACK 1.1 - Infraestrutura Core (550 stmts):
**Prioridade:** CRÍTICA  
**Tempo estimado:** 3-4h

1. **audit_logger.py** (106 stmts, 20 branches)
   - Testes: Async logging, audit trail, error handling
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_audit_logger.py`

2. **error_handlers.py** (72 stmts, 8 branches)
   - Testes: HTTP exceptions, validation errors, custom handlers
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_error_handlers.py`

3. **openapi_config.py** (36 stmts, 8 branches)
   - Testes: OpenAPI schema generation, custom fields
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_openapi_config.py`

4. **websocket_gateway.py** (174 stmts, 34 branches)
   - Testes: WebSocket lifecycle, broadcast, error recovery
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_websocket_gateway.py`

5. **devops_tools/container_health.py** (146 stmts, 14 branches)
   - Testes: Health checks, liveness/readiness probes
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_container_health.py`

6. **middleware/__init__.py** (2 stmts)
   - Testes: Module imports
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_middleware_init.py`

7. **middleware/rate_limiter.py** (118 stmts, 26 branches)
   - Testes: Rate limiting logic, Redis backend, sliding window
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_middleware_rate_limiter.py`

### TRACK 1.2 - Definições & Enums (576 stmts):
**Prioridade:** ALTA  
**Tempo estimado:** 2-3h

8. **constants.py** (254 stmts)
   - Testes: Constant definitions, immutability
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_constants.py`

9. **enums.py** (322 stmts)
   - Testes: All enum values, string representations
   - Cobertura alvo: 100%
   - Arquivo teste: `backend/shared/tests/test_enums.py`

### TRACK 1.3 - Security Tools (105 stmts):
**Prioridade:** CRÍTICA  
**Tempo estimado:** 2h

10. **security_tools/rate_limiter.py** (105 stmts, 22 branches)
    - Testes: Token bucket, leaky bucket algorithms
    - Cobertura alvo: 100%
    - Arquivo teste: `backend/shared/tests/test_security_tools_rate_limiter.py`

---

## FASE 2: BACKEND/SHARED - COMPLETAR MÓDULOS PARCIAIS

### TRACK 2.1 - Edge Cases & Branches:
**Prioridade:** ALTA  
**Tempo estimado:** 3-4h

1. **exceptions.py**: 57.83% → 100% (-69 stmts)
   - Missing: Exception constructors, error codes, repr
   - Adicionar a: `backend/shared/tests/test_exceptions.py` (criar)

2. **vulnerability_scanner.py**: 73.73% → 100% (-33 stmts)
   - Missing: Error paths, edge cases em scan functions
   - Adicionar a: `backend/tests/test_shared_vulnerability_scanner.py`

3. **validators.py**: 92.89% → 100% (-11 stmts)
   - Missing: Edge cases em regex validators
   - Adicionar a: `backend/tests/test_shared_validators.py`

4. **vault_client.py**: 94.31% → 100% (-9 stmts)
   - Missing: Credential fallback paths, error handling
   - Adicionar a: `backend/shared/tests/test_vault_client.py`

---

## FASE 3: BACKEND/LIBS - VALIDAR 100%

**Status atual:** 100% (267 stmts)  
**Ação:** Validação tripla (ruff, mypy, Pagani)

```bash
pytest backend/libs --cov=backend/libs --cov-report=term
ruff check backend/libs/
mypy backend/libs/
```

---

## FASE 4: BACKEND/SERVICES - VARREDURA COMPLETA

### METODOLOGIA:
```bash
# 1. Listar todos os serviços
find backend/services -maxdepth 1 -type d ! -path "*/.*"

# 2. Para cada serviço:
#    a) Coletar coverage
#    b) Identificar gaps
#    c) Criar/completar testes
#    d) Validar 100%

# 3. Documentar em:
#    docs/backend_100/service_[NAME]_coverage.json
```

### SERVIÇOS PRIORITÁRIOS (baseado em complexidade):
1. command_bus_service (C2L)
2. maximus_core_service
3. active_immune_core
4. offensive_orchestrator
5. verdict_engine
6. [... 78 serviços restantes]

---

## FASE 5: BACKEND/MODULES - TEGUMENTAR SYSTEM

**Status atual:** Parcial (tegumentar/metrics.py, config.py = 100%)  
**Missing:**
- tegumentar/orchestrator.py: 52.94%
- tegumentar/derme/* (múltiplos arquivos)
- tegumentar/epiderme/*
- tegumentar/hipoderme/*
- tegumentar/lymphnode/*

---

## FASE 6: BACKEND/API_GATEWAY

**Status atual:** api_docs_portal.py = 100%  
**Pendente:**
- api_gateway/main.py
- api_gateway/reactive_fabric_integration.py

---

## EXECUÇÃO - PROTOCOLOS DOUTRINÁRIOS

### Artigo I - Cláusula 3.3 (Validação Tripla Silenciosa):
```bash
# Para cada arquivo corrigido:
ruff check [arquivo]
mypy [arquivo]
grep -E "(TODO|FIXME|mock|Mock)" [arquivo]

# Reportar APENAS se falhar
```

### Artigo VI - Seção 6 (Silêncio Operacional):
- Executar steps silenciosamente
- Reportar: 25%, 50%, 75%, 100%
- Bloqueadores críticos apenas

### Documentação Obrigatória:
**A cada commit:**
```bash
# Gerar relatório
pytest --cov --cov-report=json:docs/backend_100/coverage_[TIMESTAMP].json

# Commit pattern:
git commit -m "feat(shared): [módulo] → 100% (+[N] testes)"
```

---

## MÉTRICAS DE SUCESSO

### TARGET ABSOLUTO:
```
backend/shared/          → 100.00% (2394 stmts)
backend/libs/            → 100.00% (267 stmts)
backend/services/        → 100.00% (~15000 stmts estimados)
backend/modules/         → 100.00% (~2000 stmts estimados)
backend/api_gateway/     → 100.00% (~500 stmts estimados)

TOTAL: 100.00% (~20000 stmts)
```

### VALIDAÇÃO FINAL:
```bash
pytest backend \
  --ignore=backend/consciousness \
  --cov=backend/shared \
  --cov=backend/libs \
  --cov=backend/services \
  --cov=backend/modules \
  --cov=backend/api_gateway \
  --cov-report=term \
  --cov-report=json:docs/backend_100/FINAL_100_ABSOLUTE.json \
  --cov-fail-under=100
```

---

## CRONOGRAMA ESTIMADO

**FASE 1:** 7-9h (10 módulos shared sem testes)  
**FASE 2:** 3-4h (4 módulos shared parciais)  
**FASE 3:** 1h (validação libs)  
**FASE 4:** 40-60h (83 serviços)  
**FASE 5:** 8-12h (tegumentar)  
**FASE 6:** 2-3h (api_gateway)  

**TOTAL ESTIMADO:** 61-89h de execução pura  
**COM IMPREVISTOS:** 80-120h

---

## COMANDO DE INÍCIO

```bash
# FASE 1 - TRACK 1.1 - audit_logger.py
cd /home/juan/vertice-dev
touch backend/shared/tests/test_audit_logger.py
# [Implementação...]
```

---

**"De tanto não parar, a gente chega lá."**  
**Para Honra e Glória do nome DELE.**
