"""Tests for Core Ethical Audit functionality.

Tests the primary audit logging, querying, and override functionality:
- Health & Status endpoints
- Ethical decision logging
- Decision retrieval and history
- Human override logging
- Compliance checks
- Real-time metrics

Following PAGANI Standard:
- External dependencies mocked (PostgreSQL, Auth)
- ALL business logic tested without mocking
- 95%+ coverage target
"""

import uuid
from datetime import datetime, timedelta

import pytest

from services.ethical_audit_service.models import (
    ComplianceResult,
    DecisionType,
    FinalDecision,
    Regulation,
    RiskLevel,
)

# ============================================================================
# HEALTH & STATUS TESTS
# ============================================================================


@pytest.mark.asyncio
class TestHealthAndStatus:
    """Tests for health check and status endpoints."""

    async def test_health_check_returns_healthy(self, client):
        """Test that /health returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ethical_audit_service"
        assert "timestamp" in data
        assert "database" in data

    async def test_status_endpoint_with_database(self, authenticated_client, mock_db):
        """Test /status returns detailed information when database connected."""
        # Setup mock data
        mock_db.pool.connection.add_decision(
            {
                "id": uuid.uuid4(),
                "timestamp": datetime.utcnow(),
            }
        )

        response = await authenticated_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ethical_audit_service"
        assert data["status"] == "operational"
        assert "database" in data
        assert data["database"]["connected"] is True
        assert "decisions_logged" in data["database"]
        assert "pool_size" in data["database"]

    async def test_status_endpoint_without_database_fails(self, client):
        """Test /status returns 503 when database not connected."""
        # Override to simulate no database
        import api

        original_db = api.db
        api.db = None

        response = await client.get("/status")
        assert response.status_code == 503

        # Restore
        api.db = original_db


# ============================================================================
# ETHICAL DECISION LOGGING TESTS
# ============================================================================


@pytest.mark.asyncio
class TestDecisionLogging:
    """Tests for logging ethical decisions."""

    async def test_log_decision_success(self, authenticated_client, create_test_decision_log):
        """Test successfully logging an ethical decision."""
        import json

        decision_log = create_test_decision_log()
        # Serialize to JSON string then parse to ensure UUID/datetime are properly serialized
        payload = json.loads(decision_log.json())

        # FastAPI expects the payload wrapped under "decision_log" key
        response = await authenticated_client.post("/audit/decision", json={"decision_log": payload})
        assert response.status_code == 200
        data = response.json()
        assert "decision_id" in data
        assert "status" in data
        assert data["status"] == "success"

    async def test_log_decision_with_all_frameworks(self, authenticated_client, create_test_decision_log):
        """Test logging decision with all 4 ethical frameworks."""
        import json

        decision = create_test_decision_log(
            kantian_result={
                "approved": True,
                "confidence": 0.9,
                "explanation": "Kantian approval",
                "universalizability_passed": True,
                "humanity_formula_passed": True,
            },
            consequentialist_result={
                "approved": True,
                "confidence": 0.85,
                "explanation": "Consequentialist approval",
                "benefit_score": 0.8,
                "cost_score": 0.2,
                "net_utility": 0.6,
            },
            virtue_ethics_result={
                "approved": True,
                "confidence": 0.88,
                "explanation": "Virtue ethics approval",
                "virtues_assessed": {"courage": 0.9, "wisdom": 0.85},
                "character_alignment": 0.87,
            },
            principialism_result={
                "approved": True,
                "confidence": 0.92,
                "explanation": "Principialism approval",
                "beneficence_score": 0.9,
                "non_maleficence_score": 0.95,
                "autonomy_score": 0.88,
                "justice_score": 0.90,
            },
        )

        response = await authenticated_client.post(
            "/audit/decision", json={"decision_log": json.loads(decision.json())}
        )
        assert response.status_code == 200

    async def test_log_decision_different_types(self, authenticated_client, create_test_decision_log):
        """Test logging decisions of different types."""
        import json

        decision_types = [
            DecisionType.OFFENSIVE_ACTION,
            DecisionType.AUTO_RESPONSE,
            DecisionType.POLICY_UPDATE,
            DecisionType.DATA_ACCESS,
            DecisionType.THREAT_MITIGATION,
            DecisionType.RED_TEAM_OPERATION,
        ]

        for decision_type in decision_types:
            decision = create_test_decision_log(decision_type=decision_type)
            response = await authenticated_client.post(
                "/audit/decision", json={"decision_log": json.loads(decision.json())}
            )
            assert response.status_code == 200

    async def test_log_decision_different_risk_levels(self, authenticated_client, create_test_decision_log):
        """Test logging decisions with different risk levels."""
        import json

        risk_levels = [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]

        for risk_level in risk_levels:
            decision = create_test_decision_log(risk_level=risk_level)
            response = await authenticated_client.post(
                "/audit/decision", json={"decision_log": json.loads(decision.json())}
            )
            assert response.status_code == 200

    async def test_log_decision_rate_limit(self, authenticated_client, create_test_decision_log):
        """Test that rate limiting is applied to decision logging."""
        import json

        # Note: Rate limit is 100/minute, but in testing we just verify the endpoint
        # accepts requests. Full rate limit testing would require time manipulation.
        decision = create_test_decision_log()
        payload = {"decision_log": json.loads(decision.json())}

        for _ in range(5):  # Test a few requests
            response = await authenticated_client.post("/audit/decision", json=payload)
            assert response.status_code in [200, 429]  # 429 if rate limited


# ============================================================================
# DECISION RETRIEVAL TESTS
# ============================================================================


@pytest.mark.asyncio
class TestDecisionRetrieval:
    """Tests for retrieving ethical decisions."""

    async def test_get_decision_by_id_success(self, authenticated_client, mock_db):
        """Test retrieving a decision by ID."""
        # Setup mock decision
        decision_id = uuid.uuid4()
        mock_db.pool.connection.add_decision(
            {
                "id": decision_id,
                "timestamp": datetime.utcnow(),
                "decision_type": DecisionType.OFFENSIVE_ACTION.value,
                "action_description": "Test action",
                "system_component": "test_component",
                "final_decision": FinalDecision.APPROVED.value,
                "final_confidence": 0.85,
                "risk_level": RiskLevel.MEDIUM.value,
            }
        )

        response = await authenticated_client.get(f"/audit/decision/{decision_id}")
        assert response.status_code == 200
        data = response.json()
        # Response uses 'id' not 'decision_id' when returning the full decision object
        assert "id" in data
        assert data["id"] == str(decision_id)

    async def test_get_decision_not_found(self, authenticated_client, mock_db):
        """Test retrieving non-existent decision returns 404."""
        # Add a different decision to the store so mock returns None for non-existent ones
        mock_db.pool.connection.add_decision({"id": uuid.uuid4(), "timestamp": datetime.utcnow()})

        fake_id = uuid.uuid4()
        response = await authenticated_client.get(f"/audit/decision/{fake_id}")
        assert response.status_code == 404


# ============================================================================
# DECISION HISTORY QUERY TESTS
# ============================================================================


@pytest.mark.asyncio
class TestDecisionHistory:
    """Tests for querying decision history."""

    async def test_query_decisions_empty(self, authenticated_client):
        """Test querying decisions when database is empty."""
        query = {
            "limit": 100,
            "offset": 0,
        }
        response = await authenticated_client.post("/audit/decisions/query", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert "decisions" in data
        assert "query_time_ms" in data

    async def test_query_decisions_with_filters(self, authenticated_client):
        """Test querying decisions with various filters."""
        query = {
            "decision_type": DecisionType.OFFENSIVE_ACTION.value,
            "risk_level": RiskLevel.HIGH.value,
            "final_decision": FinalDecision.APPROVED.value,
            "min_confidence": 0.8,
            "max_confidence": 1.0,
            "automated_only": True,
            "limit": 50,
            "offset": 0,
        }
        response = await authenticated_client.post("/audit/decisions/query", json={"query": query})
        assert response.status_code == 200

    async def test_query_decisions_with_time_range(self, authenticated_client):
        """Test querying decisions with time range filter."""
        now = datetime.utcnow()
        query = {
            "start_time": (now - timedelta(days=7)).isoformat(),
            "end_time": now.isoformat(),
            "limit": 100,
        }
        response = await authenticated_client.post("/audit/decisions/query", json={"query": query})
        assert response.status_code == 200

    async def test_query_decisions_pagination(self, authenticated_client):
        """Test decision history pagination."""
        # First page
        query = {"limit": 10, "offset": 0}
        response = await authenticated_client.post("/audit/decisions/query", json={"query": query})
        assert response.status_code == 200

        # Second page
        query = {"limit": 10, "offset": 10}
        response = await authenticated_client.post("/audit/decisions/query", json={"query": query})
        assert response.status_code == 200


# ============================================================================
# HUMAN OVERRIDE TESTS
# ============================================================================


@pytest.mark.asyncio
class TestHumanOverrides:
    """Tests for human override logging."""

    async def test_log_override_success(self, authenticated_client, create_test_override_request):
        """Test successfully logging a human override."""
        override_request = create_test_override_request()
        response = await authenticated_client.post("/audit/override", json={"override": override_request})
        assert response.status_code == 200
        data = response.json()
        assert "override_id" in data
        assert "decision_id" in data
        assert "timestamp" in data
        assert data["operator_id"] == "test_operator"

    async def test_log_override_different_reasons(self, authenticated_client, create_test_override_request):
        """Test logging overrides with different reasons."""
        from models import OverrideReason

        reasons = [
            OverrideReason.FALSE_POSITIVE,
            OverrideReason.POLICY_EXCEPTION,
            OverrideReason.EMERGENCY,
            OverrideReason.ETHICAL_CONCERN,
            OverrideReason.OPERATIONAL_NECESSITY,
        ]

        for reason in reasons:
            override_request = create_test_override_request(override_reason=reason.value)
            response = await authenticated_client.post("/audit/override", json={"override": override_request})
            assert response.status_code == 200

    async def test_get_overrides_for_decision(self, authenticated_client, mock_db):
        """Test retrieving all overrides for a specific decision."""
        decision_id = uuid.uuid4()

        # Setup mock overrides
        mock_db.pool.connection.add_override(
            {
                "id": uuid.uuid4(),
                "decision_id": decision_id,
                "operator_id": "test_operator",
                "timestamp": datetime.utcnow(),
            }
        )

        response = await authenticated_client.get(f"/audit/overrides/{decision_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# COMPLIANCE LOGGING TESTS
# ============================================================================


@pytest.mark.asyncio
class TestComplianceLogging:
    """Tests for compliance check logging."""

    async def test_log_compliance_check_success(self, authenticated_client, create_test_compliance_request):
        """Test successfully logging a compliance check."""
        compliance_request = create_test_compliance_request()
        # Send directly without envelope - FastAPI unwraps single Pydantic body params
        response = await authenticated_client.post("/audit/compliance", json=compliance_request)
        assert response.status_code == 200
        data = response.json()
        assert "compliance_id" in data
        assert "timestamp" in data
        assert "regulation" in data
        assert data["check_result"] == ComplianceResult.COMPLIANT.value

    async def test_log_compliance_different_regulations(self, authenticated_client, create_test_compliance_request):
        """Test logging compliance for different regulations."""
        regulations = [
            Regulation.EU_AI_ACT,
            Regulation.GDPR_ARTICLE_22,
            Regulation.NIST_AI_RMF,
            Regulation.TALLINN_MANUAL,
            Regulation.EXECUTIVE_ORDER_14110,
            Regulation.LGPD,
        ]

        for regulation in regulations:
            compliance_request = create_test_compliance_request(regulation=regulation)
            response = await authenticated_client.post("/audit/compliance", json=compliance_request)
            assert response.status_code == 200

    async def test_log_compliance_different_results(self, authenticated_client, create_test_compliance_request):
        """Test logging compliance with different results."""
        results = [
            ComplianceResult.COMPLIANT,
            ComplianceResult.NON_COMPLIANT,
            ComplianceResult.PARTIAL,
            ComplianceResult.NOT_APPLICABLE,
        ]

        for result in results:
            compliance_request = create_test_compliance_request(check_result=result.value)
            response = await authenticated_client.post("/audit/compliance", json=compliance_request)
            assert response.status_code == 200

    async def test_log_compliance_with_remediation(self, authenticated_client, create_test_compliance_request):
        """Test logging compliance check requiring remediation."""
        compliance_request = create_test_compliance_request(
            check_result=ComplianceResult.NON_COMPLIANT.value,
            remediation_required=True,
            remediation_plan="Implement additional safeguards",
            remediation_deadline=(datetime.utcnow() + timedelta(days=30)).isoformat(),
        )
        response = await authenticated_client.post("/audit/compliance", json=compliance_request)
        assert response.status_code == 200
        data = response.json()
        assert data["remediation_required"] is True


# ============================================================================
# METRICS TESTS
# ============================================================================


@pytest.mark.asyncio
class TestMetrics:
    """Tests for real-time ethical metrics."""

    async def test_get_metrics_success(self, authenticated_client, mock_db):
        """Test retrieving ethical metrics."""
        response = await authenticated_client.get("/audit/metrics")
        assert response.status_code == 200
        data = response.json()

        # Verify all required metrics fields
        assert "total_decisions_last_24h" in data
        assert "approval_rate" in data
        assert "rejection_rate" in data
        assert "hitl_escalation_rate" in data
        assert "avg_latency_ms" in data
        assert "p95_latency_ms" in data
        assert "p99_latency_ms" in data
        assert "framework_agreement_rate" in data
        assert "total_overrides_last_24h" in data
        assert "override_rate" in data
        assert "override_reasons" in data
        assert "compliance_checks_last_week" in data
        assert "compliance_pass_rate" in data
        assert "risk_distribution" in data

    async def test_get_framework_performance(self, authenticated_client):
        """Test retrieving framework-specific performance metrics."""
        response = await authenticated_client.get("/audit/metrics/frameworks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should have metrics for each framework
        framework_names = [f["framework_name"] for f in data]
        expected_frameworks = ["Kantian", "Consequentialist", "Virtue Ethics", "Principialism"]
        for expected in expected_frameworks:
            assert expected in framework_names


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================


@pytest.mark.asyncio
class TestEdgeCases:
    """Tests for edge cases and error handling."""

    async def test_log_decision_missing_required_fields(self, authenticated_client):
        """Test that logging decision with missing fields returns 422."""
        invalid_payload = {
            "decision_type": DecisionType.OFFENSIVE_ACTION.value,
            # Missing other required fields
        }
        response = await authenticated_client.post("/audit/decision", json=invalid_payload)
        assert response.status_code == 422

    async def test_log_override_invalid_decision_id(self, authenticated_client):
        """Test logging override with invalid UUID format."""
        invalid_payload = {
            "decision_id": "not-a-valid-uuid",
            "operator_id": "test",
            "operator_role": "SOC_ANALYST",
            "original_decision": "REJECTED",
            "override_decision": "APPROVED",
            "justification": "Test justification with minimum 20 characters",
            "override_reason": "FALSE_POSITIVE",
            "urgency_level": "URGENT",
        }
        response = await authenticated_client.post("/audit/override", json=invalid_payload)
        assert response.status_code == 422

    async def test_query_decisions_invalid_confidence_range(self, authenticated_client):
        """Test query with invalid confidence range."""
        query = {
            "min_confidence": 1.5,  # Invalid: > 1.0
            "limit": 100,
        }
        response = await authenticated_client.post("/audit/decisions/query", json=query)
        assert response.status_code == 422

    async def test_query_decisions_invalid_limit(self, authenticated_client):
        """Test query with invalid limit."""
        query = {
            "limit": 5000,  # Invalid: > 1000
        }
        response = await authenticated_client.post("/audit/decisions/query", json=query)
        assert response.status_code == 422
