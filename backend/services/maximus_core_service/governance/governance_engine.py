"""
Governance Engine - HITL Decision Management

⚠️ POC IMPLEMENTATION FOR GRPC BRIDGE VALIDATION
This is a minimal implementation for Week 9-10 Migration Bridge testing.
Production implementation will integrate with existing PolicyEngine and ERBManager.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import time
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4


class DecisionStatus(str, Enum):
    """Status of a governance decision."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    EXPIRED = "EXPIRED"


@dataclass
class RiskAssessment:
    """Risk assessment for a decision."""

    score: float = 0.0  # 0.0 to 1.0
    level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    factors: list[str] = field(default_factory=list)


@dataclass
class Decision:
    """
    HITL Decision requiring operator approval.

    Represents an action that requires human oversight before execution.
    """

    decision_id: str = field(default_factory=lambda: str(uuid4()))
    operation_type: str = ""  # e.g., "EXPLOIT_EXECUTION", "LATERAL_MOVEMENT"
    context: dict[str, Any] = field(default_factory=dict)
    risk: RiskAssessment = field(default_factory=RiskAssessment)
    status: DecisionStatus = DecisionStatus.PENDING
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    sla_seconds: int = 300  # 5 minutes default SLA
    operator_id: str | None = None
    operator_comment: str = ""
    operator_reasoning: str = ""
    resolved_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if decision has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def time_remaining(self) -> int:
        """Get seconds remaining before expiration."""
        if self.expires_at is None:
            return -1
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))


