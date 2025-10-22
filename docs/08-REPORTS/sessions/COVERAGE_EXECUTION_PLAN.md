# COVERAGE 100% - PLANO DE EXECUÇÃO

**Meta:** 19.50% → 100%
**Método:** Layer-by-layer, test-first

---

## FASE 1: SHARED LAYER (0% → 100%)

### Priority Queue (15 files, 0% coverage):

1. **backend/shared/constants.py** (254 statements)
   - Tests: Enum completeness, value validation
   
2. **backend/shared/enums.py** (322 statements)  
   - Tests: All enum members, serialization
   
3. **backend/shared/validators.py** (179 statements)
   - Tests: Edge cases, malformed inputs
   
4. **backend/shared/base_config.py** (121 statements)
   - Tests: Env loading, defaults, validation
   
5. **backend/shared/audit_logger.py** (112 statements)
   - Tests: Log formatting, async writes
   
6. **backend/shared/error_handlers.py** (72 statements)
   - Tests: Exception mapping, status codes
   
7. **backend/shared/sanitizers.py** (151 statements)
   - Tests: XSS, SQL injection vectors
   
8. **backend/shared/vault_client.py** (156 statements)
   - Tests: Mock vault, secret retrieval
   
9. **backend/shared/response_models.py** (94 statements)
   - Tests: Pydantic validation, serialization
   
10. **backend/shared/openapi_config.py** (35 statements)
    - Tests: Schema generation

---

## FASE 2: ACTIVE_IMMUNE_CORE (7-25% → 100%)

### Agents (7-24%):
- base.py (7.3%)
- macrofago.py (7.5%)  
- agent_factory.py (18.9%)
- b_cell.py, dendritic_cell.py, helper_t_cell.py (21-24%)

### Communication (15-21%):
- hormones.py (15.15%)
- kafka_consumers.py (16.38%)
- cytokines.py (18.29%)
- kafka_events.py (21.49%)

### Coordination (11-65%):
- homeostatic_controller.py (11.78%)
- lymphnode.py (12.15%)
- clonal_selection.py (14.47%)

---

## FASE 3: MAXIMUS_CORE_SERVICE (12-67%)

### Consciousness:
- esgt/coordinator.py (21.01%)
- esgt/kuramoto.py (25.37%)
- esgt/arousal_integration.py (27.66%)
- episodic_memory/memory_buffer.py (12.03%)

### ToM:
- tom/models.py (22.32%)
- tom/belief_tracker.py (38.75%)
- tom/hypothesis_generator.py (44.93%)
- tom/tom_engine.py (54.47%)

---

## FASE 4: TEGUMENTAR MODULE (15-36%)

- derme/ml/anomaly_detector.py (27.6%)
- derme/langerhans_cell.py (28.9%)
- derme/signature_engine.py (35.7%)
- derme/stateful_inspector.py (36.8%)
- lymphnode/api.py (36.9%)

---

## ESTIMATIVA

**Fase 1:** 2,500 statements → ~12 horas  
**Fase 2:** 4,000 statements → ~18 horas  
**Fase 3:** 3,500 statements → ~16 horas  
**Fase 4:** 1,500 statements → ~8 horas  

**Total:** ~54 horas (~7 dias × 8h)

---

## VALIDAÇÃO POR FASE

```bash
# Após cada fase:
pytest --cov=backend/shared --cov-fail-under=100
pytest --cov=backend/services/active_immune_core --cov-fail-under=100
pytest --cov=backend/services/maximus_core_service --cov-fail-under=100
pytest --cov=backend/modules/tegumentar --cov-fail-under=100
```
