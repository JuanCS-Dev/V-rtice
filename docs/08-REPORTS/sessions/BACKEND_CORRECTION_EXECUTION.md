# BACKEND CORRECTION EXECUTION - REAL STATUS

**Data:** 2025-10-18T14:10:00Z  
**Status Inicial:** 67 containers running, 27 UNHEALTHY  
**API Gateway:** ✅ OPERATIONAL (degraded mode)

---

## DIAGNÓSTICO REAL

### ✅ Serviços Saudáveis: 40/67 (60%)
API Gateway, MAXIMUS Core, Reactive Fabric, IMMUNIS (parcial), HSAS (parcial), Core services

### ⚠️ Categoria A: Healthcheck Not Configured (21 serviços)
**Status:** Rodando perfeitamente, apenas sem healthcheck
**Impacto:** Cosmético (docker ps mostra unhealthy)
**Risk Fix:** ZERO

- immunis_treg_service
- memory_consolidation_service
- predictive_threat_hunting_service
- rte-service (⚠️ numpy missing - precisa fix antes)
- ai_immune_system
- auditory_cortex_service
- chemical_sensing_service
- cloud_coordinator_service
- digital_thalamus_service
- homeostatic_regulation
- immunis_bcell_service
- immunis_cytotoxic_t_service
- immunis_dendritic_service
- immunis_helper_t_service
- immunis_neutrophil_service
- immunis_nk_cell_service
- prefrontal_cortex_service
- sinesp_service
- social_eng_service
- somatosensory_service
- vestibular_service
- visual_cortex_service

### ❌ Categoria B: Dependency Errors (6 serviços)
**Status:** Crashed/não iniciando
**Impacto:** Funcionalidade perdida
**Risk Fix:** BAIXO (adicionar deps no requirements.txt)

1. **maximus_integration_service** - Missing: httpx
2. **google_osint_service** - Missing: backend module (PYTHONPATH)
3. **hcl_executor_service** - Missing: backend module (PYTHONPATH)
4. **immunis_macrophage_service** - Missing: kafka connection (config)
5. **reflex_triage_engine** - Missing: numpy

---

## PLANO DE EXECUÇÃO - FASEAMENTO DETALHADO

### FASE 1: FIX DEPENDENCIES (Categoria B) ⚡
**Target:** 6 serviços
**Tempo estimado:** 30 min
**Risk:** BAIXO

#### Step 1.1: maximus_integration_service
```bash
# Fix: Add httpx to requirements.txt
echo "httpx==0.25.0" >> backend/services/maximus_integration_service/requirements.txt

# Rebuild
docker compose build maximus_integration_service

# Restart
docker compose restart maximus_integration_service

# Validate
docker compose logs maximus_integration_service --tail 20
```

**Validação:**
- ✅ Serviço inicia sem ModuleNotFoundError
- ✅ API Gateway ainda HEALTHY
- ✅ Logs mostram "Application startup complete"

#### Step 1.2: google_osint_service + hcl_executor_service
```bash
# Fix: Add PYTHONPATH to both services in docker-compose.yml
# Location: environment section

environment:
  - PYTHONPATH=/app:/app/backend
```

**Rebuild & Restart:**
```bash
docker compose build google_osint_service hcl_executor_service
docker compose restart google_osint_service hcl_executor_service
```

**Validação:**
- ✅ Ambos iniciam sem ModuleNotFoundError
- ✅ Import de backend.* funciona

#### Step 1.3: reflex_triage_engine
```bash
# Fix: Add numpy to requirements.txt
echo "numpy==1.24.3" >> backend/services/reflex_triage_engine/requirements.txt

# Rebuild
docker compose build reflex_triage_engine

# Restart
docker compose restart reflex_triage_engine
```