class GovernanceEngine:
    """
    Governance Engine for HITL decision management.

    ⚠️ POC IMPLEMENTATION - For gRPC bridge validation only.
    Production version will integrate with PolicyEngine and ERBManager.
    """

    def __init__(self):
        """Initialize governance engine."""
        self.decisions: dict[str, Decision] = {}
        self.start_time = time.time()
        self._event_subscribers = []

        # Create some mock decisions for testing
        self._create_mock_decisions()

    def _create_mock_decisions(self):
        """Create mock decisions for POC testing."""
        # Decision 1: High-risk exploit execution
        decision1 = Decision(
            decision_id="dec-001",
            operation_type="EXPLOIT_EXECUTION",
            context={"target": "192.168.1.100", "cve": "CVE-2024-1234", "service": "Apache 2.4.50"},
            risk=RiskAssessment(
                score=0.85,
                level="HIGH",
                factors=["Remote code execution", "Production environment", "Critical service"],
            ),
            priority="HIGH",
            sla_seconds=600,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        # Decision 2: Lateral movement
        decision2 = Decision(
            decision_id="dec-002",
            operation_type="LATERAL_MOVEMENT",
            context={"source": "192.168.1.50", "target": "192.168.1.200", "method": "Pass-the-Hash"},
            risk=RiskAssessment(score=0.65, level="MEDIUM", factors=["Credential reuse", "Internal network"]),
            priority="MEDIUM",
            sla_seconds=300,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )

        # Decision 3: Data exfiltration
        decision3 = Decision(
            decision_id="dec-003",
            operation_type="DATA_EXFILTRATION",
            context={"source": "database-prod-01", "size_mb": 150, "contains_pii": True},
            risk=RiskAssessment(
                score=0.95, level="CRITICAL", factors=["PII data", "Large volume", "Production database"]
            ),
            priority="CRITICAL",
            sla_seconds=900,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )

        self.decisions = {
            decision1.decision_id: decision1,
            decision2.decision_id: decision2,
            decision3.decision_id: decision3,
        }

    def get_uptime(self) -> float:
        """Get engine uptime in seconds."""
        return time.time() - self.start_time

    def get_pending_decisions(
        self, limit: int = 50, status: str = "PENDING", priority: str | None = None
    ) -> list[Decision]:
        """Get pending decisions with optional filtering."""
        results = []

        for decision in self.decisions.values():
            # Filter by status
            if status and decision.status.value != status:
                continue

            # Filter by priority
            if priority and decision.priority != priority:
                continue

            results.append(decision)

        # Sort by priority and creation time BEFORE limiting
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        results.sort(key=lambda d: (priority_order.get(d.priority, 4), d.created_at))

        # Apply limit AFTER sorting
        return results[:limit]

    def get_decision(self, decision_id: str) -> Decision | None:
        """Get a specific decision by ID."""
        return self.decisions.get(decision_id)

    def create_decision(
        self,
        operation_type: str,
        context: dict[str, Any],
        risk: RiskAssessment,
        priority: str = "MEDIUM",
        sla_seconds: int = 300,
    ) -> Decision:
        """Create a new decision requiring HITL review."""
        decision = Decision(
            operation_type=operation_type,
            context=context,
            risk=risk,
            priority=priority,
            sla_seconds=sla_seconds,
            expires_at=datetime.utcnow() + timedelta(seconds=sla_seconds),
        )

        self.decisions[decision.decision_id] = decision

        # Emit event
        self._emit_event({"type": "new_decision", "decision": decision})

        return decision

    def update_decision_status(
        self, decision_id: str, status: DecisionStatus, operator_id: str, comment: str = "", reasoning: str = ""
    ) -> bool:
        """Update decision status."""
        decision = self.decisions.get(decision_id)
        if not decision:
            return False

        decision.status = status
        decision.operator_id = operator_id
        decision.operator_comment = comment
        decision.operator_reasoning = reasoning
        decision.resolved_at = datetime.utcnow()

        # Emit event
        self._emit_event({"type": "decision_resolved", "decision": decision})

        return True

    def get_metrics(self) -> dict[str, Any]:
        """Get governance metrics."""
        total = len(self.decisions)
        pending = sum(1 for d in self.decisions.values() if d.status == DecisionStatus.PENDING)
        approved = sum(1 for d in self.decisions.values() if d.status == DecisionStatus.APPROVED)
        rejected = sum(1 for d in self.decisions.values() if d.status == DecisionStatus.REJECTED)
        escalated = sum(1 for d in self.decisions.values() if d.status == DecisionStatus.ESCALATED)
        critical = sum(1 for d in self.decisions.values() if d.priority == "CRITICAL")
        high_priority = sum(1 for d in self.decisions.values() if d.priority == "HIGH")

        # Calculate average response time
        resolved_decisions = [d for d in self.decisions.values() if d.resolved_at]
        if resolved_decisions:
            response_times = [(d.resolved_at - d.created_at).total_seconds() for d in resolved_decisions]
            avg_response_time = sum(response_times) / len(response_times)
        else:
            avg_response_time = 0.0

        # Calculate approval rate
        total_resolved = approved + rejected
        approval_rate = (approved / total_resolved * 100) if total_resolved > 0 else 0.0

        # SLA violations
        sla_violations = sum(
            1
            for d in self.decisions.values()
            if d.resolved_at and (d.resolved_at - d.created_at).total_seconds() > d.sla_seconds
        )

        return {
            "pending_count": pending,
            "total_decisions": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "escalated_count": escalated,
            "critical_count": critical,
            "high_priority_count": high_priority,
            "avg_response_time": avg_response_time,
            "approval_rate": approval_rate,
            "sla_violations": sla_violations,
        }

    def subscribe_decision_events(self) -> Generator[dict[str, Any], None, None]:
        """Subscribe to decision events (for streaming)."""
        # POC: Return existing decisions as events
        for decision in self.decisions.values():
            yield {"type": "new_decision", "decision": decision}

    def subscribe_events(self) -> Generator[dict[str, Any], None, None]:
        """Subscribe to governance events (for streaming)."""
        # POC: Return mock events
        yield {
            "type": "connection_established",
            "message": "Governance engine connected",
            "metrics": self.get_metrics(),
        }

    def _emit_event(self, event: dict[str, Any]):
        """Emit an event to subscribers."""
        for subscriber in self._event_subscribers:
            subscriber(event)
