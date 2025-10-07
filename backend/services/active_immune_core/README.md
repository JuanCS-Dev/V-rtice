# 🛡️ Active Immune Core Service

Autonomous immune agents for real-time threat detection and neutralization.

**Version**: 1.0.0
**Authors**: Juan & Claude
**Status**: 🚧 Fase 1 - Foundation

---

## 📋 Overview

The **Active Immune Core Service** implements a biomimetic immune system with autonomous agents (Digital Macrophages, NK Cells, Neutrophils) that patrol the network, detect threats, and neutralize them in real-time.

Inspired by the human immune system, this service features:
- 🦠 **Autonomous Agents**: Self-directed patrol and threat hunting
- 🔥 **Homeostatic Regulation**: Dynamic activation based on threat level
- 🧬 **Clonal Selection**: Specialized agents for persistent threats
- 💬 **Cytokine Communication**: Fast, local coordination via Kafka
- 📡 **Hormonal Signaling**: Global broadcast via Redis
- 🧠 **Lymphnode Coordination**: Regional orchestration hubs
- 🔬 **Adaptive Immunity**: Somatic hypermutation for improved detection

---

## 🏗️ Architecture

```
Active Immune Core Service (Port 8200)
├── Agents (Autonomous)
│   ├── Digital Macrophages    # First responders, phagocytosis
│   ├── NK Cells                # Stress response, anomaly detection
│   └── Neutrophils             # Swarm behavior, NETs
│
├── Coordination
│   └── Lymphnodes              # Regional coordination hubs
│
├── Communication
│   ├── Cytokines (Kafka)       # Fast, local messaging
│   └── Hormones (Redis)        # Global broadcast
│
├── Homeostasis
│   └── Temperature Control     # Repouso → Vigilância → Atenção → Inflamação
│
└── Adaptive
    ├── Clonal Selection        # Specialized clones
    └── Affinity Maturation     # Somatic hypermutation
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- (Optional) Kubernetes cluster for production

### Local Development

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start dependencies (Kafka, Redis, PostgreSQL)
docker-compose -f docker-compose.dev.yml up -d

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run service
python -m uvicorn active_immune_core.main:app --reload --port 8200

# 5. Check health
curl http://localhost:8200/health

# 6. View metrics
curl http://localhost:8200/metrics

# 7. API documentation
open http://localhost:8200/docs
```

### Docker Deployment

```bash
# Build and run
docker-compose -f docker-compose.dev.yml up --build

# Check logs
docker logs -f active_immune_core

# Stop
docker-compose -f docker-compose.dev.yml down
```

---

## 📊 Monitoring

### Prometheus Metrics

Metrics available at `http://localhost:8200/metrics`:

- `immunis_agents_active` - Active agents by type and status
- `immunis_threats_detected_total` - Total threats detected
- `immunis_threats_neutralized_total` - Total threats neutralized
- `immunis_temperature_celsius` - Regional temperature
- `immunis_detection_latency_seconds` - Detection latency histogram
- `immunis_cytokines_sent_total` - Cytokines sent
- And 15+ more...

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (admin/admin):

- **Vital Signs Dashboard**: Temperature, heart rate, leukocyte count
- **Agent Metrics Dashboard**: Agent performance, detection rates
- **Lymphnode Dashboard**: Coordination metrics

---

## 🧪 Testing

**Current Status**: ✅ **155/155 tests passing (100% pass rate)**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=active_immune_core --cov-report=html

# Run specific test
pytest tests/test_health.py -v

# Run integration tests
pytest tests/integration/ -v

# Run refactoring tests (FASE 1+2)
pytest tests/test_validators.py tests/test_rate_limiter.py tests/test_thread_safe_structures.py tests/test_lymphnode.py -v
```

### Test Coverage by Module

| Module | Tests | Status | Coverage |
|--------|-------|--------|----------|
| Validators | 43 | ✅ 100% | Input validation, sanitization |
| Rate Limiter | 27 | ✅ 100% | Token bucket, clonal expansion |
| Thread-Safe Structures | 48 | ✅ 100% | Buffer, counters, temperature |
| Lymphnode | 37 | ✅ 100% | Coordination, homeostasis |
| **Total** | **155** | **✅ 100%** | **Refactoring complete** |

---

## 📦 Dependency Management

This service follows **strict dependency governance** to ensure security, stability, and reproducibility.

### Quick Reference

**Check for vulnerabilities**:
```bash
bash scripts/dependency-audit.sh
```

**Add new dependency**:
```bash
echo "package==1.2.3" >> requirements.txt
pip-compile requirements.txt --output-file requirements.txt.lock
bash scripts/dependency-audit.sh  # Verify no CVEs
git add requirements.txt requirements.txt.lock
git commit -m "feat: add package for feature X"
```

**Update dependency**:
```bash
vim requirements.txt  # Update version
pip-compile requirements.txt --output-file requirements.txt.lock --upgrade
bash scripts/dependency-audit.sh  # Verify no CVEs
git commit -am "chore(deps): update package to X.Y.Z"
```

### Policies & SLAs

All dependency management follows formal governance:

📋 **[DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md)** - Complete policy documentation

**Key SLAs**:
- **CRITICAL (CVSS >= 9.0)**: 24 hours
- **HIGH (CVSS >= 7.0)**: 72 hours
- **MEDIUM (CVSS >= 4.0)**: 2 weeks
- **LOW (CVSS < 4.0)**: 1 month

**Update Strategy**:
- **Patch (x.y.Z)**: Auto-merge if CI passes
- **Minor (x.Y.z)**: Manual review required
- **Major (X.y.z)**: RFC + breaking change analysis

### CVE Whitelist

If a CVE doesn't apply to our platform, whitelist it in `.cve-whitelist.yml`:

```yaml
whitelisted_cves:
  - id: CVE-2024-12345
    package: package==1.2.3
    cvss: 7.5
    justification: |
      Windows-only vulnerability, we run Linux exclusively
    expires_at: 2025-12-31
    owner: security-team
    approved_by: tech-lead
    approved_at: 2025-01-15
