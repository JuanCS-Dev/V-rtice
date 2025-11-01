"""Tests for Decision Audit Logger - Sophia Engine Decision Trail.

Validates audit logging, querying, statistics, and compliance features.

Biblical Foundation: Proverbs 4:11 - "I guide you in the way of wisdom"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
from datetime import datetime, timedelta

from core.decision_audit_logger import DecisionAuditLogger
import pytest

from models import InterventionDecision

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def audit_logger():
    """DecisionAuditLogger instance (in-memory storage)."""
    return DecisionAuditLogger(pool=None)


@pytest.fixture
def sample_risk_assessment():
    """Sample risk assessment dict."""
    return {
        "risk_score": 0.35,
        "risk_factors": [
            "no_precedent_found",
            "moderate_severity",
            "low_confidence",
        ],
    }


@pytest.fixture
def sample_precedents():
    """Sample precedents list."""
    return [
        {
            "case_id": "case-123",
            "similarity": 0.92,
            "outcome": "success",
            "patch_applied": "config_adjustment",
        },
        {
            "case_id": "case-456",
            "similarity": 0.78,
            "outcome": "success",
            "patch_applied": "restart_service",
        },
    ]


# ============================================================================
# TESTS: Decision Logging
# ============================================================================


class TestDecisionLogging:
    """Test basic decision logging functionality."""

    @pytest.mark.asyncio
    async def test_log_intervene_decision(
        self, audit_logger, sample_risk_assessment, sample_precedents
    ):
        """
        GIVEN: Sophia Engine makes INTERVENE decision
        WHEN: log_decision() is called
        THEN: Decision logged with all details
        """
        audit_id = await audit_logger.log_decision(
            anomaly_id="anomaly-001",
            decision=InterventionDecision.INTERVENE,
            reasoning="High severity anomaly with strong precedent match",
            risk_assessment=sample_risk_assessment,
            precedents=sample_precedents,
            sophia_wisdom="Há sabedoria em aprender com o passado",
        )

        assert audit_id is not None
        assert len(audit_id) > 0

        # Verify logged
        count = await audit_logger.count_decisions()
        assert count == 1

    @pytest.mark.asyncio
    async def test_log_observe_decision(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Sophia Engine makes OBSERVE_AND_WAIT decision
        WHEN: log_decision() is called
        THEN: Decision logged correctly
        """
        audit_id = await audit_logger.log_decision(
            anomaly_id="anomaly-002",
            decision=InterventionDecision.OBSERVE_AND_WAIT,
            reasoning="Transient failure pattern detected",
            risk_assessment={"risk_score": 0.15, "risk_factors": ["transient"]},
            precedents=[],
            sophia_wisdom="Há tempo certo para cada ação",
        )

        assert audit_id is not None

        # Retrieve decision
        decision = await audit_logger.get_decision_by_id(audit_id)
        assert decision["decision"] == InterventionDecision.OBSERVE_AND_WAIT.value
        assert decision["anomaly_id"] == "anomaly-002"

    @pytest.mark.asyncio
    async def test_log_escalate_decision(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Sophia Engine escalates to human
        WHEN: log_decision() is called
        THEN: Decision logged with escalation details
        """
        await audit_logger.log_decision(
            anomaly_id="anomaly-003",
            decision=InterventionDecision.HUMAN_CONSULTATION_REQUIRED,
            reasoning="Risk exceeds acceptable threshold",
            risk_assessment={"risk_score": 0.85, "risk_factors": ["high_risk"]},
            precedents=[],
            sophia_wisdom="A prudência é a marca da sabedoria",
        )

        count = await audit_logger.count_decisions()
        assert count == 1

    @pytest.mark.asyncio
    async def test_log_with_anomaly_details(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Decision with additional anomaly context
        WHEN: log_decision() called with anomaly_details
        THEN: Details preserved in audit entry
        """
        anomaly_details = {
            "service": "api-gateway",
            "severity": "P1",
            "metrics": {"latency_p99": 2500, "error_rate": 0.05},
        }

        audit_id = await audit_logger.log_decision(
            anomaly_id="anomaly-004",
            decision=InterventionDecision.INTERVENE,
            reasoning="Performance degradation detected",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Em momentos críticos, sabedoria também é agir",
            anomaly_details=anomaly_details,
        )

        decision = await audit_logger.get_decision_by_id(audit_id)
        assert decision["anomaly_details"]["service"] == "api-gateway"
        assert decision["anomaly_details"]["metrics"]["latency_p99"] == 2500


# ============================================================================
# TESTS: Querying Audit Trail
# ============================================================================


class TestAuditQuerying:
    """Test audit trail query functionality."""

    @pytest.mark.asyncio
    async def test_get_decisions_all(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Multiple decisions logged
        WHEN: get_decisions() called with no filters
        THEN: Returns all decisions
        """
        # Log 5 decisions
        for i in range(5):
            await audit_logger.log_decision(
                anomaly_id=f"anomaly-{i:03d}",
                decision=InterventionDecision.INTERVENE,
                reasoning=f"Reason {i}",
                risk_assessment=sample_risk_assessment,
                precedents=[],
                sophia_wisdom="Test wisdom",
            )

        decisions = await audit_logger.get_decisions()
        assert len(decisions) == 5

    @pytest.mark.asyncio
    async def test_get_decisions_by_anomaly_id(
        self, audit_logger, sample_risk_assessment
    ):
        """
        GIVEN: Decisions for multiple anomalies
        WHEN: get_decisions() called with anomaly_id filter
        THEN: Returns only matching decisions
        """
        await audit_logger.log_decision(
            anomaly_id="anomaly-A",
            decision=InterventionDecision.INTERVENE,
            reasoning="Reason A",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom A",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-B",
            decision=InterventionDecision.OBSERVE_AND_WAIT,
            reasoning="Reason B",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom B",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-A",
            decision=InterventionDecision.INTERVENE,
            reasoning="Reason A2",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom A2",
        )

        decisions = await audit_logger.get_decisions(anomaly_id="anomaly-A")
        assert len(decisions) == 2
        assert all(d["anomaly_id"] == "anomaly-A" for d in decisions)

    @pytest.mark.asyncio
    async def test_get_decisions_by_type(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Decisions of different types
        WHEN: get_decisions() called with decision_type filter
        THEN: Returns only matching type
        """
        await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Intervene",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-2",
            decision=InterventionDecision.OBSERVE_AND_WAIT,
            reasoning="Observe",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-3",
            decision=InterventionDecision.INTERVENE,
            reasoning="Intervene again",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        decisions = await audit_logger.get_decisions(
            decision_type=InterventionDecision.INTERVENE
        )
        assert len(decisions) == 2
        assert all(d["decision"] == "intervene" for d in decisions)

    @pytest.mark.asyncio
    async def test_get_decisions_since_timestamp(
        self, audit_logger, sample_risk_assessment
    ):
        """
        GIVEN: Decisions logged at different times
        WHEN: get_decisions() called with since filter
        THEN: Returns only recent decisions
        """
        # Log decision 1 hour ago (simulated)
        old_time = datetime.utcnow() - timedelta(hours=1)

        # Log first decision
        await audit_logger.log_decision(
            anomaly_id="anomaly-old",
            decision=InterventionDecision.INTERVENE,
            reasoning="Old decision",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # Manually adjust timestamp (for testing)
        if audit_logger.audit_trail:
            audit_logger.audit_trail[0]["timestamp"] = old_time.isoformat()

        # Wait a moment
        await asyncio.sleep(0.1)

        # Log recent decision
        await audit_logger.log_decision(
            anomaly_id="anomaly-new",
            decision=InterventionDecision.INTERVENE,
            reasoning="New decision",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # Query for decisions in last 30 minutes
        since = datetime.utcnow() - timedelta(minutes=30)
        decisions = await audit_logger.get_decisions(since=since)

        assert len(decisions) == 1
        assert decisions[0]["anomaly_id"] == "anomaly-new"

    @pytest.mark.asyncio
    async def test_get_decisions_limit(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Many decisions logged
        WHEN: get_decisions() called with limit
        THEN: Returns at most limit results
        """
        # Log 20 decisions
        for i in range(20):
            await audit_logger.log_decision(
                anomaly_id=f"anomaly-{i:03d}",
                decision=InterventionDecision.INTERVENE,
                reasoning=f"Reason {i}",
                risk_assessment=sample_risk_assessment,
                precedents=[],
                sophia_wisdom="Wisdom",
            )

        decisions = await audit_logger.get_decisions(limit=10)
        assert len(decisions) == 10

    @pytest.mark.asyncio
    async def test_decisions_sorted_newest_first(
        self, audit_logger, sample_risk_assessment
    ):
        """
        GIVEN: Multiple decisions logged sequentially
        WHEN: get_decisions() is called
        THEN: Results sorted by timestamp (newest first)
        """
        for i in range(3):
            await audit_logger.log_decision(
                anomaly_id=f"anomaly-{i}",
                decision=InterventionDecision.INTERVENE,
                reasoning=f"Reason {i}",
                risk_assessment=sample_risk_assessment,
                precedents=[],
                sophia_wisdom="Wisdom",
            )
            await asyncio.sleep(0.01)  # Ensure different timestamps

        decisions = await audit_logger.get_decisions()

        # Newest first
        assert decisions[0]["anomaly_id"] == "anomaly-2"
        assert decisions[1]["anomaly_id"] == "anomaly-1"
        assert decisions[2]["anomaly_id"] == "anomaly-0"


# ============================================================================
# TESTS: Decision Retrieval
# ============================================================================


class TestDecisionRetrieval:
    """Test retrieving individual decisions."""

    @pytest.mark.asyncio
    async def test_get_decision_by_id_exists(
        self, audit_logger, sample_risk_assessment
    ):
        """
        GIVEN: Decision logged
        WHEN: get_decision_by_id() called with valid ID
        THEN: Returns decision details
        """
        audit_id = await audit_logger.log_decision(
            anomaly_id="anomaly-001",
            decision=InterventionDecision.INTERVENE,
            reasoning="Test",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        decision = await audit_logger.get_decision_by_id(audit_id)

        assert decision is not None
        assert decision["audit_id"] == audit_id
        assert decision["anomaly_id"] == "anomaly-001"

    @pytest.mark.asyncio
    async def test_get_decision_by_id_not_found(self, audit_logger):
        """
        GIVEN: Empty audit trail
        WHEN: get_decision_by_id() called with non-existent ID
        THEN: Returns None
        """
        decision = await audit_logger.get_decision_by_id("non-existent-id")
        assert decision is None


# ============================================================================
# TESTS: Decision Statistics
# ============================================================================


class TestDecisionStatistics:
    """Test statistical analysis of decisions."""

    @pytest.mark.asyncio
    async def test_get_decision_stats_empty(self, audit_logger):
        """
        GIVEN: No decisions logged
        WHEN: get_decision_stats() is called
        THEN: Returns zero statistics
        """
        stats = await audit_logger.get_decision_stats()

        assert stats["total_decisions"] == 0
        assert stats["avg_risk_score"] == 0.0
        assert stats["precedents_used_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_get_decision_stats_with_data(self, audit_logger):
        """
        GIVEN: Multiple decisions logged
        WHEN: get_decision_stats() is called
        THEN: Returns accurate statistics
        """
        # Log decisions with different types and risks
        await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Reason 1",
            risk_assessment={"risk_score": 0.3, "risk_factors": []},
            precedents=[{"case_id": "c1", "similarity": 0.9}],
            sophia_wisdom="Wisdom",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-2",
            decision=InterventionDecision.OBSERVE_AND_WAIT,
            reasoning="Reason 2",
            risk_assessment={"risk_score": 0.5, "risk_factors": []},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-3",
            decision=InterventionDecision.INTERVENE,
            reasoning="Reason 3",
            risk_assessment={"risk_score": 0.2, "risk_factors": []},
            precedents=[{"case_id": "c2", "similarity": 0.85}],
            sophia_wisdom="Wisdom",
        )

        stats = await audit_logger.get_decision_stats()

        assert stats["total_decisions"] == 3
        assert stats["decision_breakdown"]["intervene"] == 2
        assert stats["decision_breakdown"]["observe"] == 1
        assert stats["avg_risk_score"] == pytest.approx(0.333, abs=0.01)
        assert stats["precedents_used_pct"] == pytest.approx(66.67, abs=0.1)

    @pytest.mark.asyncio
    async def test_get_decision_stats_time_filtered(self, audit_logger):
        """
        GIVEN: Decisions logged at different times
        WHEN: get_decision_stats() called with since parameter
        THEN: Returns stats only for recent decisions
        """
        # Log old decision
        await audit_logger.log_decision(
            anomaly_id="anomaly-old",
            decision=InterventionDecision.INTERVENE,
            reasoning="Old",
            risk_assessment={"risk_score": 0.9, "risk_factors": []},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # Manually adjust timestamp
        if audit_logger.audit_trail:
            old_time = datetime.utcnow() - timedelta(hours=2)
            audit_logger.audit_trail[0]["timestamp"] = old_time.isoformat()

        # Log recent decision
        await audit_logger.log_decision(
            anomaly_id="anomaly-new",
            decision=InterventionDecision.OBSERVE_AND_WAIT,
            reasoning="New",
            risk_assessment={"risk_score": 0.1, "risk_factors": []},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # Get stats for last hour
        since = datetime.utcnow() - timedelta(hours=1)
        stats = await audit_logger.get_decision_stats(since=since)

        assert stats["total_decisions"] == 1
        assert stats["decision_breakdown"]["observe"] == 1


# ============================================================================
# TESTS: High-Risk Decision Tracking
# ============================================================================


class TestHighRiskDecisions:
    """Test tracking and querying high-risk decisions."""

    @pytest.mark.asyncio
    async def test_get_high_risk_decisions_default_threshold(self, audit_logger):
        """
        GIVEN: Decisions with varying risk scores
        WHEN: get_high_risk_decisions() is called
        THEN: Returns only decisions above 0.7 risk
        """
        # Low risk
        await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Low risk",
            risk_assessment={"risk_score": 0.3, "risk_factors": []},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # High risk
        await audit_logger.log_decision(
            anomaly_id="anomaly-2",
            decision=InterventionDecision.HUMAN_CONSULTATION_REQUIRED,
            reasoning="High risk",
            risk_assessment={"risk_score": 0.85, "risk_factors": ["critical"]},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # Very high risk
        await audit_logger.log_decision(
            anomaly_id="anomaly-3",
            decision=InterventionDecision.HUMAN_CONSULTATION_REQUIRED,
            reasoning="Very high risk",
            risk_assessment={"risk_score": 0.95, "risk_factors": ["critical"]},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        high_risk = await audit_logger.get_high_risk_decisions()

        assert len(high_risk) == 2
        assert high_risk[0]["risk_score"] == 0.95  # Sorted by risk (highest first)
        assert high_risk[1]["risk_score"] == 0.85

    @pytest.mark.asyncio
    async def test_get_high_risk_decisions_custom_threshold(self, audit_logger):
        """
        GIVEN: Decisions with varying risk scores
        WHEN: get_high_risk_decisions() called with custom threshold
        THEN: Returns decisions above custom threshold
        """
        await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Moderate risk",
            risk_assessment={"risk_score": 0.5, "risk_factors": []},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-2",
            decision=InterventionDecision.INTERVENE,
            reasoning="Higher risk",
            risk_assessment={"risk_score": 0.6, "risk_factors": []},
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        high_risk = await audit_logger.get_high_risk_decisions(risk_threshold=0.4)

        assert len(high_risk) == 2


# ============================================================================
# TESTS: Audit Trail Export
# ============================================================================


class TestAuditExport:
    """Test export functionality for compliance/analysis."""

    @pytest.mark.asyncio
    async def test_export_json_format(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Decisions logged
        WHEN: export_audit_trail() called with json format
        THEN: Returns valid JSON export
        """
        await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Test",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        export = await audit_logger.export_audit_trail(format="json")

        import json

        data = json.loads(export)
        assert "exported_at" in data
        assert "decisions" in data
        assert len(data["decisions"]) == 1

    @pytest.mark.asyncio
    async def test_export_csv_format(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Decisions logged
        WHEN: export_audit_trail() called with csv format
        THEN: Returns valid CSV export
        """
        await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Test",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        export = await audit_logger.export_audit_trail(format="csv")

        lines = export.split("\n")
        assert len(lines) >= 2  # Header + at least 1 data row
        assert "timestamp" in lines[0]  # Header

    @pytest.mark.asyncio
    async def test_export_time_filtered(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Decisions at different times
        WHEN: export_audit_trail() called with since parameter
        THEN: Exports only recent decisions
        """
        # Log old decision
        await audit_logger.log_decision(
            anomaly_id="anomaly-old",
            decision=InterventionDecision.INTERVENE,
            reasoning="Old",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # Adjust timestamp
        if audit_logger.audit_trail:
            old_time = datetime.utcnow() - timedelta(days=2)
            audit_logger.audit_trail[0]["timestamp"] = old_time.isoformat()

        # Log recent
        await audit_logger.log_decision(
            anomaly_id="anomaly-new",
            decision=InterventionDecision.INTERVENE,
            reasoning="New",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        # Export last 24 hours
        since = datetime.utcnow() - timedelta(days=1)
        export = await audit_logger.export_audit_trail(since=since, format="json")

        import json

        data = json.loads(export)
        assert len(data["decisions"]) == 1


# ============================================================================
# TESTS: Precedent Tracking
# ============================================================================


class TestPrecedentTracking:
    """Test precedent similarity tracking in decisions."""

    @pytest.mark.asyncio
    async def test_best_precedent_similarity_single(
        self, audit_logger, sample_risk_assessment
    ):
        """
        GIVEN: Decision with single precedent
        WHEN: Decision logged
        THEN: best_precedent_similarity set correctly
        """
        precedent = [{"case_id": "c1", "similarity": 0.92, "outcome": "success"}]

        audit_id = await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Test",
            risk_assessment=sample_risk_assessment,
            precedents=precedent,
            sophia_wisdom="Wisdom",
        )

        decision = await audit_logger.get_decision_by_id(audit_id)
        assert decision["best_precedent_similarity"] == 0.92

    @pytest.mark.asyncio
    async def test_best_precedent_similarity_multiple(
        self, audit_logger, sample_risk_assessment
    ):
        """
        GIVEN: Decision with multiple precedents
        WHEN: Decision logged
        THEN: best_precedent_similarity is highest value
        """
        precedents = [
            {"case_id": "c1", "similarity": 0.75, "outcome": "success"},
            {"case_id": "c2", "similarity": 0.92, "outcome": "success"},
            {"case_id": "c3", "similarity": 0.81, "outcome": "failure"},
        ]

        audit_id = await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.INTERVENE,
            reasoning="Test",
            risk_assessment=sample_risk_assessment,
            precedents=precedents,
            sophia_wisdom="Wisdom",
        )

        decision = await audit_logger.get_decision_by_id(audit_id)
        assert decision["best_precedent_similarity"] == 0.92

    @pytest.mark.asyncio
    async def test_no_precedents(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Decision with no precedents
        WHEN: Decision logged
        THEN: best_precedent_similarity is None
        """
        audit_id = await audit_logger.log_decision(
            anomaly_id="anomaly-1",
            decision=InterventionDecision.OBSERVE_AND_WAIT,
            reasoning="No precedents",
            risk_assessment=sample_risk_assessment,
            precedents=[],
            sophia_wisdom="Wisdom",
        )

        decision = await audit_logger.get_decision_by_id(audit_id)
        assert decision["best_precedent_similarity"] is None


# ============================================================================
# TESTS: Concurrency and Thread Safety
# ============================================================================


class TestConcurrency:
    """Test thread-safe concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_logging(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Multiple concurrent log_decision() calls
        WHEN: Executed in parallel
        THEN: All logged correctly (no race conditions)
        """

        async def log_decision(i):
            return await audit_logger.log_decision(
                anomaly_id=f"anomaly-{i}",
                decision=InterventionDecision.INTERVENE,
                reasoning=f"Reason {i}",
                risk_assessment=sample_risk_assessment,
                precedents=[],
                sophia_wisdom=f"Wisdom {i}",
            )

        # Run 10 concurrent logs
        audit_ids = await asyncio.gather(*[log_decision(i) for i in range(10)])

        assert len(audit_ids) == 10
        assert len(set(audit_ids)) == 10  # All unique

        count = await audit_logger.count_decisions()
        assert count == 10


# ============================================================================
# TESTS: Administrative Operations
# ============================================================================


class TestAdministrativeOperations:
    """Test admin operations like clearing trail."""

    @pytest.mark.asyncio
    async def test_count_decisions(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Multiple decisions logged
        WHEN: count_decisions() is called
        THEN: Returns accurate count
        """
        for i in range(5):
            await audit_logger.log_decision(
                anomaly_id=f"anomaly-{i}",
                decision=InterventionDecision.INTERVENE,
                reasoning="Test",
                risk_assessment=sample_risk_assessment,
                precedents=[],
                sophia_wisdom="Wisdom",
            )

        count = await audit_logger.count_decisions()
        assert count == 5

    @pytest.mark.asyncio
    async def test_clear_audit_trail(self, audit_logger, sample_risk_assessment):
        """
        GIVEN: Decisions logged
        WHEN: clear_audit_trail() is called
        THEN: All decisions removed
        """
        # Log some decisions
        for i in range(3):
            await audit_logger.log_decision(
                anomaly_id=f"anomaly-{i}",
                decision=InterventionDecision.INTERVENE,
                reasoning="Test",
                risk_assessment=sample_risk_assessment,
                precedents=[],
                sophia_wisdom="Wisdom",
            )

        # Clear trail
        cleared = await audit_logger.clear_audit_trail()
        assert cleared == 3

        # Verify empty
        count = await audit_logger.count_decisions()
        assert count == 0


# ============================================================================
# INTEGRATION TEST: Full Audit Workflow
# ============================================================================


class TestFullAuditWorkflow:
    """Test complete audit trail workflow."""

    @pytest.mark.asyncio
    async def test_full_audit_lifecycle(self, audit_logger):
        """
        GIVEN: DecisionAuditLogger initialized
        WHEN: Multiple operations performed
        THEN: Complete audit trail maintained correctly
        """
        # Step 1: Log various decision types
        await audit_logger.log_decision(
            anomaly_id="anomaly-A",
            decision=InterventionDecision.INTERVENE,
            reasoning="P0 critical anomaly",
            risk_assessment={"risk_score": 0.45, "risk_factors": ["high_severity"]},
            precedents=[{"case_id": "c1", "similarity": 0.88}],
            sophia_wisdom="Em momentos críticos, sabedoria também é agir",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-B",
            decision=InterventionDecision.OBSERVE_AND_WAIT,
            reasoning="Transient pattern",
            risk_assessment={"risk_score": 0.12, "risk_factors": []},
            precedents=[],
            sophia_wisdom="Há tempo certo para cada ação",
        )

        await audit_logger.log_decision(
            anomaly_id="anomaly-C",
            decision=InterventionDecision.HUMAN_CONSULTATION_REQUIRED,
            reasoning="High risk intervention",
            risk_assessment={"risk_score": 0.88, "risk_factors": ["no_precedent"]},
            precedents=[],
            sophia_wisdom="A prudência é a marca da sabedoria",
        )

        # Step 2: Query and verify
        all_decisions = await audit_logger.get_decisions()
        assert len(all_decisions) == 3

        # Step 3: Get statistics
        stats = await audit_logger.get_decision_stats()
        assert stats["total_decisions"] == 3
        assert stats["decision_breakdown"]["intervene"] == 1
        assert stats["decision_breakdown"]["observe"] == 1
        assert stats["decision_breakdown"]["escalate"] == 1

        # Step 4: Find high-risk decisions
        high_risk = await audit_logger.get_high_risk_decisions(risk_threshold=0.7)
        assert len(high_risk) == 1
        assert high_risk[0]["anomaly_id"] == "anomaly-C"

        # Step 5: Export for compliance
        export = await audit_logger.export_audit_trail(format="json")
        assert len(export) > 0

        import json

        data = json.loads(export)
        assert len(data["decisions"]) == 3
