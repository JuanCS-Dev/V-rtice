"""
Comprehensive Coverage Tests for Guardian Base Framework

Surgical tests to achieve 100% coverage on guardian/base.py

Author: Claude Code
Date: 2025-10-14
Coverage Target: 100.00%
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from .base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianAgent,
    GuardianDecision,
    GuardianIntervention,
    GuardianPriority,
    GuardianReport,
    InterventionType,
    VetoAction,
)


# ============================================================================
# CONCRETE GUARDIAN FOR TESTING
# ============================================================================


class TestGuardian(GuardianAgent):
    """Concrete Guardian implementation for testing base class."""

    def __init__(self):
        super().__init__(
            guardian_id="test-guardian",
            article=ConstitutionalArticle.ARTICLE_II,
            name="Test Guardian",
            description="Guardian for testing",
        )
        self.monitor_called = False
        self.analyze_called = False
        self.intervene_called = False

    async def monitor(self) -> list[ConstitutionalViolation]:
        """Mock monitor that returns violations."""
        self.monitor_called = True
        return []

    async def analyze_violation(
        self, violation: ConstitutionalViolation
    ) -> GuardianDecision:
        """Mock analyze that returns decision."""
        self.analyze_called = True
        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type="alert",
            target="test_target",
            reasoning="Test reasoning",
            confidence=0.8,
            requires_validation=False,
        )

    async def intervene(
        self, violation: ConstitutionalViolation
    ) -> GuardianIntervention:
        """Mock intervene that returns intervention."""
        self.intervene_called = True
        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=InterventionType.ALERT,
            priority=violation.severity,
            violation=violation,
            action_taken="Test action",
            result="Test result",
            success=True,
        )

    def get_monitored_systems(self) -> list[str]:
        """Return list of monitored systems."""
        return ["test_system_1", "test_system_2"]


# ============================================================================
# DATA STRUCTURE TESTS
# ============================================================================


class TestConstitutionalViolation:
    """Test ConstitutionalViolation data structure."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test Clause",
            rule="Test Rule",
            description="Test description",
            severity=GuardianPriority.HIGH,
            context={"key": "value"},
            evidence=["evidence1", "evidence2"],
            affected_systems=["system1"],
            recommended_action="Fix it",
            metadata={"meta": "data"},
        )

        result = violation.to_dict()

        assert result["article"] == "ARTICLE_II"
        assert result["clause"] == "Test Clause"
        assert result["rule"] == "Test Rule"
        assert result["description"] == "Test description"
        assert result["severity"] == "HIGH"
        assert result["context"] == {"key": "value"}
        assert result["evidence"] == ["evidence1", "evidence2"]
        assert result["affected_systems"] == ["system1"]
        assert result["recommended_action"] == "Fix it"
        assert result["metadata"] == {"meta": "data"}
        assert "detected_at" in result
        assert "violation_id" in result

    def test_generate_hash(self):
        """Test hash generation for violation tracking."""
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            clause="Clause 1",
            rule="Rule 1",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            context={"file": "test.py"},
        )

        hash1 = violation.generate_hash()
        hash2 = violation.generate_hash()

        # Same violation should generate same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars


