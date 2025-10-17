# BACKEND 100% COVERAGE - EXECUTION STRATEGY

**Status Atual:**
- ✅ LIBS: 100% (536/536 stmts, 145/145 tests)
- ⚠️ SERVICES: Análise requerida (83 services, 82k+ LOC)

---

## BLOQUEADORES IDENTIFICADOS

### 1. Import Errors (RESOLVIDO)
- ❌ `ModuleNotFoundError: communication`
- ✅ **Fix:** pytest.ini com PYTHONPATH dinâmico

### 2. Performance (CRÍTICO)
- ❌ active_immune_core: 84 test files (timeout >120s)
- ❌ Coleta full de 83 services: inviável em single run

---

## ESTRATÉGIA: INCREMENTAL POR PRIORITY

### TIER 1: Core Services (Priority 1) - Dias 1-3
```
api_gateway/          - API entry point
maximus_core_service/ - AI core
osint_service/        - OSINT
```

### TIER 2: Security Services (Priority 2) - Dias 4-6
```
vuln_scanner_service/
threat_intel_service/
malware_analysis_service/
```

### TIER 3: Support Services (Priority 3) - Dias 7-10
```
domain_service/
ip_intelligence_service/
ssl_monitor_service/
nmap_service/
```

### TIER 4: Specialized (Priority 4) - Dias 11-15
```
active_immune_core/     - Complex (84 tests)
adaptive_immunity_service/
autonomous_investigation_service/
```

### TIER 5: Remaining (Priority 5) - Dias 16-30
```
[73 services restantes]
```

---

## METODOLOGIA

### Por Service:
1. **Isolate**: `cd services/{service}`
2. **Analyze**: Count tests, LOC, dependencies
3. **Execute**: `pytest tests/ --cov=. --cov-report=json`
4. **Fix**: Identificar missing lines
5. **Validate**: Re-run até 100%
6. **Document**: Update report

### Metrics Tracking:
```python
{
  "service": "api_gateway",
  "coverage_pct": 87.5,
  "tests_pass": "45/50",
  "missing_lines": 156,
  "priority": 1,
  "status": "in_progress"
}
```

---

## GATES

### GATE 1: TIER 1 Complete (Dia 3)
- [ ] api_gateway: 100%
- [ ] maximus_core: 100%
- [ ] osint: 100%

### GATE 2: TIER 1-3 Complete (Dia 10)
- [ ] 10 services: 100%
- [ ] Bloqueadores documentados
- [ ] Strategy ajustada se necessário

### GATE 3: ALL Services 100% (Dia 30)
- [ ] 83 services: 100%
- [ ] Backend total: 100%
- [ ] Build validation passed

---

## TOOLS

### Coverage Aggregator Script
```bash
#!/bin/bash
# aggregate_coverage.sh
for svc in services/*/; do
  cd "$svc"
  pytest --cov=. --cov-report=json:coverage.json -q
  jq -r '.totals.percent_covered' coverage.json >> ../../coverage_tracker.txt
  cd ../..
done
```

### Daily Report Generator
```python
# generate_daily_report.py
import json
from pathlib import Path

services = Path("services").glob("*/coverage.json")
total_pct = []
for svc in services:
    data = json.loads(svc.read_text())
    total_pct.append(data["totals"]["percent_covered"])

print(f"Backend Coverage: {sum(total_pct)/len(total_pct):.2f}%")
```

---

## CURRENT ACTION

**Iniciando TIER 1:**
1. api_gateway - analysis
2. maximus_core_service - analysis
3. osint_service - analysis

**Target:** 3 services @ 100% até fim do dia.