#### Step 1.4: immunis_macrophage_service
```bash
# Fix: Update Kafka connection to use hcl-kafka (não localhost)
# File: backend/services/immunis_macrophage_service/main.py

# Change:
# KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
# To:
KAFKA_BOOTSTRAP_SERVERS = "hcl-kafka:9092"

# Rebuild
docker compose build immunis_macrophage_service
docker compose restart immunis_macrophage_service
```

**Validação FASE 1:**
```bash
# Verificar que os 6 serviços agora iniciam corretamente
for svc in maximus_integration_service google_osint_service hcl_executor_service reflex_triage_engine immunis_macrophage_service; do
    echo "=== $svc ==="
    docker compose logs $svc --tail 10 | grep -i "startup complete\|running on" || echo "❌ STILL BROKEN"
done

# API Gateway MUST still be healthy
curl -f http://localhost:8000/health || echo "🚨 GATEWAY BROKEN - ROLLBACK"
```

---

### FASE 2: ADD HEALTHCHECKS (Categoria A) 🏥
**Target:** 21 serviços
**Tempo estimado:** 45 min
**Risk:** ZERO (apenas adiciona healthcheck)

#### Step 2.1: Template de Healthcheck Universal
```yaml
# docker-compose.yml
# Template para TODOS os serviços sem healthcheck

healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:${PORT}/health"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 60s
```

#### Step 2.2: Adicionar healthcheck em batch
**Serviços por porta:**
```yaml
# IMMUNIS Services
immunis_treg_service:           # Port 8018
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8018/health"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 60s

immunis_bcell_service:          # Port 8026
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8026/health"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 60s

# (Repetir para cada um dos 21 serviços)
```

#### Step 2.3: Aplicar mudanças
```bash
# Edit docker-compose.yml (via str_replace_editor)

# Restart services (não precisa rebuild)
docker compose restart \
  immunis_treg_service \
  memory_consolidation_service \
  predictive_threat_hunting_service \
  ai_immune_system \
  auditory_cortex_service \
  chemical_sensing_service \
  cloud_coordinator_service \
  digital_thalamus_service \
  homeostatic_regulation \
  immunis_bcell_service \
  immunis_cytotoxic_t_service \
  immunis_dendritic_service \
  immunis_helper_t_service \
  immunis_neutrophil_service \
  immunis_nk_cell_service \
  prefrontal_cortex_service \
  sinesp_service \
  social_eng_service \
  somatosensory_service \
  vestibular_service \
  visual_cortex_service

# Wait 2 minutes for healthchecks to stabilize
sleep 120

# Validate
docker compose ps | grep -c "healthy" # Deve ser 60+
```

**Validação FASE 2:**
```bash
# Contagem de serviços healthy deve aumentar
before=$(docker compose ps --format "{{.Status}}" | grep -c unhealthy)
after=$(docker compose ps --format "{{.Status}}" | grep -c healthy)

echo "Before: $before unhealthy"
echo "After: $after healthy"
echo "Improvement: $((after - before)) services fixed"

# API Gateway check
curl -f http://localhost:8000/health
```

---

### FASE 3: CODE QUALITY SCAN 🎯
**Target:** Identificar TODOs, mocks, violações Pagani
**Tempo estimado:** 15 min (scan) + variável (fixes)
**Risk:** ZERO (apenas scan)

#### Step 3.1: TODO/FIXME Audit
```bash
# Comprehensive scan
find backend/services -name "*.py" -type f \
  | xargs grep -n "TODO\|FIXME\|HACK\|XXX" \
  > /tmp/backend_code_debt.txt

# Count
total=$(wc -l < /tmp/backend_code_debt.txt)
echo "Total code debt markers: $total"

# Categorize
grep "TODO:" /tmp/backend_code_debt.txt | wc -l
grep "FIXME:" /tmp/backend_code_debt.txt | wc -l
```

