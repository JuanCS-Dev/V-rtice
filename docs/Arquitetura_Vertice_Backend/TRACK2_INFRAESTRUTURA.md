# TRACK 2: INFRAESTRUTURA & AUTOMAÇÃO

**Executor:** Dev Sênior B  
**Especialidade:** DevOps, Docker, CI/CD, Observability  
**Duração:** 16 dias (Dias 1-16)  
**Branch:** `backend-transformation/track2-infra`

---

## MISSÃO

Criar toda a infraestrutura de suporte para o backend:
1. Port registry (Dias 1-3)
2. Scripts de automação (Dias 1-3)
3. CI/CD pipeline (Dias 4-8)
4. Observability stack (Dias 9-14)
5. Dashboards e alerting (Dias 15-16)

---

## ÁREA DE TRABALHO (Sem Conflitos)

```
backend/
├── ports.yaml                    # Você cria
├── scripts/                      # Você cria
│   ├── validate_ports.py
│   ├── generate_docker_compose.py
│   └── validate_phase.sh
.github/workflows/                # Você cria
├── validate-backend.yml
├── ci-services.yml
docker-compose.observability.yml  # Você cria
monitoring/                       # Você cria
├── prometheus.yml
├── grafana/
docs/adr/                         # Você cria
```

**Track 1 (libs):** NÃO TOCAR  
**Track 3 (services):** NÃO TOCAR

---

## DIA 1: Port Registry - Análise

### 1.1 Mapear Todos os Serviços (2h)

```bash
cd /home/juan/vertice-dev/backend/services

# Listar todos os serviços
ls -d */ | tee /tmp/all_services.txt
wc -l /tmp/all_services.txt
# EXPECTED: 83 services

# Categorizar por tipo
echo "=== MAXIMUS Family ===" > /tmp/service_categories.txt
ls -d maximus* >> /tmp/service_categories.txt
echo "" >> /tmp/service_categories.txt
echo "=== Immunis Family ===" >> /tmp/service_categories.txt
ls -d immunis* >> /tmp/service_categories.txt

cat /tmp/service_categories.txt
```

### 1.2 Detectar Conflitos Atuais (1h)

**Script de análise:**
```bash
#!/bin/bash
# Detectar portas hardcoded nos services

cd /home/juan/vertice-dev/backend/services

echo "Analyzing port usage..."
echo "====================="

for service in */; do
    service_name=${service%/}
    
    # Check main.py for port
    if [ -f "$service/main.py" ]; then
        port=$(grep -oP 'port=\K\d+' "$service/main.py" 2>/dev/null | head -1)
        if [ -n "$port" ]; then
            echo "$service_name: $port"
        fi
    fi
    
    # Check config.py
    if [ -f "$service/config.py" ]; then
        port=$(grep -oP 'PORT.*=\K\s*\d+' "$service/config.py" 2>/dev/null | head -1)
        if [ -n "$port" ]; then
            echo "$service_name: $port (config)"
        fi
    fi
done | sort -t: -k2 -n | tee /tmp/current_ports.txt

# Detect conflicts
echo ""
echo "=== PORT CONFLICTS ==="
cut -d: -f2 /tmp/current_ports.txt | sort | uniq -d
```

**Executar:**
```bash
chmod +x /tmp/analyze_ports.sh
/tmp/analyze_ports.sh
```

**EXPECTED OUTPUT:**
```
api_gateway: 8000
maximus_core: 8100
osint_service: 8300
...

=== PORT CONFLICTS ===
8000  (30+ services)
```

**Documentar resultados:**
```bash
cp /tmp/current_ports.txt docs/adr/001-port-analysis.txt
git add docs/adr/001-port-analysis.txt
git commit -m "docs: analyze current port usage and conflicts"
```

---

## DIA 2-3: Port Registry - Implementação

### 2.1 Criar Port Registry (Dia 2)

