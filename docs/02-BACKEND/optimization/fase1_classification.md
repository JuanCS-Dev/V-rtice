# FASE 1 - CLASSIFICAÇÃO DE IMPORT ERRORS

**Total Collection Errors:** 131  
**Erros Únicos Identificados:** ~50  

---

## TOP ERRORS (Por Frequência)

### 1. monitoring.logger (13 occurrências)
```
Affected services:
- active_immune_core/monitoring/test_*.py (3 files)
- maximus_core_service/monitoring/* (10+ files)
```

**Causa:** Import relativo sem package prefix  
**Fix:** Mudar `from monitoring.logger` → `from services.{service}.monitoring.logger`

---

### 2. compassion.event_detector (9 occurrências)
```
Affected:
- consciousness/compassion/tests/test_compassion_planner.py
- consciousness/compassion/tests/test_event_detector.py
- consciousness/consciousness/tests/* (7 files)
```

**Causa:** Namespace collision + relative imports  
**Fix:** `from compassion.event_detector` → `from backend.consciousness.compassion.event_detector`

---

### 3. justice.precedent_database (9 occurrências)
```
Affected:
- maximus_core_service/justice/tests/*.py (9 files)
```

**Causa:** Import relativo sem package  
**Fix:** `from justice.precedent_database` → `from services.maximus_core_service.justice.precedent_database`

---

### 4. models.apv (7 occurrências)
```
Affected:
- maximus_eureka/tests/unit/*.py (7 files)
```

**Causa:** 'models' is not a package  
**Fix:** `from models.apv` → `from services.maximus_eureka.models.apv`

---

### 5. cannot import 'app' from 'api' (7 occurrências)
```
Affected:
- maximus_oraculo/tests/*.py
```

**Causa:** api/__init__.py vazio ou sem app  
**Fix:** Verificar api/__init__.py, adicionar `from .main import app`

---

### 6. cannot import 'settings' from 'config' (5 occurrências)
```
Affected:
- maximus_core_service/ethics/tests/*.py
```

**Causa:** config.py incorreto ou settings não exportado  
**Fix:** Verificar config.py, exportar settings

---

### 7. memory (4 occorrências)
```
Affected:
- offensive_orchestrator_service/tests/*.py
```

**Causa:** `from memory` sem package prefix  
**Fix:** `from memory` → `from services.offensive_orchestrator_service.memory`

---

### 8. orchestrator (3 occorrências)
```
Affected:
- offensive_orchestrator_service/tests/*.py
```

**Causa:** Import relativo  
**Fix:** Absolute imports

---

### 9. torch (2 occurrências)
```
Affected:
- maximus_core_service/tests/*.py
```

**Causa:** Dependency não instalada  
**Fix:** Adicionar torch ao requirements ou skip test se opcional

---

### 10. hotl (2 occorrências)
```
Affected:
- offensive_orchestrator_service/tests/test_hotl_*.py
```

**Causa:** Import relativo  
**Fix:** Absolute imports

---

## ESTRATÉGIA DE FIXING

### Batch 1: Namespace Absolute Imports (90 arquivos)
**Pattern:** `from {module}` → `from backend.services.{service}.{module}`

Aplicar script batch:
```bash
# monitoring.*
find backend/services -name "test_*.py" -exec sed -i \
  's/from monitoring\./from services.{SERVICE}.monitoring./g' {} +

# justice.*
find backend/services/maximus_core_service/justice/tests -name "*.py" -exec sed -i \
  's/from justice\./from services.maximus_core_service.justice./g' {} +

# Similar para outros...
```

---

### Batch 2: consciousness Namespace (9 arquivos)
```bash
find backend/consciousness -name "test_*.py" -exec sed -i \
  's/from compassion\./from backend.consciousness.compassion./g' {} +
```

---

### Batch 3: Config/API Exports (12 arquivos)
Verificar manualmente:
1. `backend/services/maximus_oraculo/api/__init__.py` → add `from .main import app`
2. `backend/services/maximus_core_service/ethics/config.py` → export settings
3. Similar para outros

---

### Batch 4: Optional Dependencies (2 arquivos)
```python
# Add skip decorator
pytest.mark.skipif(not has_torch, reason="torch not installed")
```

---

## CRONOGRAMA

```
Batch 1: 90 files → Script automated (30min)
Batch 2: 9 files  → Script automated (15min)
Batch 3: 12 files → Manual review (1h)
Batch 4: 2 files  → Manual skip (15min)
───────────────────────────────────────────
TOTAL: ~2h
```

---

## VALIDAÇÃO

```bash
# Após cada batch:
pytest backend/ --collect-only -q 2>&1 | grep "ERROR" | wc -l

# Target: 131 → 0
```

---

**PRÓXIMO PASSO:** Executar Batch 1 (monitoring.* fixes)
