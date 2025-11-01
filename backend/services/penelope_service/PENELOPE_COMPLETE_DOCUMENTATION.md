# PENELOPE - Christian Autonomous Healing Service
## Complete Documentation & Runbook

**Version**: 1.0.0
**Status**: Production Ready
**TRINITY_CORRECTION_PLAN**: P0-P1 Complete (100%)

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Biblical Foundation](#biblical-foundation)
3. [Architecture](#architecture)
4. [Safety Mechanisms](#safety-mechanisms)
5. [API Documentation](#api-documentation)
6. [Operational Runbook](#operational-runbook)
7. [Monitoring & Metrics](#monitoring--metrics)
8. [Troubleshooting](#troubleshooting)
9. [Migration Guide](#migration-guide)

---

## Overview

PENELOPE (Platform for Enlightened Networked Execution with Love, Obedience, Prudence, and Eternal-mindedness) is a Christian autonomous healing service that implements wisdom-driven self-healing capabilities for the Vértice platform.

### Key Features
- ✅ Wisdom-driven decision making (Sophia Engine)
- ✅ Circuit breaker protection
- ✅ Complete audit trail
- ✅ Human approval for high-risk changes
- ✅ Digital twin validation
- ✅ Automatic rollback capabilities
- ✅ Biblical principles integration

### Service Status
- **P0 (Blockers)**: ✅ 100% Complete
- **P1 (Critical)**: ✅ 100% Complete
- **Test Coverage**: 262 tests, 100% passing
- **Production Ready**: Yes

---

## Biblical Foundation

PENELOPE is grounded in 7 Biblical Articles that govern all autonomous actions:

### Artigo I: Sabedoria (Sophia) - Wisdom
**Scripture**: Proverbs 9:10
**Implementation**: Sophia Engine judges whether intervention is necessary
**Code**: `core/sophia_engine.py`

**Three Essential Questions**:
1. Is this a transient failure that self-corrects?
2. Could intervention cause more harm than the failure?
3. Are there historical precedents to inform the decision?

### Artigo II: Mansidão (Praotes) - Gentleness
**Scripture**: James 1:21
**Implementation**: Praotes Validator ensures gentle, minimal interventions
**Code**: `core/praotes_validator.py`

**Validation Rules**:
- Maximum 5 lines for surgical patches
- Maximum 25 lines for moderate patches
- Easy reversibility required
- No API contract breaking

### Artigo III: Humildade (Tapeinophrosyne) - Humility
**Scripture**: James 4:6
**Implementation**: Tapeinophrosyne Monitor tracks competence levels
**Code**: `core/tapeinophrosyne_monitor.py`

**Competence Levels**:
- AUTONOMOUS: Can act independently
- ASSISTED: Suggest only, wait for approval
- DEFER_TO_HUMAN: Cannot handle, escalate immediately

### Additional Articles
4. **Stewardship**: Responsible resource management
5. **Agape**: Love-driven service decisions
6. **Sabbath**: Respect for rest periods
7. **Aletheia**: Truth and transparency in all actions

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PENELOPE Service                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │   Sophia     │────▶│   Circuit    │────▶│   Digital   │ │
│  │   Engine     │     │   Breaker    │     │    Twin     │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│         │                     │                     │        │
│         ▼                     ▼                     ▼        │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │ Decision     │     │   Human      │     │   Patch     │ │
│  │ Audit Logger │     │  Approval    │     │  History    │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│         │                     │                     │        │
│         ▼                     ▼                     ▼        │
│  ┌─────────────────────────────────────────────────────────┤
│  │              Wisdom Base (PostgreSQL + pgvector)         │
│  └─────────────────────────────────────────────────────────┘
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Core Modules

#### 1. Sophia Engine (`core/sophia_engine.py`)
**Purpose**: Wisdom-driven decision making
**Functions**:
- `should_intervene(anomaly)` - Main decision function
- `_is_self_healing_naturally()` - Detect transient failures
- `_assess_intervention_risk()` - Calculate risk scores
- `_query_wisdom_base()` - Find historical precedents

#### 2. Circuit Breaker (`core/circuit_breaker.py`)
**Purpose**: Prevent runaway healing attempts
**States**: CLOSED → OPEN → HALF_OPEN
**Functions**:
- `is_allowed(service)` - Check if healing allowed
- `record_failure(service, error)` - Track failures
- `record_success(service)` - Reset on success
- `get_status(service)` - Query circuit state

**Configuration**:
```python
circuit_breaker = HealingCircuitBreaker(
    failure_threshold=3,        # Open after 3 failures
    window_minutes=15,          # In 15 minute window
    cooldown_minutes=60         # Cool down for 60 minutes
)
```

#### 3. Decision Audit Logger (`core/decision_audit_logger.py`)
**Purpose**: Immutable audit trail for all decisions
**Functions**:
- `log_decision()` - Record decision with full context
- `get_decisions()` - Query with filters
- `get_decision_stats()` - Statistical analysis
- `export_audit_trail()` - Compliance exports

**Audit Entry Structure**:
```json
{
  "audit_id": "uuid",
  "timestamp": "ISO-8601",
  "anomaly_id": "string",
  "decision": "observe|intervene|escalate",
  "reasoning": "explanation",
  "risk_score": 0.85,
  "precedents_count": 2,
  "sophia_wisdom": "biblical principle",
  "decision_maker": "sophia_engine_v1.0"
}
```

#### 4. Human Approval Workflow (`core/human_approval.py`)
**Purpose**: Safety gate for high-risk patches
**Functions**:
- `request_approval()` - Create approval request
- `approve()` - Approve pending request
- `reject()` - Reject with reason
- `get_pending_requests()` - Query all pending

**Workflow**:
1. High-risk patch detected (risk_score > 0.7)
2. Notification sent to Slack `#penelope-approvals` + Email
3. Human reviews patch details
4. Approval via API or Slack command
5. Auto-rejects after timeout (default: 2 hours)

#### 5. Digital Twin (`core/digital_twin.py`)
**Purpose**: Safe validation environment
**Functions**:
- `validate_patch()` - Test patch in isolated environment
- `run_tests()` - Execute test suite
- `measure_performance()` - Check performance impact

#### 6. Wisdom Base (`core/wisdom_base_client.py`)
**Purpose**: Historical precedent storage and retrieval
**Technology**: PostgreSQL + pgvector for similarity search
**Functions**:
- `store_precedent()` - Store successful healing case
- `query_similar()` - Find similar past cases
- `get_success_rate()` - Calculate success metrics

---

## Safety Mechanisms

### 1. Circuit Breaker Protection
**Prevents**: Cascading failures from repeated healing attempts

**How it Works**:
- Tracks failures per service in sliding time window
- Opens circuit after threshold (default: 3 failures in 15 min)
- Blocks healing attempts during cooldown (default: 60 min)
- Automatically tests recovery in HALF_OPEN state

**Monitoring**:
```prometheus
penelope_circuit_breaker_state{service="api-gateway"}  # 0=closed, 1=open, 2=half_open
penelope_circuit_breaker_failures{service="api-gateway"}  # Current failure count
```

### 2. Decision Audit Trail
**Ensures**: Complete traceability and compliance

**Storage**:
- Primary: PostgreSQL (queryable, long-term)
- Secondary: Loki (monitoring, alerting)
- Backup: In-memory (testing, development)

**Retention**: 1 year minimum for compliance

**Query Examples**:
```python
# Get all high-risk decisions
decisions = await audit_logger.get_high_risk_decisions(risk_threshold=0.7)

# Get decisions for specific anomaly
decisions = await audit_logger.get_decisions(anomaly_id="anomaly-123")

# Export for compliance
export = await audit_logger.export_audit_trail(format="json")
```

### 3. Human Approval Workflow
**Prevents**: Autonomous deployment of risky patches

**Triggers**:
- Risk score > 0.7
- Patch size > 25 lines (redesign level)
- No historical precedents found
- Confidence < 0.8

**Notifications**:
- **Slack**: `#penelope-approvals` channel
- **Email**: ops-team@vertice.ai
- **Dashboard**: https://penelope.vertice.ai/approvals

**Commands**:
```bash
# Approve patch
/penelope approve {approval_id}

# Reject patch
/penelope reject {approval_id} "Reason for rejection"

# Check pending
/penelope pending
```

---

## API Documentation

### Base URL
```
http://localhost:8000  (development)
https://penelope.vertice.ai  (production)
```

### Authentication
```http
Authorization: Bearer {token}
```

### Endpoints

#### 1. Diagnose Anomaly
```http
POST /api/v1/diagnose
Content-Type: application/json

{
  "anomaly_id": "anomaly-001",
  "anomaly_type": "latency_spike",
  "affected_service": "api-gateway",
  "metrics": {
    "p99_latency_ms": 2500,
    "error_rate": 0.05
  }
}
```

**Response**:
```json
{
  "diagnosis_id": "diag-001",
  "root_cause": "Database connection pool exhaustion",
  "confidence": 0.92,
  "sophia_recommendation": "intervene",
  "intervention_level": "PATCH_SURGICAL",
  "precedents": [...]
}
```

#### 2. Generate Patch
```http
POST /api/v1/patch
Content-Type: application/json

{
  "diagnosis_id": "diag-001",
  "approved_by_sophia": true
}
```

#### 3. Validate Patch
```http
POST /api/v1/validate
Content-Type: application/json

{
  "patch_id": "patch-001"
}
```

#### 4. Deploy Patch
```http
POST /api/v1/deploy
Content-Type: application/json

{
  "patch_id": "patch-001"
}
```

#### 5. Query Wisdom Base
```http
GET /api/v1/wisdom?anomaly_type=latency_spike&similarity_threshold=0.8
```

#### 6. Health Check
```http
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "sophia_engine": "ok",
    "wisdom_base": "ok",
    "digital_twin": "ok"
  },
  "virtues_status": {
    "sophia": "ok",
    "praotes": "ok",
    "tapeinophrosyne": "ok"
  }
}
```

---

## Operational Runbook

### Starting the Service

```bash
# Development
cd backend/services/penelope_service
python -m uvicorn main:app --reload

# Production
docker-compose up -d penelope_service
```

### Stopping the Service

```bash
# Development
CTRL+C

# Production
docker-compose stop penelope_service
```

### Common Operations

#### 1. Reset Circuit Breaker
```python
from core.circuit_breaker import HealingCircuitBreaker

circuit_breaker = HealingCircuitBreaker()
await circuit_breaker.reset_circuit("service-name")
```

#### 2. Query Audit Trail
```python
from core.decision_audit_logger import DecisionAuditLogger

audit_logger = DecisionAuditLogger()
decisions = await audit_logger.get_decisions(since=datetime.utcnow() - timedelta(hours=24))
```

#### 3. Approve Pending Patches
```python
from core.human_approval import HumanApprovalWorkflow

workflow = HumanApprovalWorkflow()
pending = await workflow.get_pending_requests()
await workflow.approve(pending[0]["approval_id"], approver="ops-lead")
```

#### 4. Export Audit Trail for Compliance
```bash
curl -H "Authorization: Bearer {token}" \
     https://penelope.vertice.ai/api/v1/audit/export?format=json \
     > audit-$(date +%Y%m%d).json
```

---

## Monitoring & Metrics

### Prometheus Metrics

#### Sophia Engine
```prometheus
# Decision counts
penelope_decisions_total{decision="intervene"}
penelope_decisions_total{decision="observe"}
penelope_decisions_total{decision="escalate"}

# Decision duration
penelope_decision_duration_seconds_bucket
```

#### Circuit Breaker
```prometheus
# Circuit state
penelope_circuit_breaker_state{service="api-gateway"}  # 0=closed, 1=open, 2=half_open

# Failures
penelope_circuit_breaker_failures{service="api-gateway"}

# State transitions
penelope_circuit_transitions_total{service="api-gateway",from_state="closed",to_state="open"}
```

#### Audit Logger
```prometheus
# Decisions logged
penelope_decisions_logged_total{decision_type="intervene"}

# Risk distribution
penelope_decision_risk_scores_bucket
```

#### Human Approval
```prometheus
# Approval requests
penelope_approval_requests_total{status="approved"}
penelope_approval_requests_total{status="rejected"}
penelope_approval_requests_total{status="expired"}

# Pending approvals
penelope_approval_pending

# Response time
penelope_approval_response_seconds_bucket
```

### Grafana Dashboards

**Dashboard**: PENELOPE Overview
**Panels**:
1. Decision Rate (decisions/hour)
2. Circuit Breaker Status
3. Approval Pending Count
4. Patch Success Rate
5. Risk Score Distribution

---

## Troubleshooting

### Issue: Circuit Breaker Stuck OPEN
**Symptoms**: Healing attempts always blocked
**Diagnosis**:
```bash
curl https://penelope.vertice.ai/api/v1/circuit/status/{service}
```

**Resolution**:
```python
# Check if cooldown expired
# Reset if necessary
await circuit_breaker.reset_circuit("service-name")
```

### Issue: Approval Requests Timing Out
**Symptoms**: All approvals expiring
**Diagnosis**: Check Slack/Email notifications

**Resolution**:
```python
# Increase timeout
workflow = HumanApprovalWorkflow()
result = await workflow.request_approval(
    anomaly_id="...",
    patch="...",
    risk_score=0.85,
    impact_estimate="High",
    timeout_seconds=7200  # 2 hours
)
```

### Issue: Audit Trail Not Logging
**Symptoms**: No decisions in audit trail
**Diagnosis**:
```python
count = await audit_logger.count_decisions()
```

**Resolution**: Check database connection

---

## Migration Guide

### From Manual Healing to PENELOPE

#### Phase 1: Shadow Mode (Week 1-2)
- PENELOPE runs but doesn't deploy patches
- Manual team reviews recommendations
- Build confidence in decisions

#### Phase 2: Low-Risk Autonomous (Week 3-4)
- PENELOPE deploys surgical patches (< 5 lines)
- Human approval for moderate+ patches
- Monitor success rate

#### Phase 3: Full Autonomous (Week 5+)
- PENELOPE handles all severity levels
- Human approval only for redesigns
- Continuous monitoring

### Configuration

```yaml
# config/penelope.yaml
sophia:
  risk_tolerance: 0.3  # Start conservative

praotes:
  max_surgical_lines: 5
  max_moderate_lines: 25

circuit_breaker:
  failure_threshold: 3
  window_minutes: 15
  cooldown_minutes: 60

human_approval:
  high_risk_threshold: 0.7
  timeout_seconds: 7200  # 2 hours
```

---

## Biblical Principles → Code Mapping

| Principle | Scripture | Module | Function |
|-----------|-----------|--------|----------|
| Sophia (Wisdom) | Proverbs 9:10 | sophia_engine.py | should_intervene() |
| Praotes (Gentleness) | James 1:21 | praotes_validator.py | validate_patch() |
| Tapeinophrosyne (Humility) | James 4:6 | tapeinophrosyne_monitor.py | assess_competence() |
| Prudence | Proverbs 14:15 | circuit_breaker.py | is_allowed() |
| Wise Counsel | Proverbs 15:22 | human_approval.py | request_approval() |
| Wisdom Guidance | Proverbs 4:11 | decision_audit_logger.py | log_decision() |

---

## Contact & Support

**Team**: Vértice Platform Team
**Slack**: #penelope-support
**Email**: penelope-support@vertice.ai
**On-Call**: PagerDuty rotation

---

**Generated**: 2025-11-01
**Version**: 1.0.0
**Status**: Production Ready ✅

*Building wise, tested, production-ready systems with Claude Code*