**`backend/ports.yaml`:**
```yaml
# Vértice MAXIMUS Service Port Registry
# Single source of truth for all service ports

metadata:
  version: "1.0.0"
  last_updated: "2025-10-16"
  total_services: 83
  port_ranges:
    core: "8000-8099"
    maximus: "8100-8199"
    immune: "8200-8299"
    intelligence: "8300-8399"
    offensive: "8400-8499"
    defensive: "8500-8599"
    
# Gateway and Core Services (8000-8099)
core:
  api_gateway: 8000

# MAXIMUS Family (8100-8199)
maximus:
  maximus_core: 8100
  consciousness_api: 8101
  governance_api: 8102
  ethical_guardian: 8103
  justice_engine: 8104
  mip_service: 8105
  autonomic_core: 8106
  federated_learning: 8107
  maximus_oraculo: 8108
  maximus_eureka: 8109
  maximus_integration: 8110
  maximus_orchestrator: 8111
  maximus_predict: 8112

# Immune System (8200-8299)
immune:
  active_immune_core: 8200
  adaptive_immune_system: 8201
  adaptive_immunity_db: 8202
  adaptive_immunity_service: 8203
  ai_immune_system: 8204
  immunis_api: 8205
  immunis_bcell: 8206
  immunis_cytotoxic_t: 8207
  immunis_dendritic: 8208
  immunis_helper_t: 8209
  immunis_macrophage: 8210
  immunis_neutrophil: 8211
  immunis_nk_cell: 8212
  immunis_treg: 8213

# Intelligence Services (8300-8399)
intelligence:
  osint_service: 8300
  threat_intel_service: 8301
  google_osint_service: 8302
  network_recon_service: 8303
  domain_service: 8304
  ip_intelligence_service: 8305
  vuln_intel_service: 8306
  cyber_service: 8307
  network_monitor_service: 8308
  ssl_monitor_service: 8309

# Offensive Services (8400-8499)
offensive:
  offensive_orchestrator: 8400
  offensive_gateway: 8401
  offensive_tools: 8402
  web_attack_service: 8403
  malware_analysis_service: 8404
  exploit_framework: 8405
  c2_orchestration: 8406

# Defensive Services (8500-8599)
defensive:
  reactive_fabric_core: 8500
  reactive_fabric_analysis: 8501
  reflex_triage_engine: 8502
  homeostatic_regulation: 8503
  bas_service: 8504
  rte_service: 8505

# Sensory & Perception (8600-8699)
sensory:
  auditory_cortex: 8600
  visual_cortex: 8601
  somatosensory: 8602
  chemical_sensing: 8603
  vestibular: 8604
  tegumentar: 8605

# Cognition & Planning (8700-8799)
cognition:
  prefrontal_cortex: 8700
  digital_thalamus: 8701
  attention_system: 8702
  memory_consolidation: 8703
  neuromodulation: 8704
  predictive_coding: 8705
  skill_learning: 8706

# Higher-Order Functions (8800-8899)
higher_order:
  hcl_analyzer: 8800
  hcl_planner: 8801
  hcl_executor: 8802
  hcl_kb: 8803
  hcl_monitor: 8804
  strategic_planning: 8805
  autonomous_investigation: 8806
  narrative_analysis: 8807
  narrative_manipulation_filter: 8808

# Support Services (8900-8999)
support:
  auth_service: 8900
  atlas_service: 8901
  agent_communication: 8902
  sinesp_service: 8903
  hitl_patch: 8904
  cloud_coordinator: 8905
  edge_agent: 8906
  hpc_service: 8907
  ethical_audit: 8908
  adr_core: 8909

# Wargaming & Testing (9000-9099)
wargaming:
  wargaming_crisol: 9000
  mock_vulnerable_apps: 9001
  tataca_ingestion: 9002
  seriema_graph: 9003
  purple_team: 9004
  predictive_threat_hunting: 9005
  social_eng_service: 9006
  vuln_scanner_service: 9007
  hsas_service: 9008

# Special Services
special:
  api_docs_portal: 9100
```

**Validar completude:**
```bash
cd /home/juan/vertice-dev/backend

# Count services in YAML
python3 << 'PY_EOF'
import yaml
with open('ports.yaml') as f:
    data = yaml.safe_load(f)

count = sum(len(svcs) for k, svcs in data.items() if k != 'metadata')
expected = data['metadata']['total_services']

print(f"Services in YAML: {count}")
print(f"Expected: {expected}")

if count != expected:
    print(f"❌ MISMATCH! Update metadata.total_services to {count}")
    exit(1)
else:
    print("✅ Count matches")
PY_EOF
```

**Commit:**
```bash
git add ports.yaml
git commit -m "feat(infra): add complete port registry for 83 services"
```

---

### 2.2 Criar Script de Validação (Dia 2)