class TestVetoAction:
    """Test VetoAction data structure."""

    def test_is_active_no_expiry(self):
        """Test veto is active when no expiry set."""
        veto = VetoAction(
            guardian_id="test-guardian",
            target_action="deploy",
            target_system="production",
            reason="Test reason",
            expires_at=None,
        )

        assert veto.is_active() is True

    def test_is_active_future_expiry(self):
        """Test veto is active when expiry is in future."""
        veto = VetoAction(
            guardian_id="test-guardian",
            target_action="deploy",
            target_system="production",
            reason="Test reason",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        assert veto.is_active() is True

    def test_is_active_past_expiry(self):
        """Test veto is inactive when expiry has passed."""
        veto = VetoAction(
            guardian_id="test-guardian",
            target_action="deploy",
            target_system="production",
            reason="Test reason",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        assert veto.is_active() is False

    def test_to_dict(self):
        """Test veto conversion to dictionary."""
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.HIGH,
        )

        veto = VetoAction(
            guardian_id="test-guardian",
            target_action="deploy",
            target_system="production",
            violation=violation,
            reason="Test reason",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            override_allowed=True,
            override_requirements=["approval_required"],
            metadata={"key": "value"},
        )

        result = veto.to_dict()

        assert result["guardian_id"] == "test-guardian"
        assert result["target_action"] == "deploy"
        assert result["target_system"] == "production"
        assert result["violation"] is not None
        assert result["reason"] == "Test reason"
        assert result["is_active"] is True
        assert result["override_allowed"] is True
        assert result["override_requirements"] == ["approval_required"]
        assert result["metadata"] == {"key": "value"}

    def test_to_dict_no_violation(self):
        """Test veto to_dict when violation is None."""
        veto = VetoAction(
            guardian_id="test-guardian",
            target_action="deploy",
            target_system="production",
            violation=None,
            reason="Test reason",
        )

        result = veto.to_dict()

        assert result["violation"] is None


class TestGuardianIntervention:
    """Test GuardianIntervention data structure."""

    def test_to_dict(self):
        """Test intervention conversion to dictionary."""
        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_IV,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.CRITICAL,
        )

        intervention = GuardianIntervention(
            guardian_id="test-guardian",
            intervention_type=InterventionType.VETO,
            priority=GuardianPriority.CRITICAL,
            violation=violation,
            action_taken="Blocked deployment",
            result="Deployment blocked successfully",
            success=True,
            metadata={"reason": "critical_violation"},
        )

        result = intervention.to_dict()

        assert result["guardian_id"] == "test-guardian"
        assert result["intervention_type"] == "VETO"
        assert result["priority"] == "CRITICAL"
        assert result["violation"] is not None
        assert result["action_taken"] == "Blocked deployment"
        assert result["result"] == "Deployment blocked successfully"
        assert result["success"] is True
        assert result["metadata"] == {"reason": "critical_violation"}

    def test_to_dict_no_violation(self):
        """Test intervention to_dict when violation is None."""
        intervention = GuardianIntervention(
            guardian_id="test-guardian",
            intervention_type=InterventionType.ALERT,
            priority=GuardianPriority.LOW,
            violation=None,
            action_taken="Sent alert",
            result="Alert sent",
            success=True,
        )

        result = intervention.to_dict()

        assert result["violation"] is None


class TestGuardianDecision:
    """Test GuardianDecision data structure."""

    def test_to_dict(self):
        """Test decision conversion to dictionary."""
        decision = GuardianDecision(
            guardian_id="test-guardian",
            decision_type="veto",
            target="deployment.yaml",
            reasoning="Critical constitutional violation",
            confidence=0.95,
            requires_validation=False,
            metadata={"evidence": "file_scan"},
        )

        result = decision.to_dict()

        assert result["guardian_id"] == "test-guardian"
        assert result["decision_type"] == "veto"
        assert result["target"] == "deployment.yaml"
        assert result["reasoning"] == "Critical constitutional violation"
        assert result["confidence"] == 0.95
        assert result["requires_validation"] is False
        assert result["metadata"] == {"evidence": "file_scan"}
        assert "timestamp" in result


class TestGuardianReport:
    """Test GuardianReport data structure."""

    def test_to_dict(self):
        """Test report conversion to dictionary."""
        period_start = datetime.utcnow() - timedelta(hours=24)
        period_end = datetime.utcnow()

        report = GuardianReport(
            guardian_id="test-guardian",
            period_start=period_start,
            period_end=period_end,
            violations_detected=10,
            interventions_made=5,
            vetos_enacted=2,
            compliance_score=85.5,
            top_violations=["violation1", "violation2"],
            recommendations=["rec1", "rec2"],
            metrics={"avg_response_time": 1.5},
        )

        result = report.to_dict()

        assert result["guardian_id"] == "test-guardian"
        assert result["violations_detected"] == 10
        assert result["interventions_made"] == 5
        assert result["vetos_enacted"] == 2
        assert result["compliance_score"] == 85.5
        assert result["top_violations"] == ["violation1", "violation2"]
        assert result["recommendations"] == ["rec1", "rec2"]
        assert result["metrics"] == {"avg_response_time": 1.5}
        assert "period_start" in result
        assert "period_end" in result
        assert "generated_at" in result


# ============================================================================
# GUARDIAN AGENT LIFECYCLE TESTS
# ============================================================================


