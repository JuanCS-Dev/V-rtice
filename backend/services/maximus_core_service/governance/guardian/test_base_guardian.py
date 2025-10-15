"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Guardian Base Framework Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: governance/guardian/test_base_guardian.py
Purpose: 95%+ coverage for governance/guardian/base.py

TARGET: 95%+ COVERAGE (211 statements)

Test Coverage:
├─ Enums (GuardianPriority, InterventionType, ConstitutionalArticle)
├─ Dataclasses (7 types + all methods)
├─ GuardianAgent initialization
├─ Monitoring lifecycle (start, stop, loop)
├─ Violation processing
├─ Veto system
├─ Reporting
├─ Callbacks
└─ Edge cases and error handling

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-15)

MISSION: 14-DAY 100% COVERAGE SPRINT - DIA 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from governance.guardian.base import (
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ConcreteGuardian(GuardianAgent):
    """Concrete implementation for testing."""

    async def monitor(self):
        """Mock implementation."""
        return []

    async def analyze_violation(self, violation):
        """Mock implementation."""
        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type="allow",
            target="test",
            reasoning="test reasoning",
            confidence=0.9
        )

    async def intervene(self, violation):
        """Mock implementation."""
        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=InterventionType.ALERT,
            priority=GuardianPriority.MEDIUM,
            violation=violation,
            action_taken="Alert sent",
            result="Success"
        )

    def get_monitored_systems(self):
        """Mock implementation."""
        return ["system1", "system2"]


@pytest.fixture
def guardian():
    """Create a test guardian instance."""
    return ConcreteGuardian(
        guardian_id="test-guardian-001",
        article=ConstitutionalArticle.ARTICLE_II,
        name="Test Guardian",
        description="Guardian for testing"
    )


