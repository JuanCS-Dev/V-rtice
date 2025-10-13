# 🔗 E2E INTEGRATION PLAN - Adaptive Immune System

**Date**: 2025-10-13
**Branch**: `reactive-fabric/sprint3-collectors-orchestration`
**Status**: Planning

---

## 🎯 Objective

Connect all existing components (Oráculo, Eureka, Wargaming, HITL) into a complete end-to-end workflow using RabbitMQ message queues.

---

## 📊 Component Mapping

### Existing Components (Implemented)

| Component | Status | Location | Purpose |
|-----------|--------|----------|---------|
| **Oráculo** | ✅ | `/oraculo/` | CVE detection, APV generation |
| **Eureka** | ✅ | `/eureka/` | Confirmation, remedy generation |
| **Wargaming** | ✅ | `/wargaming/` | Exploit validation |
| **HITL API** | ✅ | `/hitl/api/` | Human review interface |
| **HITL Frontend** | ✅ | `/frontend/src/components/admin/HITLConsole/` | Web UI |
| **RabbitMQ Client** | ✅ | `/messaging/client.py` | Queue management |
| **Database** | ✅ | `/database/` | PostgreSQL schema |

### Message Queue Infrastructure (Partial)

| Queue | Status | Purpose |
|-------|--------|---------|
| `oraculo.apv.dispatch` | ✅ Configured | Oráculo → Eureka (APV dispatch) |
| `eureka.remedy.status` | ✅ Configured | Eureka → Oráculo (status updates) |
| `wargaming.results` | ✅ Configured | Wargaming → Eureka (results) |
| `hitl.decisions` | ❌ **Missing** | HITL → System (decisions) |
| `hitl.notifications` | ❌ **Missing** | System → HITL (new APVs) |

---

## 🔄 Data Flow (Target E2E)

```
┌─────────────────────────────────────────────────────────────────┐
│                      E2E WORKFLOW                                │
└─────────────────────────────────────────────────────────────────┘

1. CVE DETECTION (Oráculo)
   ├─> Ingest CVEs from NVD/GHSA/OSV
   ├─> Scan dependencies (Python/JS/Go/Docker)
   ├─> Generate APV with vulnerable_code_signature
   └─> Publish to: oraculo.apv.dispatch
            │
            ▼
2. CONFIRMATION (Eureka)
   ├─> Consume from: oraculo.apv.dispatch
   ├─> Run static analysis (Semgrep, Bandit)
   ├─> Run dynamic analysis (Docker exploits)
   ├─> Calculate confirmation score
   ├─> Publish status to: eureka.remedy.status
   └─> If confirmed → Generate remedy
            │
            ▼
3. REMEDY GENERATION (Eureka)
   ├─> Generate patch using LLM (Claude/GPT-4)
   ├─> Validate patch (5-stage pipeline)
   ├─> Create GitHub PR
   └─> Trigger wargaming validation
            │
            ▼
4. WARGAMING VALIDATION (Wargaming Engine)
   ├─> Generate GitHub Actions workflow
   ├─> Run exploit before/after patch
   ├─> Collect evidence
   ├─> Calculate verdict
   └─> Publish to: wargaming.results
            │
            ▼
5. HITL REVIEW (Human-in-the-Loop)
   ├─> Consume from: hitl.notifications (NEW)
   ├─> Display in web console
   ├─> Human makes decision (approve/reject/modify/escalate)
   ├─> Publish to: hitl.decisions (NEW)
   └─> Execute decision via DecisionEngine
            │
            ▼
6. FINAL ACTION (System)
   ├─> Merge PR (if approved)
   ├─> Close PR (if rejected)
   ├─> Request changes (if modify)
   ├─> Escalate (if escalate)
   └─> Update database + notify Oráculo
```

---

## 🔧 Integration Points

### Point 1: Oráculo → Eureka (APV Dispatch)

**Status**: ✅ Partially implemented
**Queue**: `oraculo.apv.dispatch`

**Publisher**: `messaging/publisher.py::APVPublisher`
**Consumer**: `messaging/consumer.py::APVConsumer`

**Payload**:
```json
{
  "apv_id": "uuid",
  "apv_code": "APV-20251013-001",
  "priority": 2,
  "cve_id": "CVE-2021-44228",
  "package_name": "log4j-core",
  "package_version": "2.14.0",
  "vulnerable_code_signature": "${jndi:",
  "affected_files": ["src/main/java/Logger.java"]
}
```

**Action Needed**: Wire Oráculo's APV generator to publish to queue

---

### Point 2: Eureka → Oráculo (Status Updates)