class TestGuardianAgentLifecycle:
    """Test Guardian Agent lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_guardian(self):
        """Test starting a guardian."""
        guardian = TestGuardian()

        assert not guardian.is_active()
        assert guardian._monitor_task is None

        await guardian.start()

        assert guardian.is_active()
        assert guardian._monitor_task is not None

        await guardian.stop()

    @pytest.mark.asyncio
    async def test_start_already_active(self):
        """Test starting guardian that's already active (idempotent)."""
        guardian = TestGuardian()

        await guardian.start()
        task1 = guardian._monitor_task

        await guardian.start()  # Second start should be no-op
        task2 = guardian._monitor_task

        assert task1 == task2  # Same task

        await guardian.stop()

    @pytest.mark.asyncio
    async def test_stop_guardian(self):
        """Test stopping a guardian."""
        guardian = TestGuardian()

        await guardian.start()
        assert guardian.is_active()

        await guardian.stop()

        assert not guardian.is_active()
        assert guardian._monitor_task is None

    @pytest.mark.asyncio
    async def test_stop_not_running(self):
        """Test stopping guardian that's not running (idempotent)."""
        guardian = TestGuardian()

        assert not guardian.is_active()

        await guardian.stop()  # Should not raise

        assert not guardian.is_active()

    @pytest.mark.asyncio
    async def test_monitoring_loop_calls_monitor(self):
        """Test that monitoring loop calls monitor() method."""
        guardian = TestGuardian()
        guardian._monitor_interval = 0.01  # Fast cycling for test

        await guardian.start()
        await asyncio.sleep(0.05)  # Let it cycle a few times
        await guardian.stop()

        assert guardian.monitor_called is True


# ============================================================================
# VIOLATION PROCESSING TESTS
# ============================================================================


class TestViolationProcessing:
    """Test violation processing and callbacks."""

    @pytest.mark.asyncio
    async def test_process_violation_records(self):
        """Test that processing a violation records it."""
        guardian = TestGuardian()

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test violation",
            severity=GuardianPriority.MEDIUM,
        )

        await guardian._process_violation(violation)

        assert violation in guardian._violations
        assert len(guardian._decisions) == 1

    @pytest.mark.asyncio
    async def test_process_violation_calls_callbacks(self):
        """Test that violation callbacks are triggered."""
        guardian = TestGuardian()
        callback_called = False
        callback_violation = None

        async def test_callback(v: ConstitutionalViolation):
            nonlocal callback_called, callback_violation
            callback_called = True
            callback_violation = v

        guardian.register_violation_callback(test_callback)

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.LOW,
        )

        await guardian._process_violation(violation)

        assert callback_called is True
        assert callback_violation == violation

    @pytest.mark.asyncio
    async def test_process_violation_block_decision(self):
        """Test processing violation with 'block' decision triggers intervention."""
        guardian = TestGuardian()

        # Override analyze to return block decision
        async def block_decision(v):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="block",
                target="test",
                reasoning="Block test",
                confidence=0.9,
            )

        guardian.analyze_violation = block_decision

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.HIGH,
        )

        await guardian._process_violation(violation)

        assert len(guardian._interventions) == 1
        assert guardian.intervene_called is True

    @pytest.mark.asyncio
    async def test_process_violation_veto_decision(self):
        """Test processing violation with 'veto' decision creates veto."""
        guardian = TestGuardian()

        # Override analyze to return veto decision
        async def veto_decision(v):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="veto",
                target="deployment",
                reasoning="Veto test",
                confidence=0.95,
            )

        guardian.analyze_violation = veto_decision

        # Override intervene to return VETO intervention
        async def veto_intervention(v):
            return GuardianIntervention(
                guardian_id=guardian.guardian_id,
                intervention_type=InterventionType.VETO,
                priority=v.severity,
                violation=v,
                action_taken="Vetoed",
                result="Veto applied",
                success=True,
            )

        guardian.intervene = veto_intervention

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.CRITICAL,
            affected_systems=["test_system"],
        )

        await guardian._process_violation(violation)

        assert len(guardian._vetos) == 1
        assert guardian._vetos[0].target_action == "deployment"

    @pytest.mark.asyncio
    async def test_process_violation_remediate_decision(self):
        """Test processing violation with 'remediate' decision."""
        guardian = TestGuardian()

        async def remediate_decision(v):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="remediate",
                target="test",
                reasoning="Remediate test",
                confidence=0.8,
            )

        guardian.analyze_violation = remediate_decision

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.MEDIUM,
        )

        await guardian._process_violation(violation)

        assert len(guardian._interventions) == 1

    @pytest.mark.asyncio
    async def test_intervention_callback_triggered(self):
        """Test that intervention callbacks are triggered."""
        guardian = TestGuardian()
        intervention_callback_called = False

        async def intervention_callback(i: GuardianIntervention):
            nonlocal intervention_callback_called
            intervention_callback_called = True

        guardian.register_intervention_callback(intervention_callback)

        async def block_decision(v):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="block",
                target="test",
                reasoning="Test",
                confidence=0.9,
            )

        guardian.analyze_violation = block_decision

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.HIGH,
        )

        await guardian._process_violation(violation)

        assert intervention_callback_called is True

    @pytest.mark.asyncio
    async def test_veto_callback_triggered(self):
        """Test that veto callbacks are triggered."""
        guardian = TestGuardian()
        veto_callback_called = False

        async def veto_callback(v: VetoAction):
            nonlocal veto_callback_called
            veto_callback_called = True

        guardian.register_veto_callback(veto_callback)

        async def veto_decision(v):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="veto",
                target="test",
                reasoning="Test",
                confidence=0.95,
            )

        guardian.analyze_violation = veto_decision

        async def veto_intervention(v):
            return GuardianIntervention(
                guardian_id=guardian.guardian_id,
                intervention_type=InterventionType.VETO,
                priority=v.severity,
                violation=v,
                action_taken="Vetoed",
                result="Veto applied",
                success=True,
            )

        guardian.intervene = veto_intervention

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.CRITICAL,
            affected_systems=["production"],
        )

        await guardian._process_violation(violation)

        assert veto_callback_called is True