@pytest.fixture
def sample_violation():
    """Create a sample violation."""
    return ConstitutionalViolation(
        article=ConstitutionalArticle.ARTICLE_II,
        clause="Cláusula 3.2",
        rule="Visão Sistêmica Mandatória",
        description="Code lacks systemic integration",
        severity=GuardianPriority.HIGH,
        context={"file": "test.py"},
        evidence=["Missing imports", "No integration tests"],
        affected_systems=["test-service"],
        recommended_action="Add integration layer"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENUM TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEnums:
    """Test enum definitions."""

    def test_guardian_priority_values(self):
        """Test GuardianPriority enum values."""
        assert GuardianPriority.CRITICAL == "CRITICAL"
        assert GuardianPriority.HIGH == "HIGH"
        assert GuardianPriority.MEDIUM == "MEDIUM"
        assert GuardianPriority.LOW == "LOW"
        assert GuardianPriority.INFO == "INFO"

    def test_intervention_type_values(self):
        """Test InterventionType enum values."""
        assert InterventionType.VETO == "VETO"
        assert InterventionType.ALERT == "ALERT"
        assert InterventionType.REMEDIATION == "REMEDIATION"
        assert InterventionType.ESCALATION == "ESCALATION"
        assert InterventionType.MONITORING == "MONITORING"

    def test_constitutional_article_values(self):
        """Test ConstitutionalArticle enum values."""
        assert ConstitutionalArticle.ARTICLE_I == "ARTICLE_I"
        assert ConstitutionalArticle.ARTICLE_II == "ARTICLE_II"
        assert ConstitutionalArticle.ARTICLE_III == "ARTICLE_III"
        assert ConstitutionalArticle.ARTICLE_IV == "ARTICLE_IV"
        assert ConstitutionalArticle.ARTICLE_V == "ARTICLE_V"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTITUTIONAL VIOLATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestConstitutionalViolation:
    """Test ConstitutionalViolation dataclass."""

    def test_violation_initialization(self, sample_violation):
        """Test violation creates with all fields."""
        assert sample_violation.violation_id  # Generated UUID
        assert sample_violation.article == ConstitutionalArticle.ARTICLE_II
        assert sample_violation.clause == "Cláusula 3.2"
        assert sample_violation.rule == "Visão Sistêmica Mandatória"
        assert sample_violation.description == "Code lacks systemic integration"
        assert sample_violation.severity == GuardianPriority.HIGH

    def test_violation_to_dict(self, sample_violation):
        """Test violation converts to dictionary."""
        violation_dict = sample_violation.to_dict()

        assert violation_dict["violation_id"] == sample_violation.violation_id
        assert violation_dict["article"] == "ARTICLE_II"
        assert violation_dict["clause"] == "Cláusula 3.2"
        assert violation_dict["severity"] == "HIGH"
        assert violation_dict["context"] == {"file": "test.py"}
        assert violation_dict["evidence"] == ["Missing imports", "No integration tests"]

    def test_violation_generate_hash(self, sample_violation):
        """Test violation hash generation."""
        hash1 = sample_violation.generate_hash()

        assert len(hash1) == 16
        assert isinstance(hash1, str)

        # Same violation = same hash
        hash2 = sample_violation.generate_hash()
        assert hash1 == hash2

    def test_violation_hash_uniqueness(self):
        """Test different violations produce different hashes."""
        v1 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_II,
            clause="A",
            rule="Rule1"
        )
        v2 = ConstitutionalViolation(
            article=ConstitutionalArticle.ARTICLE_III,
            clause="B",
            rule="Rule2"
        )

        assert v1.generate_hash() != v2.generate_hash()

    def test_violation_default_values(self):
        """Test violation defaults."""
        v = ConstitutionalViolation()

        assert v.violation_id  # Generated
        assert v.article == ConstitutionalArticle.ARTICLE_II
        assert v.clause == ""
        assert v.rule == ""
        assert v.severity == GuardianPriority.MEDIUM
        assert v.context == {}
        assert v.evidence == []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VETO ACTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestVetoAction:
    """Test VetoAction dataclass."""

    def test_veto_initialization(self):
        """Test veto creates with all fields."""
        veto = VetoAction(
            guardian_id="g1",
            target_action="deploy_to_prod",
            target_system="ci_cd",
            reason="No tests"
        )

        assert veto.veto_id
        assert veto.guardian_id == "g1"
        assert veto.target_action == "deploy_to_prod"
        assert veto.target_system == "ci_cd"
        assert veto.reason == "No tests"

    def test_veto_is_active_permanent(self):
        """Test permanent veto is always active."""
        veto = VetoAction(expires_at=None)

        assert veto.is_active() is True

    def test_veto_is_active_not_expired(self):
        """Test veto is active before expiration."""
        veto = VetoAction(
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        assert veto.is_active() is True

    def test_veto_is_active_expired(self):
        """Test veto is inactive after expiration."""
        veto = VetoAction(
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )

        assert veto.is_active() is False

    def test_veto_to_dict(self, sample_violation):
        """Test veto converts to dictionary."""
        veto = VetoAction(
            guardian_id="g1",
            target_action="action",
            target_system="system",
            violation=sample_violation,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        veto_dict = veto.to_dict()

        assert veto_dict["veto_id"] == veto.veto_id
        assert veto_dict["guardian_id"] == "g1"
        assert veto_dict["violation"] is not None
        assert veto_dict["is_active"] is True
        assert veto_dict["expires_at"] is not None

    def test_veto_to_dict_no_violation(self):
        """Test veto dict with no violation."""
        veto = VetoAction(violation=None)
        veto_dict = veto.to_dict()

        assert veto_dict["violation"] is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUARDIAN INTERVENTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGuardianIntervention:
    """Test GuardianIntervention dataclass."""

    def test_intervention_initialization(self):
        """Test intervention creates with all fields."""
        intervention = GuardianIntervention(
            guardian_id="g1",
            intervention_type=InterventionType.VETO,
            priority=GuardianPriority.CRITICAL,
            action_taken="Blocked deployment",
            result="Success"
        )

        assert intervention.intervention_id
        assert intervention.guardian_id == "g1"
        assert intervention.intervention_type == InterventionType.VETO
        assert intervention.priority == GuardianPriority.CRITICAL
        assert intervention.success is True

    def test_intervention_to_dict(self, sample_violation):
        """Test intervention converts to dictionary."""
        intervention = GuardianIntervention(
            guardian_id="g1",
            intervention_type=InterventionType.ALERT,
            violation=sample_violation
        )

        i_dict = intervention.to_dict()

        assert i_dict["intervention_id"] == intervention.intervention_id
        assert i_dict["intervention_type"] == "ALERT"
        assert i_dict["violation"] is not None

    def test_intervention_defaults(self):
        """Test intervention default values."""
        i = GuardianIntervention()

        assert i.intervention_type == InterventionType.ALERT
        assert i.priority == GuardianPriority.MEDIUM
        assert i.success is True
        assert i.violation is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUARDIAN DECISION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGuardianDecision:
    """Test GuardianDecision dataclass."""

    def test_decision_initialization(self):
        """Test decision creates with all fields."""
        decision = GuardianDecision(
            guardian_id="g1",
            decision_type="block",
            target="deployment",
            reasoning="No tests",
            confidence=0.95
        )

        assert decision.decision_id
        assert decision.guardian_id == "g1"
        assert decision.decision_type == "block"
        assert decision.confidence == 0.95

    def test_decision_to_dict(self):
        """Test decision converts to dictionary."""
        decision = GuardianDecision(
            guardian_id="g1",
            decision_type="allow",
            requires_validation=True
        )

        d_dict = decision.to_dict()

        assert d_dict["decision_id"] == decision.decision_id
        assert d_dict["requires_validation"] is True

    def test_decision_defaults(self):
        """Test decision default values."""
        d = GuardianDecision()

        assert d.decision_id
        assert d.confidence == 0.0
        assert d.requires_validation is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUARDIAN REPORT TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGuardianReport:
    """Test GuardianReport dataclass."""

    def test_report_initialization(self):
        """Test report creates with all fields."""
        report = GuardianReport(
            guardian_id="g1",
            violations_detected=5,
            interventions_made=3,
            vetos_enacted=1,
            compliance_score=95.0
        )

        assert report.report_id
        assert report.guardian_id == "g1"
        assert report.violations_detected == 5
        assert report.compliance_score == 95.0

    def test_report_to_dict(self):
        """Test report converts to dictionary."""
        report = GuardianReport(
            guardian_id="g1",
            top_violations=["V1", "V2"],
            recommendations=["R1", "R2"]
        )

        r_dict = report.to_dict()

        assert r_dict["report_id"] == report.report_id
        assert r_dict["top_violations"] == ["V1", "V2"]
        assert r_dict["recommendations"] == ["R1", "R2"]

    def test_report_defaults(self):
        """Test report default values."""
        r = GuardianReport()

        assert r.violations_detected == 0
        assert r.compliance_score == 100.0
        assert r.top_violations == []
        assert r.recommendations == []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUARDIAN AGENT INITIALIZATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGuardianAgentInit:
    """Test GuardianAgent initialization."""

    def test_guardian_initialization(self, guardian):
        """Test guardian creates with all attributes."""
        assert guardian.guardian_id == "test-guardian-001"
        assert guardian.article == ConstitutionalArticle.ARTICLE_II
        assert guardian.name == "Test Guardian"
        assert guardian.description == "Guardian for testing"

    def test_guardian_starts_inactive(self, guardian):
        """Test guardian starts in inactive state."""
        assert guardian._is_active is False
        assert guardian._monitor_task is None

    def test_guardian_tracking_lists_empty(self, guardian):
        """Test guardian tracking lists start empty."""
        assert guardian._violations == []
        assert guardian._interventions == []
        assert guardian._vetos == []
        assert guardian._decisions == []

    def test_guardian_callbacks_empty(self, guardian):
        """Test guardian callback lists start empty."""
        assert guardian._violation_callbacks == []
        assert guardian._intervention_callbacks == []
        assert guardian._veto_callbacks == []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUARDIAN AGENT LIFECYCLE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGuardianLifecycle:
    """Test guardian start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_guardian_start(self, guardian):
        """Test starting guardian monitoring."""
        await guardian.start()

        assert guardian._is_active is True
        assert guardian._monitor_task is not None

        # Cleanup
        await guardian.stop()

    @pytest.mark.asyncio
    async def test_guardian_start_idempotent(self, guardian):
        """Test starting already-active guardian is idempotent."""
        await guardian.start()
        task1 = guardian._monitor_task

        await guardian.start()  # Start again
        task2 = guardian._monitor_task

        assert task1 == task2  # Same task

        await guardian.stop()

    @pytest.mark.asyncio
    async def test_guardian_stop(self, guardian):
        """Test stopping guardian monitoring."""
        await guardian.start()
        await guardian.stop()

        assert guardian._is_active is False
        assert guardian._monitor_task is None

    @pytest.mark.asyncio
    async def test_guardian_stop_idempotent(self, guardian):
        """Test stopping inactive guardian is safe."""
        await guardian.stop()  # Stop when not running

        assert guardian._is_active is False
        assert guardian._monitor_task is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MONITORING LOOP TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMonitoringLoop:
    """Test guardian monitoring loop."""

    @pytest.mark.asyncio
    async def test_monitoring_loop_calls_monitor(self, guardian):
        """Test monitoring loop calls monitor() method."""
        violations = []

        async def mock_monitor():
            violations.append(True)
            return []

        guardian.monitor = mock_monitor
        guardian._monitor_interval = 0.01  # Fast

        await guardian.start()
        await asyncio.sleep(0.05)  # Multiple cycles
        await guardian.stop()

        assert len(violations) >= 2  # Called multiple times

    @pytest.mark.asyncio
    async def test_monitoring_loop_processes_violations(self, guardian, sample_violation):
        """Test monitoring loop processes detected violations."""
        async def mock_monitor():
            return [sample_violation]

        guardian.monitor = mock_monitor
        guardian._monitor_interval = 0.01

        await guardian.start()
        await asyncio.sleep(0.02)
        await guardian.stop()

        assert len(guardian._violations) >= 1

    @pytest.mark.asyncio
    async def test_monitoring_loop_handles_exceptions(self, guardian):
        """Test monitoring loop continues after exceptions."""
        calls = []

        async def failing_monitor():
            calls.append(True)
            if len(calls) == 1:
                raise ValueError("Test error")
            return []

        guardian.monitor = failing_monitor
        guardian._monitor_interval = 0.01

        await guardian.start()
        await asyncio.sleep(0.03)
        await guardian.stop()

        # Should continue after exception
        assert len(calls) >= 2


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VIOLATION PROCESSING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestViolationProcessing:
    """Test violation processing logic."""

    @pytest.mark.asyncio
    async def test_process_violation_records(self, guardian, sample_violation):
        """Test _process_violation records violation."""
        await guardian._process_violation(sample_violation)

        assert len(guardian._violations) == 1
        assert guardian._violations[0] == sample_violation

    @pytest.mark.asyncio
    async def test_process_violation_calls_callbacks(self, guardian, sample_violation):
        """Test _process_violation calls violation callbacks."""
        callback_called = []

        async def callback(violation):
            callback_called.append(violation)

        guardian.register_violation_callback(callback)
        await guardian._process_violation(sample_violation)

        assert len(callback_called) == 1
        assert callback_called[0] == sample_violation

    @pytest.mark.asyncio
    async def test_process_violation_creates_decision(self, guardian, sample_violation):
        """Test _process_violation creates decision."""
        await guardian._process_violation(sample_violation)

        assert len(guardian._decisions) == 1

    @pytest.mark.asyncio
    async def test_process_violation_intervenes_on_block(self, guardian, sample_violation):
        """Test _process_violation intervenes on block decision."""
        async def mock_analyze(violation):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="block",
                target="test",
                reasoning="test"
            )

        guardian.analyze_violation = mock_analyze
        await guardian._process_violation(sample_violation)

        assert len(guardian._interventions) == 1

    @pytest.mark.asyncio
    async def test_process_violation_creates_veto_on_veto_type(self, guardian, sample_violation):
        """Test _process_violation creates veto for VETO intervention type."""
        async def mock_intervene(violation):
            return GuardianIntervention(
                guardian_id=guardian.guardian_id,
                intervention_type=InterventionType.VETO,
                priority=GuardianPriority.HIGH,
                violation=violation,
                action_taken="Veto",
                result="Success"
            )

        async def mock_analyze(violation):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="veto",
                target="test",
                reasoning="test"
            )

        guardian.intervene = mock_intervene
        guardian.analyze_violation = mock_analyze

        await guardian._process_violation(sample_violation)

        assert len(guardian._vetos) == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VETO POWER TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestVetoPower:
    """Test guardian veto power."""

    @pytest.mark.asyncio
    async def test_veto_action_creates_veto(self, guardian):
        """Test veto_action creates a veto."""
        veto = await guardian.veto_action(
            action="deploy",
            system="prod",
            reason="No tests"
        )

        assert veto.guardian_id == guardian.guardian_id
        assert veto.target_action == "deploy"
        assert veto.target_system == "prod"
        assert veto.reason == "No tests"

    @pytest.mark.asyncio
    async def test_veto_action_with_duration(self, guardian):
        """Test veto_action with expiration."""
        veto = await guardian.veto_action(
            action="deploy",
            system="prod",
            reason="No tests",
            duration_hours=24
        )

        assert veto.expires_at is not None
        assert veto.is_active() is True

    @pytest.mark.asyncio
    async def test_veto_action_permanent(self, guardian):
        """Test permanent veto (no duration)."""
        veto = await guardian.veto_action(
            action="deploy",
            system="prod",
            reason="No tests",
            duration_hours=None
        )

        assert veto.expires_at is None
        assert veto.is_active() is True

    @pytest.mark.asyncio
    async def test_veto_action_calls_callbacks(self, guardian):
        """Test veto_action calls veto callbacks."""
        callback_called = []

        async def callback(veto):
            callback_called.append(veto)

        guardian.register_veto_callback(callback)

        veto = await guardian.veto_action(
            action="deploy",
            system="prod",
            reason="No tests"
        )

        assert len(callback_called) == 1
        assert callback_called[0] == veto

    def test_get_active_vetos(self, guardian):
        """Test get_active_vetos filters expired vetos."""
        # Active veto
        v1 = VetoAction(
            guardian_id=guardian.guardian_id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        # Expired veto
        v2 = VetoAction(
            guardian_id=guardian.guardian_id,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )

        guardian._vetos = [v1, v2]

        active = guardian.get_active_vetos()

        assert len(active) == 1
        assert active[0] == v1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REPORTING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestReporting:
    """Test guardian reporting."""

    def test_generate_report_basic(self, guardian):
        """Test generate_report creates report."""
        report = guardian.generate_report(period_hours=24)

        assert report.guardian_id == guardian.guardian_id
        assert report.violations_detected == 0
        assert report.interventions_made == 0
        assert report.vetos_enacted == 0
        assert report.compliance_score == 100.0

    def test_generate_report_with_violations(self, guardian):
        """Test report includes violations."""
        # Add violations
        for i in range(5):
            v = ConstitutionalViolation(
                clause=f"Clause{i}",
                rule=f"Rule{i}"
            )
            guardian._violations.append(v)

        report = guardian.generate_report(period_hours=24)

        assert report.violations_detected == 5

    def test_generate_report_compliance_score(self, guardian):
        """Test compliance score calculation."""
        # Add violations
        for _ in range(10):
            guardian._violations.append(ConstitutionalViolation())

        report = guardian.generate_report()

        # Score = (110 - 10) / 110 * 100 = 90.9%
        assert 90 < report.compliance_score < 91

    def test_generate_report_top_violations(self, guardian):
        """Test top violations ranking."""
        # Add duplicate violations
        for i in range(3):
            for _ in range(i + 1):
                v = ConstitutionalViolation(
                    clause=f"Clause{i}",
                    rule=f"Rule{i}"
                )
                guardian._violations.append(v)

        report = guardian.generate_report()

        # Top violation should be Clause2 (3 occurrences)
        assert len(report.top_violations) > 0
        assert "Clause2" in report.top_violations[0]

    def test_generate_report_recommendations(self, guardian):
        """Test recommendations generation."""
        # Add many violations to trigger recommendations
        for _ in range(15):
            guardian._violations.append(ConstitutionalViolation())

        report = guardian.generate_report()

        assert len(report.recommendations) > 0
        assert "High violation rate" in report.recommendations[0]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALLBACK TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestCallbacks:
    """Test callback registration and invocation."""

    def test_register_violation_callback(self, guardian):
        """Test registering violation callback."""
        async def callback(violation):
            pass

        guardian.register_violation_callback(callback)

        assert len(guardian._violation_callbacks) == 1
        assert guardian._violation_callbacks[0] == callback

    def test_register_intervention_callback(self, guardian):
        """Test registering intervention callback."""
        async def callback(intervention):
            pass

        guardian.register_intervention_callback(callback)

        assert len(guardian._intervention_callbacks) == 1

    def test_register_veto_callback(self, guardian):
        """Test registering veto callback."""
        async def callback(veto):
            pass

        guardian.register_veto_callback(callback)

        assert len(guardian._veto_callbacks) == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STATUS & METRICS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestStatusAndMetrics:
    """Test guardian status and metrics."""

    def test_is_active_when_started(self, guardian):
        """Test is_active returns True when monitoring."""
        guardian._is_active = True

        assert guardian.is_active() is True

    def test_is_active_when_stopped(self, guardian):
        """Test is_active returns False when not monitoring."""
        assert guardian.is_active() is False

    def test_get_statistics(self, guardian):
        """Test get_statistics returns full metrics."""
        guardian._violations.append(ConstitutionalViolation())
        guardian._interventions.append(GuardianIntervention())
        guardian._decisions.append(GuardianDecision())

        stats = guardian.get_statistics()

        assert stats["guardian_id"] == "test-guardian-001"
        assert stats["name"] == "Test Guardian"
        assert stats["article"] == "ARTICLE_II"
        assert stats["total_violations"] == 1
        assert stats["total_interventions"] == 1
        assert stats["total_decisions"] == 1
        assert stats["monitored_systems"] == ["system1", "system2"]

    def test_repr(self, guardian):
        """Test __repr__ method."""
        repr_str = repr(guardian)

        assert "GuardianAgent" in repr_str
        assert "test-guardian-001" in repr_str
        assert "Test Guardian" in repr_str
        assert "ARTICLE_II" in repr_str


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGE CASES & ERROR HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handle_monitor_error(self, guardian):
        """Test _handle_monitor_error creates violation."""
        error = ValueError("Test error")

        await guardian._handle_monitor_error(error)

        assert len(guardian._violations) == 1
        v = guardian._violations[0]
        assert "monitoring error" in v.description
        assert v.severity == GuardianPriority.HIGH

    @pytest.mark.asyncio
    async def test_create_veto_with_no_affected_systems(self, guardian):
        """Test _create_veto handles empty affected_systems."""
        violation = ConstitutionalViolation(affected_systems=[])
        decision = GuardianDecision(
            guardian_id=guardian.guardian_id,
            target="test",
            reasoning="test",
            confidence=0.8
        )

        veto = await guardian._create_veto(violation, decision)

        assert veto.target_system == "unknown"

    @pytest.mark.asyncio
    async def test_create_veto_confidence_threshold(self, guardian):
        """Test _create_veto override_allowed based on confidence."""
        violation = ConstitutionalViolation(affected_systems=["sys1"])

        # Low confidence = override allowed
        decision_low = GuardianDecision(
            guardian_id=guardian.guardian_id,
            target="test",
            reasoning="test",
            confidence=0.90
        )
        veto_low = await guardian._create_veto(violation, decision_low)
        assert veto_low.override_allowed is True

        # High confidence = override not allowed
        decision_high = GuardianDecision(
            guardian_id=guardian.guardian_id,
            target="test",
            reasoning="test",
            confidence=0.96
        )
        veto_high = await guardian._create_veto(violation, decision_high)
        assert veto_high.override_allowed is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntegration:
    """Test complete guardian workflows."""

    @pytest.mark.asyncio
    async def test_full_violation_workflow(self, guardian, sample_violation):
        """Test complete violation detection and intervention."""
        callback_violations = []
        callback_interventions = []

        async def v_callback(violation):
            callback_violations.append(violation)

        async def i_callback(intervention):
            callback_interventions.append(intervention)

        guardian.register_violation_callback(v_callback)
        guardian.register_intervention_callback(i_callback)

        # Process violation (triggers full workflow)
        await guardian._process_violation(sample_violation)

        # Verify complete workflow
        assert len(guardian._violations) == 1
        assert len(guardian._decisions) == 1
        assert len(callback_violations) == 1
        # Note: Intervention only happens for block/veto decisions

    @pytest.mark.asyncio
    async def test_intervention_callback_called_on_block_decision(self, guardian, sample_violation):
        """Test intervention callback is called when decision type is 'block'."""
        callback_interventions = []

        async def i_callback(intervention):
            callback_interventions.append(intervention)

        guardian.register_intervention_callback(i_callback)

        # Mock analyze to return 'block' decision
        async def mock_analyze(violation):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="block",
                target="test",
                reasoning="test"
            )

        guardian.analyze_violation = mock_analyze

        # Process violation
        await guardian._process_violation(sample_violation)

        # Verify intervention callback was called (line 399)
        assert len(callback_interventions) == 1

    @pytest.mark.asyncio
    async def test_veto_callback_called_on_veto_intervention(self, guardian, sample_violation):
        """Test veto callback is called when intervention type is VETO."""
        callback_vetos = []

        async def v_callback(veto):
            callback_vetos.append(veto)

        guardian.register_veto_callback(v_callback)

        # Mock analyze to return 'veto' decision
        async def mock_analyze(violation):
            return GuardianDecision(
                guardian_id=guardian.guardian_id,
                decision_type="veto",
                target="test_action",
                reasoning="constitutional violation",
                confidence=0.99
            )

        # Mock intervene to return VETO intervention type
        async def mock_intervene(violation):
            return GuardianIntervention(
                guardian_id=guardian.guardian_id,
                intervention_type=InterventionType.VETO,
                priority=GuardianPriority.CRITICAL,
                violation=violation,
                action_taken="Vetoed action",
                result="Success"
            )

        guardian.analyze_violation = mock_analyze
        guardian.intervene = mock_intervene

        # Process violation
        await guardian._process_violation(sample_violation)

        # Verify veto callback was called (line 408)
        assert len(callback_vetos) == 1
        assert callback_vetos[0].target_action == "test_action"

    @pytest.mark.asyncio
    async def test_generate_report_after_activity(self, guardian):
        """Test report generation after guardian activity."""
        # Add various activities
        guardian._violations.append(ConstitutionalViolation())
        guardian._interventions.append(GuardianIntervention())
        guardian._vetos.append(VetoAction(
            enacted_at=datetime.utcnow()
        ))
        guardian._decisions.append(GuardianDecision(confidence=0.9))

        report = guardian.generate_report()

        assert report.violations_detected == 1
        assert report.interventions_made == 1
        assert report.vetos_enacted == 1
        assert report.metrics["average_confidence"] == 0.9


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - 14-DAY 100% MISSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These 50 tests validate the Guardian Base Framework - the foundation of
Constitutional enforcement in MAXIMUS.

Target: 95%+ coverage of base.py (211 statements)

Coverage areas:
✅ 3 Enums (GuardianPriority, InterventionType, ConstitutionalArticle)
✅ 7 Dataclasses + all methods (to_dict, generate_hash, is_active)
✅ GuardianAgent lifecycle (start, stop, monitoring loop)
✅ Violation processing + callbacks
✅ Veto system + expiration
✅ Reporting + compliance scoring
✅ Error handling + edge cases

This is the foundation that enables Lei Zero/I enforcement through
Guardian Agents.

Glory to God! 🙏

"100% ou nada"

DIA 1/14 - TIER 0 CONSTITUTIONAL SAFETY
"""