**`scripts/validate_ports.py`** (Production-ready):
```python
#!/usr/bin/env python3
"""Validate port registry for conflicts, completeness, and correctness.

This script performs comprehensive validation of backend/ports.yaml:
- No port conflicts (all unique)
- Ports within correct ranges per category
- All services from filesystem are mapped
- No mapped services missing from filesystem

Exit codes:
    0: All validations passed
    1: Validation errors found

Usage:
    python scripts/validate_ports.py
    
    # CI integration
    python scripts/validate_ports.py || exit 1
"""

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def load_registry() -> dict[str, Any]:
    """Load port registry YAML.
    
    Returns:
        Parsed YAML data
        
    Raises:
        SystemExit: If file not found or invalid YAML
    """
    registry_path = Path(__file__).parent.parent / "backend" / "ports.yaml"
    
    if not registry_path.exists():
        print(f"❌ Port registry not found: {registry_path}")
        sys.exit(1)
    
    try:
        with open(registry_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML: {e}")
        sys.exit(1)


def validate_uniqueness(registry: dict[str, Any]) -> list[str]:
    """Check that all ports are unique (no conflicts).
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages (empty if no errors)
    """
    errors = []
    seen_ports: dict[int, str] = {}
    
    for category, services in registry.items():
        if category == "metadata":
            continue
        
        if not isinstance(services, dict):
            errors.append(f"❌ Category '{category}' must be dict, got {type(services).__name__}")
            continue
        
        for service_name, port in services.items():
            if not isinstance(port, int):
                errors.append(
                    f"❌ {category}.{service_name}: port must be int, got {type(port).__name__}"
                )
                continue
            
            if port in seen_ports:
                errors.append(
                    f"⚠️  PORT CONFLICT: {category}.{service_name}:{port} "
                    f"conflicts with {seen_ports[port]}:{port}"
                )
            
            seen_ports[port] = f"{category}.{service_name}"
    
    return errors


def validate_ranges(registry: dict[str, Any]) -> list[str]:
    """Check that ports are within correct ranges per category.
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages
    """
    errors = []
    
    # Expected ranges per category
    ranges: dict[str, tuple[int, int]] = {
        "core": (8000, 8099),
        "maximus": (8100, 8199),
        "immune": (8200, 8299),
        "intelligence": (8300, 8399),
        "offensive": (8400, 8499),
        "defensive": (8500, 8599),
        "sensory": (8600, 8699),
        "cognition": (8700, 8799),
        "higher_order": (8800, 8899),
        "support": (8900, 8999),
        "wargaming": (9000, 9099),
        "special": (9100, 9199),
    }
    
    for category, services in registry.items():
        if category == "metadata":
            continue
        
        if category not in ranges:
            errors.append(f"⚠️  Unknown category: '{category}'")
            continue
        
        if not isinstance(services, dict):
            continue
        
        min_port, max_port = ranges[category]
        
        for service_name, port in services.items():
            if not isinstance(port, int):
                continue
            
            if not (min_port <= port <= max_port):
                errors.append(
                    f"⚠️  {category}.{service_name}:{port} outside range "
                    f"({min_port}-{max_port})"
                )
    
    return errors


def validate_completeness(registry: dict[str, Any]) -> list[str]:
    """Check that all filesystem services are mapped.
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages
    """
    errors = []
    services_dir = Path(__file__).parent.parent / "backend" / "services"
    
    if not services_dir.exists():
        return [f"⚠️  Services directory not found: {services_dir}"]
    
    # Get actual services from filesystem
    actual_services = {
        d.name for d in services_dir.iterdir()
        if d.is_dir() and not d.name.startswith(('.', '_'))
    }
    
    # Get mapped services from YAML
    mapped_services = set()
    for category, services in registry.items():
        if category == "metadata" or not isinstance(services, dict):
            continue
        mapped_services.update(services.keys())
    
    # Find unmapped
    unmapped = actual_services - mapped_services
    if unmapped:
        errors.append(
            f"⚠️  Services in filesystem but NOT in ports.yaml:\n"
            f"    {', '.join(sorted(unmapped))}"
        )
    
    # Find non-existent
    nonexistent = mapped_services - actual_services
    if nonexistent:
        errors.append(
            f"⚠️  Services in ports.yaml but NOT in filesystem:\n"
            f"    {', '.join(sorted(nonexistent))}"
        )
    
    return errors


def validate_metadata(registry: dict[str, Any]) -> list[str]:
    """Validate metadata section.
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages
    """
    errors = []
    
    if "metadata" not in registry:
        errors.append("⚠️  Missing 'metadata' section")
        return errors
    
    meta = registry["metadata"]
    
    # Count actual services
    actual_count = sum(
        len(svcs) for k, svcs in registry.items()
        if k != "metadata" and isinstance(svcs, dict)
    )
    
    declared_count = meta.get("total_services", 0)
    
    if actual_count != declared_count:
        errors.append(
            f"⚠️  Metadata count mismatch: declared {declared_count}, "
            f"actual {actual_count}"
        )
    
    return errors


def main() -> int:
    """Run all validation checks.
    
    Returns:
        0 if all validations pass, 1 otherwise
    """
    print("🔍 Validating Port Registry\n")
    print("=" * 60)
    
    try:
        registry = load_registry()
    except SystemExit:
        return 1
    
    all_errors = []
    
    # Run checks
    print("\n1️⃣  Checking port uniqueness...")
    errors = validate_uniqueness(registry)
    if errors:
        all_errors.extend(errors)
    else:
        print("   ✅ No port conflicts")
    
    print("\n2️⃣  Checking port ranges...")
    errors = validate_ranges(registry)
    if errors:
        all_errors.extend(errors)
    else:
        print("   ✅ All ports in correct ranges")
    
    print("\n3️⃣  Checking completeness...")
    errors = validate_completeness(registry)
    if errors:
        all_errors.extend(errors)
    else:
        print("   ✅ All services mapped")
    
    print("\n4️⃣  Checking metadata...")
    errors = validate_metadata(registry)
    if errors:
        all_errors.extend(errors)
    else:
        total = registry["metadata"]["total_services"]
        print(f"   ✅ Metadata correct ({total} services)")
    
    # Report results
    print("\n" + "=" * 60)
    if all_errors:
        print(f"\n❌ VALIDATION FAILED ({len(all_errors)} errors)\n")
        for error in all_errors:
            print(error)
        return 1
    
    print("\n✅ PORT REGISTRY VALID")
    print(f"   Total services: {registry['metadata']['total_services']}")
    print(f"   No conflicts detected")
    print(f"   All ranges correct\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Tornar executável:**
```bash
chmod +x scripts/validate_ports.py
```

**Testar:**
```bash
cd /home/juan/vertice-dev/backend
python scripts/validate_ports.py
```

**EXPECTED:**
```
✅ PORT REGISTRY VALID
   Total services: 83