```

**Process**: Tech Lead + Security Team approval required

### Emergency Response

For **CRITICAL vulnerabilities (CVSS >= 9.0)**:

🚨 **[DEPENDENCY_EMERGENCY_RUNBOOK.md](./DEPENDENCY_EMERGENCY_RUNBOOK.md)**

**24-hour Response Timeline**:
- **Hour 0-2**: Containment
- **Hour 2-4**: Remediation
- **Hour 4-6**: Validation
- **Hour 6-8**: Phased Deployment

### Automation

**Dependabot**: Auto-creates PRs weekly (Mondays 00:00 UTC)
- Patch updates: Auto-merged if safe
- Minor/Major: Manual review

**GitHub Actions**:
- `dependabot-auto-approve.yml` - Auto-approval workflow
- `dependency-audit-weekly.yml` - Weekly CVE scans
- `dependency-alerts.yml` - Critical alerts (twice daily)

**Pre-commit Hooks**:
- CVE scanning (Safety + pip-audit)
- Drift detection
- Whitelist validation

### Available Scripts

| Script | Purpose |
|--------|---------|
| `dependency-audit.sh` | Full CVE scan |
| `check-cve-whitelist.sh` | Validate whitelist |
| `audit-whitelist-expiration.sh` | Check expired CVEs |
| `validate-deterministic-build.sh` | Verify reproducibility |
| `check-dependency-drift.sh` | Detect drift |
| `generate-dependency-metrics.sh` | Generate metrics JSON |

### Related Documents

- [DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md) - Formal governance
- [DEPENDENCY_EMERGENCY_RUNBOOK.md](./DEPENDENCY_EMERGENCY_RUNBOOK.MD) - Emergency procedures
- [DEPENDENCY_DRIFT_ELIMINATION_REPORT.md](./DEPENDENCY_DRIFT_ELIMINATION_REPORT.md) - Implementation report

---

## 📚 Documentation

- [Blueprint](../../../docs/11-ACTIVE-IMMUNE-SYSTEM/01-ACTIVE_IMMUNE_SYSTEM_BLUEPRINT.md) - Complete architectural design
- [Technical Architecture](../../../docs/11-ACTIVE-IMMUNE-SYSTEM/02-TECHNICAL_ARCHITECTURE.md) - Technical specs
- [Implementation Guide](../../../docs/11-ACTIVE-IMMUNE-SYSTEM/03-IMPLEMENTATION_GUIDE.md) - Code templates
- [Roadmap](../../../docs/11-ACTIVE-IMMUNE-SYSTEM/05-ROADMAP_IMPLEMENTATION.md) - 4-phase implementation plan

---

## 🛣️ Implementation Roadmap

### ✅ Fase 1: Fundação (Weeks 1-2) - COMPLETE
- [x] Service scaffolding
- [x] Communication layer (Kafka + Redis)
- [x] Base agent class
- [x] Macrophage implementation
- [x] NK Cell implementation
- [x] Neutrophil implementation
- [x] Agent factory
- [x] Swarm behavior

### ✅ Fase 1+2: Lymphnode Refactoring - COMPLETE (2025-10-07)
- [x] **Input Validation** - Pydantic models (6 types, 43 tests ✅)
- [x] **Rate Limiting** - Token bucket algorithm (27 tests ✅)
- [x] **Thread Safety** - 5 async structures (48 tests ✅)
- [x] **Exception Handling** - 12 custom exceptions
- [x] **Code Quality** - Path injection removed, 100% type hints
- [x] **Tests Updated** - 37 lymphnode tests (100% pass rate ✅)
- [x] **Documentation** - Complete final report

**Total**: 155/155 tests passing (100% pass rate) | 914 LOC infrastructure created

### ⏳ Fase 3: Desacoplamento (Next)
- [ ] Extract `IPatternDetector` interface
- [ ] Extract `ICytokineProcessor` interface
- [ ] Extract `IAgentOrchestrator` interface
- [ ] Extract `ITemperatureController` interface
- [ ] Extract `IMetricsCollector` interface
- [ ] Reduce lymphnode.py complexity (889 → ~300 lines)

### ⏳ Fase 4: Produção (Weeks 9-12)
- [ ] Kubernetes deployment
- [ ] Observability stack
- [ ] Documentation complete
- [ ] Load testing

---

## 🔧 Configuration

All configuration via environment variables (prefix: `ACTIVE_IMMUNE_`):

```bash
# Service
ACTIVE_IMMUNE_SERVICE_PORT=8200
ACTIVE_IMMUNE_LOG_LEVEL=INFO

