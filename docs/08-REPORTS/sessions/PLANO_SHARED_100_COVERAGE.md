# PLANO: SHARED MODULES - 100% COVERAGE

**Status Atual:** 25.12%  
**Meta:** 100%  
**Gap:** 10 módulos sem testes

---

## MÓDULOS POR PRIORIDADE

### TIER 1: CRÍTICOS (0% → 100%)
**Impacto:** Alto - Usados por múltiplos serviços

1. **exceptions.py** (164 lines) - 57.83% → 100%
   - Custom exception hierarchy
   - FALTAM: 69 linhas não cobertas
   - TESTES: Error raising, serialization, inheritance

2. **vault_client.py** (156 lines) - 0% → 100%
   - HashiCorp Vault integration
   - CRÍTICO para secrets management
   - TESTES: Connection, read/write, token refresh

3. **error_handlers.py** (72 lines) - 0% → 100%
   - FastAPI exception handlers
   - TESTES: HTTP exceptions, custom handlers

4. **base_config.py** - 0% → 100%
   - Base configuration class
   - TESTES: Environment loading, validation

---

### TIER 2: MÉDIOS (0% → 100%)

5. **enums.py** (322 lines) - 0% → 100%
   - Enumerations system-wide
   - TESTES: Enum values, string conversion

6. **response_models.py** (94 lines) - 0% → 100%
   - Pydantic response schemas
   - TESTES: Validation, serialization

7. **websocket_gateway.py** (175 lines) - 0% → 100%
   - WebSocket connection manager
   - TESTES: Connection, broadcast, disconnect

---

### TIER 3: BAIXA PRIORIDADE

8. **audit_logger.py** - 0% → 100%
   - Audit logging
   - TESTES: Log formatting, persistence

9. **constants.py** - 0% → 100%
   - System constants
   - TESTES: Value consistency

10. **container_health.py** (146 lines) - 0% → 100%
    - Docker health checks
    - TESTES: Health probes, readiness

11. **openapi_config.py** (35 lines) - 0% → 100%
    - OpenAPI schema config
    - TESTES: Schema generation

---

## ESTRATÉGIA DE EXECUÇÃO

### FASE 1: TIER 1 (4 módulos críticos)
**Estimativa:** 2h  
**Ordem:**
1. exceptions.py (completar gaps)
2. error_handlers.py
3. base_config.py
4. vault_client.py

### FASE 2: TIER 2 (3 módulos médios)
**Estimativa:** 1.5h
5. response_models.py
6. enums.py
7. websocket_gateway.py

### FASE 3: TIER 3 (4 módulos baixa prioridade)
**Estimativa:** 1h
8. audit_logger.py
9. constants.py
10. container_health.py
11. openapi_config.py

---

## MÉTRICAS DE SUCESSO

| Fase | Módulos | Target Coverage | Testes Estimados |
|------|---------|-----------------|------------------|
| 1 | 4 | 100% | ~120 testes |
| 2 | 3 | 100% | ~80 testes |
| 3 | 4 | 100% | ~60 testes |
| **TOTAL** | **11** | **100%** | **~260 testes** |

**Coverage Final Esperado:** 100% em backend/shared

---

## VALIDAÇÃO

Após cada fase:
```bash
python -m pytest backend/tests/test_shared_*.py -v --cov=backend/shared --cov-report=term-missing
```

**Critério de Aceitação:**
- ✅ Coverage >= 95% por módulo
- ✅ Zero TODOs/mocks
- ✅ Todos testes passando
- ✅ Mypy strict pass
- ✅ Ruff pass

---

**Início:** Imediato  
**Duração Total:** ~4.5h  
**Executor:** Claude (Tático)
