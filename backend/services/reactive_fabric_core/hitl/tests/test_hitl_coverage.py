"""
Additional tests for HITL Engine to increase coverage.
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from ..hitl_engine import (
    HITLEngine,
    HITLConfig,
    AlertStatus,
    AlertPriority,
    DecisionType,
    ApprovalStatus
)


@pytest.fixture
def config():
    """Create test configuration."""
    return HITLConfig(
        alert_retention_days=7,
        max_pending_alerts=50,
        escalation_threshold=0.75,
        auto_escalate_after_minutes=15,
        decision_timeout_minutes=10,
        require_dual_approval=True,
        audit_all_actions=True
    )


@pytest.fixture
def engine(config):
    """Create test engine."""
    return HITLEngine(config)


class TestHITLCoverage:
    """Additional tests for HITL engine coverage."""

    @pytest.mark.asyncio
    async def test_alert_with_file_hash_entity(self, engine):
        """Test alert with file hash entity for quarantine action."""
        alert = await engine.create_alert(
            title="Malicious File Detected",
            description="Malware found",
            source="AntiVirus",
            priority=AlertPriority.HIGH,
            threat_score=0.65,
            entities={"file_hash": "abc123def456", "path": "/tmp/malware.exe"}
        )

        # Should recommend quarantine for file
        assert DecisionType.QUARANTINE_FILE in alert.recommended_actions

    @pytest.mark.asyncio
    async def test_alert_grouping_same_source(self, engine):
        """Test alert grouping by same source."""
        # Create alerts from same source
        alert1 = await engine.create_alert(
            "Alert 1", "Test", "SecurityMonitor",
            AlertPriority.MEDIUM, 0.5
        )

        alert2 = await engine.create_alert(
            "Alert 2", "Test", "SecurityMonitor",
            AlertPriority.MEDIUM, 0.5
        )

        # Second alert should find first as related
        assert alert1.alert_id in alert2.related_alerts

    @pytest.mark.asyncio
    async def test_periodic_cleanup_task(self, engine):
        """Test periodic cleanup task execution."""
        engine.config.alert_retention_days = 0  # Immediate cleanup

        # Create old resolved alert
        alert = await engine.create_alert(
            "Old Alert", "Test", "Test",
            AlertPriority.LOW, 0.1
        )
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow() - timedelta(days=1)

        # Start engine to trigger cleanup
        await engine.start()

        # Manually trigger cleanup
        await engine._cleanup_old_alerts()

        # Old alert should be removed
        assert alert.alert_id not in engine.alerts

        await engine.stop()

    @pytest.mark.asyncio
    async def test_audit_log_disabled(self, engine):
        """Test behavior when audit logging is disabled."""
        engine.config.audit_all_actions = False

        await engine.create_alert(
            "Test", "Test", "Test",
            AlertPriority.LOW, 0.1
        )

        # No audit logs should be created
        assert len(engine.audit_logs) == 0

    @pytest.mark.asyncio
    async def test_audit_log_size_limit(self, engine):
        """Test audit log size limiting."""
        # Create many audit entries
        for i in range(10005):
            await engine._audit_log(
                action=f"test_action_{i}",
                actor="system",
                target={"id": i},
                result="success"
            )

        # Should be limited to 5000 most recent
        assert len(engine.audit_logs) == 5000

    @pytest.mark.asyncio
    async def test_decision_without_notes(self, engine):
        """Test approving decision without notes."""
        alert = await engine.create_alert(
            "Test", "Test", "Test",
            AlertPriority.HIGH, 0.6,
            entities={"ip": "10.0.0.1"}
        )

        request = await engine.request_decision(
            alert.alert_id,
            DecisionType.BLOCK_IP,
            {"ip": "10.0.0.1"},
            "Block malicious IP"
        )

        # Approve without notes
        response = await engine.approve_decision(
            request.request_id,
            "admin"
        )

        assert response.status == ApprovalStatus.APPROVED
        # Alert should not have notes added
        assert len(alert.notes) == 0

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_time_filters(self, engine):
        """Test audit log retrieval with time filters."""
        # Create events at different times
        now = datetime.utcnow()

        await engine._audit_log("old_action", "user1", {}, "success")

        # Modify timestamp of first log
        engine.audit_logs[0].timestamp = now - timedelta(hours=2)

        await engine._audit_log("recent_action", "user2", {}, "success")

        # Get logs from last hour
        logs = await engine.get_audit_logs(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(minutes=1)
        )

        assert len(logs) == 1
        assert logs[0].action == "recent_action"

    @pytest.mark.asyncio
    async def test_stale_pending_alert_escalation(self, engine):
        """Test escalation of stale pending alerts."""
        engine.config.auto_escalate_after_minutes = 0.01  # Very short for testing

        alert = await engine.create_alert(
            "Stale Alert", "Test", "Test",
            AlertPriority.HIGH, 0.6
        )

        # Make alert appear old
        alert.created_at = datetime.utcnow() - timedelta(minutes=1)

        # Start engine and trigger cleanup
        engine._running = True

        # Manually check for stale alerts
        now = datetime.utcnow()
        for alert_id in list(engine.alerts_by_status[AlertStatus.PENDING]):
            if alert_id in engine.alerts:
                test_alert = engine.alerts[alert_id]
                age_minutes = (now - test_alert.created_at).total_seconds() / 60

                if age_minutes > engine.config.auto_escalate_after_minutes:
                    await engine._auto_escalate(test_alert)

        # Alert should be escalated
        assert alert.status == AlertStatus.ESCALATED

    @pytest.mark.asyncio
    async def test_no_related_alerts_empty_entities(self, engine):
        """Test finding related alerts when entities are empty."""
        alert1 = await engine.create_alert(
            "Alert 1", "Test", "Source1",
            AlertPriority.LOW, 0.2,
            entities={}
        )

        alert2 = await engine.create_alert(
            "Alert 2", "Test", "Source2",
            AlertPriority.LOW, 0.2,
            entities={}
        )

        # No common entities or source, should not be related
        assert alert1.alert_id not in alert2.related_alerts

    @pytest.mark.asyncio
    async def test_workflow_creation_on_first_decision(self, engine):
        """Test workflow is created on first decision request."""
        alert = await engine.create_alert(
            "Test", "Test", "Test",
            AlertPriority.MEDIUM, 0.5
        )

        # No workflow yet
        assert alert.alert_id not in engine.workflows

        # Request decision
        request = await engine.request_decision(
            alert.alert_id,
            DecisionType.INVESTIGATE,
            {},
            "Investigate"
        )

        # Workflow should be created
        assert alert.alert_id in engine.workflows
        workflow = engine.workflows[alert.alert_id]
        assert workflow.current_stage == "decision_pending"
        assert request.request_id in workflow.decisions_pending

    @pytest.mark.asyncio
    async def test_update_nonexistent_alert_status(self, engine):
        """Test updating status of non-existent alert."""
        success = await engine.update_alert_status(
            "nonexistent_id",
            AlertStatus.RESOLVED,
            "user",
            "Not found"
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_medium_priority_file_hash_entity(self, engine):
        """Test medium priority alert with file hash."""
        alert = await engine.create_alert(
            "Suspicious File",
            "Potential threat",
            "Scanner",
            priority=AlertPriority.MEDIUM,
            threat_score=0.55,
            entities={"file_hash": "def789", "filename": "suspicious.dll"}
        )

        # Medium priority should not get quarantine recommendation
        assert DecisionType.INVESTIGATE in alert.recommended_actions
        assert DecisionType.QUARANTINE_FILE not in alert.recommended_actions

    @pytest.mark.asyncio
    async def test_cleanup_task_cancellation(self, engine):
        """Test cleanup task proper cancellation."""
        await engine.start()
        assert engine._cleanup_task is not None

        # Stop should cancel cleanup task
        await engine.stop()

        # Task should be cancelled
        assert engine._cleanup_task.cancelled() or engine._cleanup_task.done()

    @pytest.mark.asyncio
    async def test_periodic_cleanup_with_exception(self, engine):
        """Test periodic cleanup continues despite exceptions."""
        engine._running = True

        # Mock cleanup to raise exception once
        call_count = 0
        original_cleanup = engine._cleanup_old_alerts

        async def cleanup_with_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Cleanup error")
            await original_cleanup()

        engine._cleanup_old_alerts = cleanup_with_error

        # Run cleanup loop briefly
        task = asyncio.create_task(engine._periodic_cleanup())
        await asyncio.sleep(0.1)

        # Stop the loop
        engine._running = False
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have attempted cleanup despite error
        assert call_count >= 1