# Kafka (Cytokines)
ACTIVE_IMMUNE_KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis (Hormones)
ACTIVE_IMMUNE_REDIS_URL=redis://localhost:6379

# PostgreSQL (Memory)
ACTIVE_IMMUNE_POSTGRES_HOST=localhost
ACTIVE_IMMUNE_POSTGRES_DB=immunis_memory

# Homeostasis
ACTIVE_IMMUNE_BASELINE_ACTIVE_PERCENTAGE=0.15  # 15% agents active (baseline)
ACTIVE_IMMUNE_TEMP_VIGILANCIA=37.5             # Vigilância temperature

# See .env.example for all options
```

---

## 🔒 Security

### Core Security Features
- ✅ **Ethical AI Validation**: All agent actions validated by Ethical AI Service (port 8612)
- ✅ **Fail-Safe**: Actions blocked on Ethical AI error (never fail open)
- ✅ **Non-Root Container**: Runs as user `immunis` (UID 1000)
- ✅ **Resource Limits**: Kubernetes resource quotas enforced
- ✅ **Input Validation**: Pydantic models for all inputs
- ✅ **Secrets Management**: Never commit `.env` files

### FASE 1+2 Security Enhancements ✅

**Input Validation & Sanitization**:
- ✅ 6 Pydantic models (Cytokine, Hormone, Apoptosis, Clonal, Temperature, Agent)
- ✅ String sanitization (removes `\x00`, `\n`, `<`, `>`, `;`, `&`, `|`)
- ✅ Range validation (priority 0-10, temperature ±5°C, level 0.0-1.0)
- ✅ Max lengths enforced (prevents buffer overflow)
- ✅ ISO timestamp validation

**Rate Limiting**:
- ✅ Token bucket algorithm (200 clones/minute global)
- ✅ Per-specialization limits (50 clones/type)
- ✅ Total agents cap (1000 maximum)
- ✅ DoS prevention via rate limiting
- ✅ Resource exhaustion prevention

**Thread Safety**:
- ✅ 5 thread-safe async structures (Buffer, Temperature, Counters)
- ✅ Race condition prevention (temperature updates, buffer appends, counter increments)
- ✅ `asyncio.Lock` for atomic operations
- ✅ CAS (Compare-And-Set) operations

**Exception Handling**:
- ✅ 12 custom exception types (replaced 11x generic `except Exception`)
- ✅ Specific error handling (RateLimit, Validation, Connection, ResourceExhausted, etc.)
- ✅ Graceful degradation (Redis/Kafka failures)

**Code Quality**:
- ✅ Path injection removed (`sys.path.insert()` eliminated)
- ✅ 0 TODOs/FIXMEs in refactored code
- ✅ 100% type hints
- ✅ Complete docstrings

**Documentation**: See [LYMPHNODE_REFACTOR_FINAL_REPORT.md](./coordination/LYMPHNODE_REFACTOR_FINAL_REPORT.md) for full details.

---

## 🤝 Contributing

This is a closed-source project. Internal contributions only.

---

## 📜 License

Proprietary - All rights reserved.

---

## 👥 Authors

- **Juan** - Concept, Architecture, Implementation
- **Claude** - Implementation, Documentation, Code Review

---

## 🙏 Acknowledgments

Inspired by:
- Human immune system (innate + adaptive immunity)
- Homeostatic control loops
- Swarm intelligence (Boids algorithm)
- Active inference (predictive coding)

---

**GOLDEN RULE COMPLIANCE**: ✅
- NO MOCK: All integrations use real services or graceful degradation
- NO PLACEHOLDER: Complete implementations only
- NO TODO: Zero TODOs in production code
- PRODUCTION-READY: Error handling, logging, metrics, tests
- QUALITY-FIRST: Type hints, docstrings, linting, security

---

**Next**: Implement Communication Layer (Cytokines via Kafka) - Fase 1.2