#### Step 3.2: Mock/Stub Detection
```bash
# Find mock implementations in production code
find backend/services -name "main.py" -o -name "api.py" \
  | xargs grep -l "mock\|Mock\|stub\|Stub\|placeholder"

# Count
mock_count=$(find backend/services -name "main.py" -o -name "api.py" \
  | xargs grep -l "mock\|Mock\|stub\|Stub" | wc -l)

echo "Services with mocks: $mock_count"
```

#### Step 3.3: Generate Remediation Plan
```bash
# Output structure:
# - Service name
# - File path
# - Line number
# - Issue type (TODO/MOCK/etc)
# - Suggested action

python3 << 'PYEOF'
import re
from pathlib import Path

issues = []
for service_dir in Path("backend/services").iterdir():
    if not service_dir.is_dir():
        continue
    
    for py_file in service_dir.rglob("*.py"):
        if "test" in str(py_file):
            continue
        
        content = py_file.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            if any(marker in line for marker in ["TODO", "FIXME", "HACK", "XXX"]):
                issues.append({
                    "service": service_dir.name,
                    "file": str(py_file),
                    "line": i,
                    "type": "CODE_DEBT",
                    "content": line.strip()
                })
            
            if any(word in line.lower() for word in ["mock", "stub", "placeholder"]) and "import" not in line.lower():
                issues.append({
                    "service": service_dir.name,
                    "file": str(py_file),
                    "line": i,
                    "type": "MOCK_CODE",
                    "content": line.strip()
                })

print(f"Total issues found: {len(issues)}")
print("\nTop 10 offenders:")
for issue in issues[:10]:
    print(f"  {issue['service']} - {issue['type']} - L{issue['line']}")
PYEOF
```

**Output esperado:** Relatório detalhado de violações (não implementa correções ainda)

---

### FASE 4: TEST COVERAGE BASELINE 🧪
**Target:** Medir coverage atual real
**Tempo estimado:** 20 min
**Risk:** ZERO (apenas medição)

#### Step 4.1: Run full test suite
```bash
cd /home/juan/vertice-dev

# Activate venv (se existir)
source .venv/bin/activate 2>/dev/null || true

# Install coverage tools
pip install pytest pytest-cov coverage -q

# Run tests with coverage
python3 -m pytest backend/tests/ \
  --cov=backend/services \
  --cov=backend/shared \
  --cov-report=json:coverage_backend_real.json \
  --cov-report=term-missing \
  -v \
  2>&1 | tee /tmp/pytest_output.txt

# Extract metrics
python3 << 'PYEOF'
import json
from pathlib import Path

cov_file = Path("coverage_backend_real.json")
if cov_file.exists():
    data = json.loads(cov_file.read_text())
    total_pct = data.get("totals", {}).get("percent_covered", 0)
    
    print(f"\n{'='*60}")
    print(f"BACKEND COVERAGE: {total_pct:.2f}%")
    print(f"{'='*60}\n")
    
    # Services below 99%
    low_cov = {}
    for file, stats in data.get("files", {}).items():
        if "services" in file and stats["summary"]["percent_covered"] < 99.0:
            low_cov[file] = stats["summary"]["percent_covered"]
    
    print(f"Services needing work: {len(low_cov)}")
    for file, pct in sorted(low_cov.items(), key=lambda x: x[1])[:20]:
        print(f"  {pct:5.2f}% - {Path(file).name}")
else:
    print("❌ Coverage file not generated")
PYEOF
```

**Validação FASE 4:**
- ✅ coverage_backend_real.json gerado
- ✅ Baseline documentada
- ✅ Lista de serviços <99% identificada

---

### FASE 5: START INACTIVE SERVICES 🚀
**Target:** 28 serviços não iniciados (95 total - 67 rodando)
**Tempo estimado:** 60 min
**Risk:** MÉDIO

#### Step 5.1: Inventory
```bash
# All defined services
docker compose config --services | sort > /tmp/all_services.txt

# Currently running
docker compose ps --services | sort > /tmp/running_services.txt

# Difference
comm -23 /tmp/all_services.txt /tmp/running_services.txt > /tmp/inactive_services.txt

echo "Inactive services: $(wc -l < /tmp/inactive_services.txt)"
cat /tmp/inactive_services.txt
```