**Status**: ✅ Partially implemented
**Queue**: `eureka.remedy.status`

**Publisher**: `messaging/publisher.py::RemedyStatusPublisher`
**Consumer**: `messaging/consumer.py::RemedyStatusConsumer`

**Payload**:
```json
{
  "apv_id": "uuid",
  "status": "confirmed",
  "confirmed": true,
  "confirmation_score": 0.87,
  "remedy_id": "uuid",
  "pr_url": "https://github.com/org/repo/pull/123"
}
```

**Action Needed**: Wire Eureka orchestrator to publish status updates

---

### Point 3: Wargaming → Eureka (Results)

**Status**: ✅ Partially implemented
**Queue**: `wargaming.results`

**Publisher**: `messaging/publisher.py::WargameReportPublisher`
**Consumer**: `messaging/consumer.py::WargameReportConsumer`

**Payload**:
```json
{
  "remedy_id": "uuid",
  "run_code": "WAR-20251013-001",
  "verdict": "PATCH_EFFECTIVE",
  "confidence_score": 0.95,
  "exploit_before_status": "vulnerable",
  "exploit_after_status": "fixed",
  "evidence_url": "https://github.com/org/repo/actions/runs/123"
}
```

**Action Needed**: Wire Wargaming orchestrator to publish results

---

### Point 4: System → HITL (New APVs)

**Status**: ❌ **NOT IMPLEMENTED**
**Queue**: `hitl.notifications` (NEW)

**Purpose**: Notify HITL console when APVs need human review

**Trigger**: When APV reaches `pending_hitl` state

**Payload**:
```json
{
  "apv_id": "uuid",
  "apv_code": "APV-20251013-001",
  "severity": "critical",
  "package_name": "log4j-core",
  "pr_url": "https://github.com/org/repo/pull/123",
  "wargame_verdict": "PATCH_EFFECTIVE",
  "confidence_score": 0.95
}
```

**Action Needed**:
1. Create queue in RabbitMQ client
2. Create publisher in messaging layer
3. Wire to Eureka orchestrator (after wargaming completes)
4. Wire to HITL WebSocket for real-time updates

---

### Point 5: HITL → System (Decisions)

**Status**: ❌ **NOT IMPLEMENTED**
**Queue**: `hitl.decisions` (NEW)

**Purpose**: Propagate human decisions to execute actions

**Trigger**: When human submits decision via HITL API

**Payload**:
```json
{
  "apv_id": "uuid",
  "decision": "approve",
  "justification": "Patch validated, wargaming passed, merging",
  "confidence": 95,
  "reviewer_email": "security@company.com",
  "decision_timestamp": "2025-10-13T12:34:56Z"
}
```

**Action Needed**:
1. Create queue in RabbitMQ client
2. Create publisher in messaging layer
3. Wire to HITL DecisionEngine (after processing decision)
4. Create consumer in system to execute decisions

---

## 📋 Implementation Tasks

### Task 1: Create Missing Queues

**File**: `messaging/client.py`

Add queue declarations:
```python
async def declare_hitl_queues(self):
    """Declare HITL-related queues."""
    await self._channel.declare_queue(
        "hitl.notifications",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "hitl.notifications.dlq",
            "x-message-ttl": 86400000  # 24h
        }
    )

    await self._channel.declare_queue(
        "hitl.decisions",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "hitl.decisions.dlq",
            "x-message-ttl": 86400000  # 24h
        }
    )

    # DLQs
    await self._channel.declare_queue("hitl.notifications.dlq", durable=True)
    await self._channel.declare_queue("hitl.decisions.dlq", durable=True)
```

---

### Task 2: Create HITL Publishers

**File**: `messaging/publisher.py`

Add:
```python
class HITLNotificationPublisher:
    """Publishes notifications to HITL console."""

    async def publish_new_apv_notification(
        self,
        apv_id: str,
        apv_code: str,
        severity: str,
        package_name: str,
        pr_url: str,
        wargame_verdict: str,
        confidence_score: float
    ) -> None:
        """Notify HITL console of new APV needing review."""
        ...

class HITLDecisionPublisher:
    """Publishes HITL decisions to system."""

    async def publish_decision(
        self,
        apv_id: str,
        decision: str,
        justification: str,
        confidence: int,
        reviewer_email: str
    ) -> None:
        """Publish human decision for execution."""
        ...
```

---

### Task 3: Create HITL Consumers

**File**: `messaging/consumer.py`