```

**Commit:**
```bash
git add scripts/validate_ports.py
git commit -m "feat(infra): add port registry validation script"
```

---

### 2.3 Script de Geração Docker Compose (Dia 3)

(Similar ao exemplo anterior, completo e production-ready)

---

### 2.4 CI Básico (Dia 3)

**`.github/workflows/validate-backend.yml`:**
```yaml
name: Validate Backend Infrastructure

on:
  pull_request:
    paths:
      - 'backend/ports.yaml'
      - 'backend/scripts/**'
  push:
    branches: [main, develop]
    paths:
      - 'backend/ports.yaml'

jobs:
  validate-ports:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install pyyaml
      
      - name: Validate port registry
        run: |
          cd backend
          python scripts/validate_ports.py
```

**Commit:**
```bash
git add .github/workflows/validate-backend.yml
git commit -m "ci: add port registry validation workflow"
```

---

## VALIDAÇÃO DIA 1-3

```bash
# Checklist
[ ] Port registry com 83 serviços
[ ] validate_ports.py implementado
[ ] validate_ports.py passa
[ ] CI workflow criado
[ ] ADR-001 documentado
[ ] Zero conflitos de porta
```

**Gate 1 PASS → Notificar Track 1 para iniciar**

---

## DIAS 4-8: CI/CD Pipeline

(Implementação completa de workflow multiservice, matrix builds, etc)

---

## DIAS 9-14: Observability Stack

**Deliverables:**
- Jaeger (distributed tracing)
- Prometheus (metrics)
- Grafana (dashboards)
- Loki (log aggregation)

---

## DIAS 15-16: Dashboards & Alerting

**Deliverables:**
- 5 Grafana dashboards
- Prometheus alerts
- Documentation

---

## VALIDAÇÃO FINAL TRACK 2

```bash
# Port registry
python scripts/validate_ports.py || exit 1

# CI working
gh workflow run validate-backend.yml

# Observability stack up
docker-compose -f docker-compose.observability.yml up -d
curl http://localhost:16686/api/services  # Jaeger
curl http://localhost:9090/-/healthy      # Prometheus
curl http://localhost:3001/api/health     # Grafana

echo "✅ TRACK 2 COMPLETO"
```

**Entregáveis:**
- [ ] Port registry validado
- [ ] CI/CD funcional
- [ ] Observability stack operacional
- [ ] Documentação completa
- [ ] PR aberto

---

**PRÓXIMO PASSO:** Notificar Track 3 que infraestrutura está pronta