# ============================================================================
# VETO POWER TESTS
# ============================================================================


class TestVetoPower:
    """Test Guardian veto power functionality."""

    @pytest.mark.asyncio
    async def test_veto_action_permanent(self):
        """Test creating permanent veto (no duration)."""
        guardian = TestGuardian()

        veto = await guardian.veto_action(
            action="deploy_to_production",
            system="maximus_core",
            reason="Contains NotImplementedError",
            duration_hours=None,
        )

        assert veto.guardian_id == guardian.guardian_id
        assert veto.target_action == "deploy_to_production"
        assert veto.target_system == "maximus_core"
        assert veto.reason == "Contains NotImplementedError"
        assert veto.expires_at is None
        assert veto.override_allowed is True
        assert veto in guardian._vetos

    @pytest.mark.asyncio
    async def test_veto_action_temporary(self):
        """Test creating temporary veto with expiration."""
        guardian = TestGuardian()

        veto = await guardian.veto_action(
            action="enable_feature",
            system="test_system",
            reason="Needs review",
            duration_hours=48,
        )

        assert veto.expires_at is not None
        expected_expiry = datetime.utcnow() + timedelta(hours=48)
        # Check within 1 second tolerance
        assert abs((veto.expires_at - expected_expiry).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_veto_action_triggers_callback(self):
        """Test that veto action triggers registered callbacks."""
        guardian = TestGuardian()
        callback_called = False

        async def veto_callback(v: VetoAction):
            nonlocal callback_called
            callback_called = True

        guardian.register_veto_callback(veto_callback)

        await guardian.veto_action(
            action="test_action",
            system="test_system",
            reason="Test",
            duration_hours=24,
        )

        assert callback_called is True

    def test_get_active_vetos_filters_expired(self):
        """Test that get_active_vetos filters out expired vetos."""
        guardian = TestGuardian()

        # Add active veto
        active_veto = VetoAction(
            guardian_id=guardian.guardian_id,
            target_action="action1",
            target_system="system1",
            reason="Active",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        # Add expired veto
        expired_veto = VetoAction(
            guardian_id=guardian.guardian_id,
            target_action="action2",
            target_system="system2",
            reason="Expired",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        # Add permanent veto
        permanent_veto = VetoAction(
            guardian_id=guardian.guardian_id,
            target_action="action3",
            target_system="system3",
            reason="Permanent",
            expires_at=None,
        )

        guardian._vetos = [active_veto, expired_veto, permanent_veto]

        active_vetos = guardian.get_active_vetos()

        assert len(active_vetos) == 2
        assert active_veto in active_vetos
        assert permanent_veto in active_vetos
        assert expired_veto not in active_vetos


# ============================================================================
# VETO CREATION TESTS
# ============================================================================


class Test_CreateVeto:
    """Test internal _create_veto method."""

    @pytest.mark.asyncio
    async def test_create_veto_high_confidence(self):
        """Test veto creation with high confidence (no override)."""
        guardian = TestGuardian()

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_V,
            clause="Section 1",
            rule="Test rule",
            description="Test",
            severity=GuardianPriority.CRITICAL,
            affected_systems=["critical_system"],
        )

        decision = GuardianDecision(
            guardian_id=guardian.guardian_id,
            decision_type="veto",
            target="deploy",
            reasoning="Critical violation",
            confidence=0.98,  # High confidence -> no override
        )

        veto = await guardian._create_veto(violation, decision)

        assert veto.override_allowed is False  # High confidence blocks override

    @pytest.mark.asyncio
    async def test_create_veto_low_confidence(self):
        """Test veto creation with low confidence (override allowed)."""
        guardian = TestGuardian()

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Section 2",
            rule="Test rule",
            description="Test",
            severity=GuardianPriority.MEDIUM,
            affected_systems=["test_system"],
        )

        decision = GuardianDecision(
            guardian_id=guardian.guardian_id,
            decision_type="veto",
            target="action",
            reasoning="Medium violation",
            confidence=0.80,  # Low confidence -> override allowed
        )

        veto = await guardian._create_veto(violation, decision)

        assert veto.override_allowed is True  # Low confidence allows override

    @pytest.mark.asyncio
    async def test_create_veto_no_affected_systems(self):
        """Test veto creation when violation has no affected systems."""
        guardian = TestGuardian()

        violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Test",
            description="Test",
            severity=GuardianPriority.HIGH,
            affected_systems=[],  # Empty
        )

        decision = GuardianDecision(
            guardian_id=guardian.guardian_id,
            decision_type="veto",
            target="action",
            reasoning="Test",
            confidence=0.9,
        )

        veto = await guardian._create_veto(violation, decision)

        assert veto.target_system == "unknown"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Test Guardian error handling."""

    @pytest.mark.asyncio
    async def test_monitor_error_creates_violation(self):
        """Test that monitoring errors create error violations."""
        guardian = TestGuardian()

        test_error = RuntimeError("Test monitoring error")

        await guardian._handle_monitor_error(test_error)

        assert len(guardian._violations) == 1
        error_violation = guardian._violations[0]
        assert "Guardian monitoring error" in error_violation.description
        assert error_violation.severity == GuardianPriority.HIGH
        assert error_violation.article == ConstitutionalArticle.ARTICLE_II

    @pytest.mark.asyncio
    async def test_monitoring_loop_handles_exception(self):
        """Test that monitoring loop catches and handles exceptions."""
        guardian = TestGuardian()

        # Make monitor() raise exception
        async def failing_monitor():
            raise RuntimeError("Monitor failure")

        guardian.monitor = failing_monitor
        guardian._monitor_interval = 0.01

        await guardian.start()
        await asyncio.sleep(0.05)  # Let it fail and handle
        await guardian.stop()

        # Should have created error violation
        assert len(guardian._violations) > 0


# ============================================================================
# REPORTING TESTS
# ============================================================================


class TestReporting:
    """Test Guardian reporting functionality."""

    def test_generate_report_empty(self):
        """Test report generation with no data."""
        guardian = TestGuardian()

        report = guardian.generate_report(period_hours=24)

        assert report.guardian_id == guardian.guardian_id
        assert report.violations_detected == 0
        assert report.interventions_made == 0
        assert report.vetos_enacted == 0
        assert report.compliance_score == 100.0

    def test_generate_report_with_violations(self):
        """Test report with violations in period."""
        guardian = TestGuardian()

        # Add violations
        for i in range(3):
            guardian._violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_II,
                    clause="Test",
                    rule=f"Rule {i}",
                    description=f"Violation {i}",
                    severity=GuardianPriority.MEDIUM,
                )
            )

        report = guardian.generate_report(period_hours=24)

        assert report.violations_detected == 3
        assert report.compliance_score < 100

    def test_generate_report_filters_by_period(self):
        """Test that report filters data by time period."""
        guardian = TestGuardian()

        # Add old violation (outside period)
        old_violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Old",
            description="Old",
            severity=GuardianPriority.LOW,
        )
        old_violation.detected_at = datetime.utcnow() - timedelta(hours=48)
        guardian._violations.append(old_violation)

        # Add recent violation (inside period)
        recent_violation = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="Test",
            rule="Recent",
            description="Recent",
            severity=GuardianPriority.HIGH,
        )
        guardian._violations.append(recent_violation)

        report = guardian.generate_report(period_hours=24)

        # Should only count recent violation
        assert report.violations_detected == 1

    def test_generate_report_top_violations(self):
        """Test top violations ranking in report."""
        guardian = TestGuardian()

        # Add multiple violations of same rule
        for i in range(5):
            guardian._violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_II,
                    clause="Clause A",
                    rule="Rule X",
                    description=f"Violation {i}",
                    severity=GuardianPriority.MEDIUM,
                )
            )

        # Add few violations of different rule
        for i in range(2):
            guardian._violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_III,
                    clause="Clause B",
                    rule="Rule Y",
                    description=f"Violation {i}",
                    severity=GuardianPriority.HIGH,
                )
            )

        report = guardian.generate_report(period_hours=24)

        assert len(report.top_violations) > 0
        # Top violation should be "Rule X" with 5 occurrences
        assert "Rule X" in report.top_violations[0]
        assert "5 occurrences" in report.top_violations[0]

    def test_generate_report_recommendations(self):
        """Test recommendation generation based on violation patterns."""
        guardian = TestGuardian()

        # Add many violations to trigger recommendations
        for i in range(15):
            guardian._violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_II,
                    clause="Test",
                    rule="Test",
                    description="Test",
                    severity=GuardianPriority.HIGH,
                )
            )

        report = guardian.generate_report(period_hours=24)

        assert len(report.recommendations) > 0
        assert any("High violation rate" in rec for rec in report.recommendations)

    def test_generate_report_with_vetos(self):
        """Test report includes veto information."""
        guardian = TestGuardian()

        # Add vetos
        for i in range(3):
            guardian._vetos.append(
                VetoAction(
                    guardian_id=guardian.guardian_id,
                    target_action=f"action{i}",
                    target_system="test",
                    reason="Test",
                )
            )

        report = guardian.generate_report(period_hours=24)

        assert report.vetos_enacted == 3
        assert any("veto" in rec.lower() for rec in report.recommendations)


# ============================================================================
# STATUS METHODS TESTS
# ============================================================================


class TestStatusMethods:
    """Test Guardian status and statistics methods."""

    def test_get_statistics(self):
        """Test get_statistics returns comprehensive data."""
        guardian = TestGuardian()

        # Add some data
        guardian._violations.append(
            ConstitutionalViolation(
                article=ConstitutionalArticle.ARTICLE_II,
                clause="Test",
                rule="Test",
                description="Test",
                severity=GuardianPriority.HIGH,
            )
        )

        guardian._decisions.append(
            GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="alert",
                target="test",
                reasoning="Test",
                confidence=0.8,
            )
        )

        stats = guardian.get_statistics()

        assert stats["guardian_id"] == guardian.guardian_id
        assert stats["name"] == "Test Guardian"
        assert stats["article"] == "ARTICLE_II"
        assert stats["is_active"] is False
        assert stats["total_violations"] == 1
        assert stats["total_decisions"] == 1
        assert stats["monitored_systems"] == ["test_system_1", "test_system_2"]

    def test_repr(self):
        """Test string representation of Guardian."""
        guardian = TestGuardian()

        repr_str = repr(guardian)

        assert "GuardianAgent" in repr_str
        assert "test-guardian" in repr_str
        assert "Test Guardian" in repr_str
        assert "ARTICLE_II" in repr_str
        assert "active=False" in repr_str