Add:
```python
class HITLNotificationConsumer:
    """Consumes HITL notifications (for WebSocket broadcast)."""

    async def consume(self) -> None:
        """Listen for new APV notifications."""
        ...

class HITLDecisionConsumer:
    """Consumes HITL decisions (for execution)."""

    async def consume(self) -> None:
        """Execute human decisions."""
        ...
```

---

### Task 4: Wire Oráculo APV Publisher

**File**: `oraculo/triage_engine.py`

After APV creation, publish to queue:
```python
from messaging.publisher import APVPublisher

class TriageEngine:
    def __init__(self):
        self.apv_publisher = APVPublisher(rabbitmq_client)

    async def process_apv(self, apv: APV) -> None:
        # ... existing code ...

        # Publish to Eureka
        await self.apv_publisher.publish_dispatch_message(
            apv_id=str(apv.id),
            apv_code=apv.code,
            priority=apv.priority_score,
            cve_id=threat.cve_id,
            package_name=dependency.package_name,
            package_version=dependency.package_version,
            vulnerable_code_signature=apv.vulnerable_code_signature,
            affected_files=apv.affected_files
        )
```

---

### Task 5: Wire Eureka Status Publisher

**File**: `eureka/eureka_orchestrator.py`

After confirmation, publish status:
```python
from messaging.publisher import RemedyStatusPublisher

class EurekaOrchestrator:
    def __init__(self):
        self.status_publisher = RemedyStatusPublisher(rabbitmq_client)

    async def process_apv(self, apv_message: dict) -> None:
        # ... confirmation ...

        await self.status_publisher.publish_confirmation_status(
            apv_id=apv_message["apv_id"],
            status="confirmed",
            confirmed=True,
            confirmation_score=score
        )

        # ... remedy generation ...

        await self.status_publisher.publish_remedy_status(
            apv_id=apv_message["apv_id"],
            status="remedy_generated",
            remedy_id=str(remedy.id),
            pr_url=pr_url
        )
```

---

### Task 6: Wire Wargaming Result Publisher

**File**: `wargaming/wargame_orchestrator.py`

After wargaming completes:
```python
from messaging.publisher import WargameReportPublisher

class WargameOrchestrator:
    def __init__(self):
        self.report_publisher = WargameReportPublisher(rabbitmq_client)

    async def run_wargame(self, remedy_id: str) -> dict:
        # ... wargaming ...

        await self.report_publisher.publish_wargame_report(
            remedy_id=remedy_id,
            run_code=run_code,
            verdict=verdict,
            confidence_score=confidence,
            exploit_before_status="vulnerable",
            exploit_after_status="fixed",
            evidence_url=evidence_url
        )
```

---

### Task 7: Wire HITL Notification Publisher

**File**: `eureka/eureka_orchestrator.py`

After wargaming results received:
```python
from messaging.publisher import HITLNotificationPublisher

class EurekaOrchestrator:
    def __init__(self):
        self.hitl_publisher = HITLNotificationPublisher(rabbitmq_client)

    async def handle_wargaming_result(self, result: dict) -> None:
        # Update APV state to pending_hitl
        await self.db.update_apv_state(
            result["remedy_id"],
            "pending_hitl"
        )

        # Notify HITL console
        await self.hitl_publisher.publish_new_apv_notification(
            apv_id=apv_id,
            apv_code=apv_code,
            severity=severity,
            package_name=package_name,
            pr_url=pr_url,
            wargame_verdict=result["verdict"],
            confidence_score=result["confidence_score"]
        )
```

---

### Task 8: Wire HITL Decision Publisher

**File**: `hitl/decision_engine.py`

After processing decision:
```python
from messaging.publisher import HITLDecisionPublisher

class DecisionEngine:
    def __init__(self):
        self.decision_publisher = HITLDecisionPublisher(rabbitmq_client)

    async def process_decision(self, decision_request: DecisionRequest) -> DecisionRecord:
        # ... process decision (GitHub API calls) ...

        # Publish decision to system
        await self.decision_publisher.publish_decision(
            apv_id=decision_request.apv_id,
            decision=decision_request.decision,
            justification=decision_request.justification,
            confidence=decision_request.confidence,
            reviewer_email=decision_request.reviewer_email
        )

        return record
```

---

### Task 9: Create HITL Decision Consumer

**File**: `system/decision_executor.py` (NEW)