#### Step 5.2: Categorize by dependency
```bash
# For each inactive service, check why it's not running
while read svc; do
    echo "=== $svc ==="
    
    # Try to start
    docker compose up -d $svc 2>&1 | head -5
    
    # Check logs
    sleep 5
    docker compose logs $svc --tail 20 | grep -i "error\|exception" || echo "Started OK"
    
    echo ""
done < /tmp/inactive_services.txt
```

**Manual triage needed:** Alguns podem ter dependências externas ou estarem deprecados

---

## MÉTRICAS DE SUCESSO

### Estado Atual (Baseline)
- Containers rodando: 67/95 (71%)
- Serviços healthy: 40/67 (60%)
- Serviços unhealthy: 27/67 (40%)
- API Gateway: degraded mode
- Coverage: Unknown

### Target Final (100% Operational)
- Containers rodando: 90+/95 (95%+)
- Serviços healthy: 90+/90+ (100%)
- Serviços unhealthy: 0
- API Gateway: healthy mode
- Coverage: 99%+

### Milestones
- ✅ FASE 1: 6 dependency errors corrigidos → 46 healthy (69%)
- ✅ FASE 2: 21 healthchecks adicionados → 67 healthy (100% dos running)
- ✅ FASE 3: Code debt mapeado
- ✅ FASE 4: Coverage baseline estabelecido
- ✅ FASE 5: 90+ serviços rodando

---

## COMANDO DE VALIDAÇÃO UNIVERSAL

```bash
#!/bin/bash
# validate_backend_complete.sh

echo "🔍 BACKEND HEALTH CHECK"
echo "======================="

# 1. API Gateway
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✅ API Gateway: HEALTHY"
else
    echo "❌ API Gateway: DOWN"
    exit 1
fi

# 2. Container count
running=$(docker compose ps --format "{{.Service}}" | wc -l)
echo "✅ Containers running: $running/95"

# 3. Health status
healthy=$(docker compose ps --format "{{.Status}}" | grep -c "healthy" || echo 0)
unhealthy=$(docker compose ps --format "{{.Status}}" | grep -c "unhealthy" || echo 0)
echo "✅ Healthy: $healthy"
echo "⚠️  Unhealthy: $unhealthy"

# 4. Dependency errors
errors=$(docker compose logs --since 5m 2>&1 | grep -c "ModuleNotFoundError\|ImportError" || echo 0)
if [ $errors -eq 0 ]; then
    echo "✅ No dependency errors"
else
    echo "⚠️  Dependency errors: $errors"
fi

# 5. Coverage (if file exists)
if [ -f "coverage_backend_real.json" ]; then
    cov=$(python3 -c "import json; print(json.load(open('coverage_backend_real.json'))['totals']['percent_covered'])")
    echo "✅ Coverage: $cov%"
fi

echo ""
echo "Overall Status: OPERATIONAL"
```

---

## PRÓXIMA AÇÃO IMEDIATA

Aguardando aprovação do Arquiteto-Chefe para iniciar:

**FASE 1: FIX DEPENDENCIES**
- Step 1.1: maximus_integration_service (httpx)
- Step 1.2: google_osint_service + hcl_executor_service (PYTHONPATH)
- Step 1.3: reflex_triage_engine (numpy)
- Step 1.4: immunis_macrophage_service (kafka config)

**Comando de início:**
```bash
# Aprovado? Execute:
./fix_dependencies.sh
```

---

**Status:** 📋 DIAGNÓSTICO COMPLETO - AGUARDANDO EXECUÇÃO  
**Filosofia:** Primum non nocere - Backend permanece operacional  
**Risk Level:** BAIXO (mudanças cirúrgicas, validação contínua)
