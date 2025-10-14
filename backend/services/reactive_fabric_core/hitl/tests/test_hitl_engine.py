"""
Tests for HITL Engine.

Tests alert management, decision workflows, and human oversight interfaces.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..hitl_engine import (
    HITLEngine,
    HITLConfig,
    Alert,
    AlertStatus,
    AlertPriority,
    DecisionRequest,
    DecisionResponse,
    DecisionType,
    ApprovalStatus,
    AuditLog,
    WorkflowState
)


@pytest.fixture
def config():
    """Create test configuration."""
    return HITLConfig(
        alert_retention_days=30,
        max_pending_alerts=100,
        escalation_threshold=0.8,
        auto_escalate_after_minutes=30,
        decision_timeout_minutes=15,
        require_dual_approval=False,
        audit_all_actions=True,
        alert_grouping_window_minutes=10,
        max_related_alerts=5
    )


@pytest.fixture
def engine(config):
    """Create test HITL engine."""
    return HITLEngine(config)


class TestHITLEngine:
    """Test suite for HITLEngine."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.config is not None
        assert len(engine.alerts) == 0
        assert len(engine.decision_requests) == 0
        assert len(engine.decision_responses) == 0
        assert len(engine.audit_logs) == 0
        assert engine.total_alerts == 0
        assert engine.total_decisions == 0
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_create_alert(self, engine):
        """Test alert creation."""
        alert = await engine.create_alert(
            title="Suspicious Network Activity",
            description="Port scanning detected from external IP",
            source="NetworkCollector",
            priority=AlertPriority.HIGH,
            threat_score=0.7,
            entities={"ip": "192.168.1.100", "hostname": "workstation01"},
            mitre_tactics=["TA0043"],
            mitre_techniques=["T1046"]
        )

        assert alert.alert_id in engine.alerts
        assert alert.title == "Suspicious Network Activity"
        assert alert.priority == AlertPriority.HIGH
        assert alert.status == AlertStatus.PENDING
        assert alert.threat_score == 0.7
        assert "ip" in alert.entities
        assert len(alert.recommended_actions) > 0
        assert DecisionType.INVESTIGATE in alert.recommended_actions
        assert engine.total_alerts == 1

        # Check audit log
        assert len(engine.audit_logs) == 1
        assert engine.audit_logs[0].action == "alert_created"

    @pytest.mark.asyncio
    async def test_create_critical_alert_auto_escalation(self, engine):
        """Test auto-escalation of critical alerts."""
        alert = await engine.create_alert(
            title="Critical Security Breach",
            description="Unauthorized access detected",
            source="SecurityMonitor",
            priority=AlertPriority.CRITICAL,
            threat_score=0.9,
            entities={"ip": "10.0.0.50", "user": "admin"}
        )

        # Should be auto-escalated
        assert alert.status == AlertStatus.ESCALATED
        assert engine.escalation_count == 1
        assert DecisionType.ESCALATE in alert.recommended_actions

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, engine):
        """Test alert acknowledgment."""
        alert = await engine.create_alert(
            title="Test Alert",
            description="Test",
            source="Test",
            priority=AlertPriority.MEDIUM,
            threat_score=0.5
        )

        success = await engine.acknowledge_alert(
            alert.alert_id,
            assigned_to="analyst1",
            notes="Investigating the issue"
        )

        assert success is True
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.assigned_to == "analyst1"
        assert alert.acknowledged_at is not None
        assert len(alert.notes) == 1
        assert "Investigating the issue" in alert.notes[0]

    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent_alert(self, engine):
        """Test acknowledging non-existent alert."""
        success = await engine.acknowledge_alert(
            "nonexistent",
            assigned_to="analyst1"
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_update_alert_status(self, engine):
        """Test updating alert status."""
        alert = await engine.create_alert(
            title="Test Alert",
            description="Test",
            source="Test",
            priority=AlertPriority.LOW,
            threat_score=0.3
        )

        success = await engine.update_alert_status(
            alert.alert_id,
            AlertStatus.INVESTIGATING,
            actor="analyst2",
            notes="Running deep analysis"
        )

        assert success is True
        assert alert.status == AlertStatus.INVESTIGATING
        assert len(alert.notes) == 1

        # Resolve the alert
        success = await engine.update_alert_status(
            alert.alert_id,
            AlertStatus.RESOLVED,
            actor="analyst2",
            notes="False positive"
        )

        assert success is True
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert len(alert.notes) == 2

    @pytest.mark.asyncio
    async def test_request_decision(self, engine):
        """Test decision request creation."""
        alert = await engine.create_alert(
            title="Malicious IP",
            description="Known bad actor",
            source="ThreatIntel",
            priority=AlertPriority.HIGH,
            threat_score=0.7,
            entities={"ip": "10.0.0.100"}
        )

        request = await engine.request_decision(
            alert_id=alert.alert_id,
            decision_type=DecisionType.BLOCK_IP,
            target={"ip": "10.0.0.100"},
            reason="Known malicious IP from threat intel",
            risk_level="high"
        )

        assert request.request_id in engine.decision_requests
        assert request.alert_id == alert.alert_id
        assert request.decision_type == DecisionType.BLOCK_IP
        assert request.requires_approval is True
        assert request.automated is False  # Phase 1
        assert request.expires_at is not None
        assert engine.total_decisions == 1
        assert request.request_id in engine.pending_decisions

        # Check workflow created
        assert alert.alert_id in engine.workflows
        workflow = engine.workflows[alert.alert_id]
        assert request.request_id in workflow.decisions_pending

    @pytest.mark.asyncio
    async def test_request_decision_invalid_alert(self, engine):
        """Test decision request with invalid alert."""
        with pytest.raises(ValueError, match="Alert .* not found"):
            await engine.request_decision(
                alert_id="nonexistent",
                decision_type=DecisionType.BLOCK_IP,
                target={"ip": "10.0.0.1"},
                reason="Test"
            )

    @pytest.mark.asyncio
    async def test_approve_decision(self, engine):
        """Test decision approval."""
        alert = await engine.create_alert(
            title="Test",
            description="Test",
            source="Test",
            priority=AlertPriority.HIGH,
            threat_score=0.6,
            entities={"ip": "10.0.0.1"}
        )

        request = await engine.request_decision(
            alert_id=alert.alert_id,
            decision_type=DecisionType.BLOCK_IP,
            target={"ip": "10.0.0.1"},
            reason="Malicious activity"
        )

        response = await engine.approve_decision(
            request_id=request.request_id,
            approver="security_admin",
            notes="Confirmed malicious"
        )

        assert response.status == ApprovalStatus.APPROVED
        assert response.approver == "security_admin"
        assert response.approved_at is not None
        assert response.execution_result is not None

        # Phase 1: Check logged only
        assert response.execution_result["phase"] == "1"
        assert response.execution_result["action"] == "logged_only"

        assert request.request_id not in engine.pending_decisions
        assert len(alert.notes) == 1

    @pytest.mark.asyncio
    async def test_approve_expired_decision(self, engine):
        """Test approving expired decision."""
        alert = await engine.create_alert(
            title="Test",
            description="Test",
            source="Test",
            priority=AlertPriority.MEDIUM,
            threat_score=0.5
        )

        request = await engine.request_decision(
            alert_id=alert.alert_id,
            decision_type=DecisionType.INVESTIGATE,
            target={},
            reason="Test"
        )

        # Make request expired
        request.expires_at = datetime.utcnow() - timedelta(minutes=1)

        response = await engine.approve_decision(
            request_id=request.request_id,
            approver="admin"
        )

        assert response.status == ApprovalStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_reject_decision(self, engine):
        """Test decision rejection."""
        alert = await engine.create_alert(
            title="Test",
            description="Test",
            source="Test",
            priority=AlertPriority.LOW,
            threat_score=0.2,
            entities={"hostname": "server01"}
        )

        request = await engine.request_decision(
            alert_id=alert.alert_id,
            decision_type=DecisionType.ISOLATE_HOST,
            target={"hostname": "server01"},
            reason="Suspicious behavior"
        )

        response = await engine.reject_decision(
            request_id=request.request_id,
            rejector="security_lead",
            reason="Not enough evidence"
        )

        assert response.status == ApprovalStatus.REJECTED
        assert response.rejection_reason == "Not enough evidence"
        assert request.request_id not in engine.pending_decisions
        assert len(alert.notes) == 1
        assert "Rejected" in alert.notes[0]

    @pytest.mark.asyncio
    async def test_get_pending_alerts(self, engine):
        """Test retrieving pending alerts."""
        # Create alerts with different priorities
        # Note: Critical with score 0.9 will be auto-escalated
        critical_alert = await engine.create_alert(
            "Critical Alert", "Test", "Test",
            AlertPriority.CRITICAL, 0.9
        )
        await engine.create_alert(
            "High Alert", "Test", "Test",
            AlertPriority.HIGH, 0.7
        )
        await engine.create_alert(
            "Low Alert", "Test", "Test",
            AlertPriority.LOW, 0.2
        )

        # Get all pending (Critical is escalated, not pending)
        pending = await engine.get_pending_alerts()
        assert len(pending) == 2  # Only High and Low are pending

        # High should be first (sorted by priority, Critical was escalated)
        assert pending[0].priority == AlertPriority.HIGH
        assert pending[0].title == "High Alert"

        # Filter by priority
        high_alerts = await engine.get_pending_alerts(priority=AlertPriority.HIGH)
        assert len(high_alerts) == 1
        assert high_alerts[0].title == "High Alert"

        # Check that critical alert was escalated
        assert critical_alert.status == AlertStatus.ESCALATED

    @pytest.mark.asyncio
    async def test_get_pending_decisions(self, engine):
        """Test retrieving pending decisions."""
        alert = await engine.create_alert(
            "Test", "Test", "Test",
            AlertPriority.MEDIUM, 0.5
        )

        # Create multiple decision requests
        req1 = await engine.request_decision(
            alert.alert_id,
            DecisionType.INVESTIGATE,
            {},
            "Need investigation"
        )

        req2 = await engine.request_decision(
            alert.alert_id,
            DecisionType.ESCALATE,
            {},
            "Escalate to senior team"
        )

        pending = await engine.get_pending_decisions()
        assert len(pending) == 2

        request_ids = [r.request_id for r in pending]
        assert req1.request_id in request_ids
        assert req2.request_id in request_ids

    @pytest.mark.asyncio
    async def test_expired_decision_cleanup(self, engine):
        """Test cleanup of expired decisions."""
        alert = await engine.create_alert(
            "Test", "Test", "Test",
            AlertPriority.LOW, 0.1
        )

        request = await engine.request_decision(
            alert.alert_id,
            DecisionType.DISMISS,
            {},
            "Low risk"
        )

        # Make it expired
        request.expires_at = datetime.utcnow() - timedelta(minutes=1)

        pending = await engine.get_pending_decisions()
        assert len(pending) == 0

        # Check response was created
        assert len(engine.decision_responses) == 1
        response = list(engine.decision_responses.values())[0]
        assert response.status == ApprovalStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_get_alert_timeline(self, engine):
        """Test alert timeline generation."""
        alert = await engine.create_alert(
            "Test Alert", "Test", "Test",
            AlertPriority.HIGH, 0.6,
            entities={"ip": "10.0.0.1"}
        )

        # Acknowledge
        await engine.acknowledge_alert(
            alert.alert_id,
            "analyst1"
        )

        # Request decision
        request = await engine.request_decision(
            alert.alert_id,
            DecisionType.BLOCK_IP,
            {"ip": "10.0.0.1"},
            "Block malicious IP"
        )

        # Approve decision
        await engine.approve_decision(
            request.request_id,
            "admin"
        )

        # Resolve
        await engine.update_alert_status(
            alert.alert_id,
            AlertStatus.RESOLVED,
            "analyst1"
        )

        timeline = await engine.get_alert_timeline(alert.alert_id)

        # Check timeline events
        assert len(timeline) >= 5
        event_types = [e["event"] for e in timeline]
        assert "alert_created" in event_types
        assert "alert_acknowledged" in event_types
        assert "decision_requested" in event_types
        assert "decision_approved" in event_types
        assert "alert_resolved" in event_types

        # Check chronological order
        for i in range(1, len(timeline)):
            assert timeline[i]["timestamp"] >= timeline[i-1]["timestamp"]

    @pytest.mark.asyncio
    async def test_get_audit_logs(self, engine):
        """Test audit log retrieval."""
        # Create some activity
        alert = await engine.create_alert(
            "Test", "Test", "Test",
            AlertPriority.MEDIUM, 0.5
        )

        await engine.acknowledge_alert(
            alert.alert_id,
            "user1"
        )

        await engine.update_alert_status(
            alert.alert_id,
            AlertStatus.RESOLVED,
            "user2"
        )

        # Get all logs
        logs = await engine.get_audit_logs()
        assert len(logs) >= 3

        # Filter by actor
        user1_logs = await engine.get_audit_logs(actor="user1")
        assert len(user1_logs) == 1
        assert user1_logs[0].actor == "user1"

        # Filter by action
        create_logs = await engine.get_audit_logs(action="alert_created")
        assert len(create_logs) == 1
        assert create_logs[0].action == "alert_created"

    @pytest.mark.asyncio
    async def test_find_related_alerts(self, engine):
        """Test finding related alerts."""
        # Create alerts with common entities
        alert1 = await engine.create_alert(
            "Alert 1", "Test", "Test",
            AlertPriority.HIGH, 0.6,
            entities={"ip": "10.0.0.1", "port": 22}
        )

        alert2 = await engine.create_alert(
            "Alert 2", "Test", "Test",
            AlertPriority.MEDIUM, 0.5,
            entities={"ip": "10.0.0.1", "port": 80}
        )

        alert3 = await engine.create_alert(
            "Alert 3", "Test", "Test",
            AlertPriority.LOW, 0.3,
            entities={"ip": "10.0.0.2", "port": 443}
        )

        # Check related alerts
        assert len(alert1.related_alerts) == 0  # First alert has no prior
        assert alert1.alert_id in alert2.related_alerts  # Share same IP
        assert alert1.alert_id not in alert3.related_alerts  # Different IP

    @pytest.mark.asyncio
    async def test_alert_limit_cleanup(self, engine):
        """Test cleanup when alert limit reached."""
        engine.config.max_pending_alerts = 5

        # Create resolved alerts
        for i in range(3):
            alert = await engine.create_alert(
                f"Old Alert {i}", "Test", "Test",
                AlertPriority.LOW, 0.1
            )
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow() - timedelta(days=40)

        # Create active alerts up to limit
        for i in range(3):
            await engine.create_alert(
                f"Active Alert {i}", "Test", "Test",
                AlertPriority.MEDIUM, 0.5
            )

        # This should trigger cleanup
        await engine.create_alert(
            "New Alert", "Test", "Test",
            AlertPriority.HIGH, 0.7
        )

        # Old resolved alerts should be removed
        assert len(engine.alerts) <= engine.config.max_pending_alerts + 1

    @pytest.mark.asyncio
    async def test_recommended_actions(self, engine):
        """Test recommended action determination."""
        # Critical alert with multiple entities
        alert = await engine.create_alert(
            "Critical Threat", "Test", "Test",
            AlertPriority.CRITICAL, 0.9,
            entities={
                "ip": "10.0.0.1",
                "hostname": "server01",
                "process": "malware.exe",
                "user": "admin"
            }
        )

        assert DecisionType.INVESTIGATE in alert.recommended_actions
        assert DecisionType.BLOCK_IP in alert.recommended_actions
        assert DecisionType.ISOLATE_HOST in alert.recommended_actions
        assert DecisionType.TERMINATE_PROCESS in alert.recommended_actions
        assert DecisionType.REVOKE_ACCESS in alert.recommended_actions
        assert DecisionType.ESCALATE in alert.recommended_actions

        # Low priority alert
        low_alert = await engine.create_alert(
            "Low Threat", "Test", "Test",
            AlertPriority.LOW, 0.2,
            entities={"ip": "10.0.0.2"}
        )

        assert DecisionType.INVESTIGATE in low_alert.recommended_actions
        assert DecisionType.ESCALATE not in low_alert.recommended_actions

    @pytest.mark.asyncio
    async def test_workflow_tracking(self, engine):
        """Test workflow state tracking."""
        alert = await engine.create_alert(
            "Test", "Test", "Test",
            AlertPriority.HIGH, 0.7,
            entities={"ip": "10.0.0.1"}
        )

        # Request multiple decisions
        req1 = await engine.request_decision(
            alert.alert_id,
            DecisionType.INVESTIGATE,
            {},
            "Investigate"
        )

        req2 = await engine.request_decision(
            alert.alert_id,
            DecisionType.BLOCK_IP,
            {"ip": "10.0.0.1"},
            "Block IP"
        )

        workflow = engine.workflows[alert.alert_id]
        assert len(workflow.decisions_pending) == 2
        assert workflow.current_stage == "decision_pending"

        # Approve one decision
        await engine.approve_decision(req1.request_id, "admin")

        assert len(workflow.decisions_pending) == 1
        assert "decision_investigate" in workflow.stages_completed
        assert workflow.updated_at > workflow.created_at

    @pytest.mark.asyncio
    async def test_start_stop(self, engine):
        """Test engine start and stop."""
        await engine.start()
        assert engine._running is True
        assert engine._cleanup_task is not None

        await engine.stop()
        assert engine._running is False

        # Check audit logs
        logs = [log for log in engine.audit_logs if log.action in ["engine_started", "engine_stopped"]]
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_metrics(self, engine):
        """Test metrics retrieval."""
        # Create some alerts and decisions
        alert1 = await engine.create_alert(
            "Alert 1", "Test", "Test",
            AlertPriority.HIGH, 0.7
        )

        alert2 = await engine.create_alert(
            "Alert 2", "Test", "Test",
            AlertPriority.CRITICAL, 0.9
        )

        await engine.acknowledge_alert(alert1.alert_id, "analyst")

        await engine.request_decision(
            alert1.alert_id,
            DecisionType.BLOCK_IP,
            {"ip": "10.0.0.1"},
            "Block"
        )

        metrics = engine.get_metrics()

        assert metrics["running"] is False
        assert metrics["total_alerts"] == 2
        assert metrics["active_alerts"] == 2
        assert metrics["pending_alerts"] == 0  # One escalated, one acknowledged
        assert metrics["acknowledged_alerts"] == 1
        assert metrics["escalated_alerts"] == 1
        assert metrics["total_decisions"] == 1
        assert metrics["pending_decisions"] == 1
        assert metrics["audit_logs"] > 0

    @pytest.mark.asyncio
    async def test_invalid_approve_decision(self, engine):
        """Test approving non-existent decision."""
        with pytest.raises(ValueError, match="Request .* not found"):
            await engine.approve_decision(
                request_id="nonexistent",
                approver="admin"
            )

    @pytest.mark.asyncio
    async def test_invalid_reject_decision(self, engine):
        """Test rejecting non-existent decision."""
        with pytest.raises(ValueError, match="Request .* not found"):
            await engine.reject_decision(
                request_id="nonexistent",
                rejector="admin",
                reason="Test"
            )

    def test_repr(self, engine):
        """Test string representation."""
        repr_str = repr(engine)
        assert "HITLEngine" in repr_str
        assert "running=" in repr_str
        assert "alerts=" in repr_str
        assert "pending_decisions=" in repr_str
        assert "audit_logs=" in repr_str