Execute decisions:
```python
from messaging.consumer import HITLDecisionConsumer
from oraculo.triage_engine import TriageEngine

class DecisionExecutor:
    """Executes HITL decisions and updates Oráculo."""

    def __init__(self):
        self.consumer = HITLDecisionConsumer(rabbitmq_client)
        self.triage_engine = TriageEngine()

    async def start(self):
        await self.consumer.consume(self.handle_decision)

    async def handle_decision(self, decision: dict):
        apv_id = decision["apv_id"]
        decision_type = decision["decision"]

        if decision_type == "approve":
            # Update Oráculo APV state to approved
            await self.triage_engine.update_apv_state(apv_id, "approved")
        elif decision_type == "reject":
            await self.triage_engine.update_apv_state(apv_id, "rejected")
        elif decision_type == "modify":
            await self.triage_engine.update_apv_state(apv_id, "modification_requested")
        elif decision_type == "escalate":
            await self.triage_engine.update_apv_state(apv_id, "escalated")

        logger.info(f"Decision executed for APV {apv_id}: {decision_type}")
```

---

### Task 10: Wire HITL WebSocket Updates

**File**: `hitl/api/main.py`

Consume notifications and broadcast via WebSocket:
```python
from messaging.consumer import HITLNotificationConsumer

# Background task to consume notifications
async def consume_hitl_notifications():
    consumer = HITLNotificationConsumer(rabbitmq_client)

    async def handle_notification(notification: dict):
        # Broadcast to all WebSocket clients
        await manager.broadcast(WebSocketMessage(
            event_type="new_review",
            data=notification,
            timestamp=datetime.utcnow()
        ))

    await consumer.consume(handle_notification)

@app.on_event("startup")
async def startup_event():
    # Start background notification consumer
    asyncio.create_task(consume_hitl_notifications())
```

---

## 🧪 End-to-End Integration Test

**File**: `tests/integration/test_e2e_workflow.py` (NEW)

```python
import pytest
from adaptive_immune_system import *

@pytest.mark.asyncio
async def test_complete_e2e_workflow():
    """Test complete workflow: CVE → APV → Confirmation → Remedy → Wargaming → HITL → Approve"""

    # 1. Oráculo: Ingest CVE and generate APV
    oraculo = OraculoOrchestrator()
    apv = await oraculo.process_cve("CVE-2021-44228")
    assert apv.code.startswith("APV-")

    # 2. Eureka: Consume APV and confirm vulnerability
    eureka = EurekaOrchestrator()
    confirmation = await eureka.confirm_vulnerability(apv.id)
    assert confirmation.confirmed is True

    # 3. Eureka: Generate remedy and create PR
    remedy = await eureka.generate_remedy(apv.id)
    assert remedy.pr_url is not None

    # 4. Wargaming: Validate patch
    wargaming = WargameOrchestrator()
    result = await wargaming.run_wargame(remedy.id)
    assert result["verdict"] == "PATCH_EFFECTIVE"

    # 5. HITL: Notification sent to queue
    # (check that APV appears in HITL console)
    hitl_apvs = await hitl_api.get_pending_reviews()
    assert apv.id in [r["apv_id"] for r in hitl_apvs]

    # 6. HITL: Human decision (approve)
    decision = await hitl_api.submit_decision(
        apv_id=apv.id,
        decision="approve",
        justification="Validated and approved",
        confidence=95,
        reviewer_email="security@company.com"
    )
    assert decision.decision == "approve"

    # 7. System: Execute decision
    # (check that PR is merged)
    pr_status = await github_client.get_pr_status(remedy.pr_url)
    assert pr_status == "merged"

    # 8. Oráculo: APV state updated
    updated_apv = await oraculo.get_apv(apv.id)
    assert updated_apv.state == "approved"
```

---

## 📊 Success Criteria

- [ ] All 5 integration points implemented
- [ ] 2 new queues created (`hitl.notifications`, `hitl.decisions`)
- [ ] All publishers/consumers wired
- [ ] E2E test passes (CVE → Approve)
- [ ] WebSocket real-time updates working
- [ ] All components logging to structured logger
- [ ] Zero TODOs in integration code
- [ ] Documentation complete

---

## ⏱️ Estimated Time

- **Task 1-3** (Queues + Publishers/Consumers): 2 hours
- **Task 4-6** (Wire existing components): 2 hours
- **Task 7-8** (HITL notification/decision): 1 hour
- **Task 9-10** (Decision executor + WebSocket): 2 hours
- **E2E Test**: 1 hour
- **Documentation**: 1 hour

**Total**: ~9 hours (1 day)

---

## 🚀 Deployment Steps

1. Update RabbitMQ with new queues
2. Deploy updated messaging layer
3. Deploy updated Oráculo/Eureka/Wargaming
4. Deploy updated HITL API
5. Run E2E test
6. Monitor queues and logs

---

**Status**: Ready to implement
**Next**: Execute tasks 1-10 sequentially
