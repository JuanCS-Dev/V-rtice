"""
Tests for data models (Pydantic and SQLAlchemy).

Covers:
- Pydantic model validation
- SQLAlchemy model creation
- Enum values
- Field constraints
- Serialization/deserialization
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import ValidationError

from models import (
    # Enums
    CampaignStatus,
    ActionType,
    RiskLevel,
    ApprovalStatus,
    # Pydantic models
    CampaignObjective,
    CampaignPlan,
    HOTLRequest,
    HOTLResponse,
    HealthResponse,
    # SQLAlchemy models
    CampaignDB,
    HOTLDecisionDB,
    AttackMemoryDB,
)


# ============================================================================
# Enum Tests
# ============================================================================

@pytest.mark.unit
class TestEnums:
    """Test enum definitions."""

    def test_campaign_status_values(self):
        """Test CampaignStatus enum has expected values."""
        assert CampaignStatus.PLANNED == "planned"
        assert CampaignStatus.APPROVED == "approved"
        assert CampaignStatus.IN_PROGRESS == "in_progress"
        assert CampaignStatus.COMPLETED == "completed"
        assert CampaignStatus.FAILED == "failed"
        assert CampaignStatus.ABORTED == "aborted"

    def test_action_type_values(self):
        """Test ActionType enum has expected values."""
        assert ActionType.RECONNAISSANCE == "reconnaissance"
        assert ActionType.ANALYSIS == "analysis"
        assert ActionType.EXPLOITATION == "exploitation"
        assert ActionType.POST_EXPLOITATION == "post_exploitation"

    def test_risk_level_values(self):
        """Test RiskLevel enum has expected values."""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"

    def test_approval_status_values(self):
        """Test ApprovalStatus enum has expected values."""
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.REJECTED == "rejected"
        assert ApprovalStatus.TIMEOUT == "timeout"


# ============================================================================
# Pydantic Model Tests
# ============================================================================

@pytest.mark.unit
class TestCampaignObjective:
    """Test CampaignObjective Pydantic model."""

    def test_create_valid_objective(self):
        """Test creating valid campaign objective."""
        objective = CampaignObjective(
            target="example.com",
            scope=["web", "api"],
            objectives=["identify_vulns"],
            constraints={"time_limit": "4h"},
            priority=5,
            created_by="operator1",
        )

        assert objective.target == "example.com"
        assert objective.scope == ["web", "api"]
        assert objective.objectives == ["identify_vulns"]
        assert objective.constraints == {"time_limit": "4h"}
        assert objective.priority == 5
        assert objective.created_by == "operator1"

    def test_objective_with_defaults(self):
        """Test objective creation with default values."""
        objective = CampaignObjective(
            target="example.com",
            scope=["web"],
            objectives=["test"],
        )

        assert objective.priority == 5  # Default
        assert objective.created_by is None  # Optional

    def test_objective_validation_empty_target(self):
        """Test validation fails for empty target."""
        with pytest.raises(ValidationError):
            CampaignObjective(
                target="",
                scope=["web"],
                objectives=["test"],
            )

    def test_objective_serialization(self):
        """Test objective serialization to dict."""
        objective = CampaignObjective(
            target="example.com",
            scope=["web"],
            objectives=["test"],
            constraints={},
            priority=7,
        )

        data = objective.model_dump()
        assert data["target"] == "example.com"
        assert data["priority"] == 7
        assert isinstance(data, dict)


# NOTE: CampaignAction and CampaignPhase are represented as Dict[str, Any]
# in the current implementation, not as separate Pydantic models.
# They are embedded within CampaignPlan.phases as dictionaries.


@pytest.mark.unit
class TestCampaignPlan:
    """Test CampaignPlan Pydantic model."""

    def test_create_valid_campaign_plan(self, sample_campaign_phase):
        """Test creating valid campaign plan."""
        campaign_id = uuid4()

        plan = CampaignPlan(
            campaign_id=campaign_id,
            target="example.com",
            phases=[sample_campaign_phase],
            ttps=["T1046", "T1590"],
            estimated_duration_minutes=240,
            risk_assessment=RiskLevel.MEDIUM,
            success_criteria=["Identify vulnerabilities"],
            created_at=datetime.utcnow(),
        )

        assert plan.campaign_id == campaign_id
        assert plan.target == "example.com"
        assert len(plan.phases) == 1
        assert plan.risk_assessment == RiskLevel.MEDIUM
        assert plan.estimated_duration_minutes == 240

    def test_campaign_plan_with_multiple_phases(self):
        """Test campaign plan with multiple phases."""
        phases = [
            {"name": "Phase 1: Recon", "actions": [{"action": "Port scan", "ttp": "T1046", "agent": "recon_agent", "estimated_duration_min": 30, "requires_hotl": False}]},
            {"name": "Phase 2: Exploit", "actions": [{"action": "SQL injection", "ttp": "T1190", "agent": "exploit_agent", "estimated_duration_min": 60, "requires_hotl": True}]},
        ]

        plan = CampaignPlan(
            campaign_id=uuid4(),
            target="example.com",
            phases=phases,
            ttps=["T1046", "T1190"],
            estimated_duration_minutes=90,
            risk_assessment=RiskLevel.HIGH,
            success_criteria=["Gain access", "Extract data"],
            created_at=datetime.utcnow(),
        )

        assert len(plan.phases) == 2
        assert plan.phases[0]["name"] == "Phase 1: Recon"
        assert plan.phases[1]["name"] == "Phase 2: Exploit"

    def test_campaign_plan_serialization(self, sample_campaign_plan):
        """Test campaign plan serialization."""
        data = sample_campaign_plan.model_dump()

        assert isinstance(data, dict)
        assert "campaign_id" in data
        assert "target" in data
        assert "phases" in data
        assert "ttps" in data
        assert "risk_assessment" in data
        assert isinstance(data["phases"], list)


@pytest.mark.unit
class TestHOTLRequest:
    """Test HOTLRequest Pydantic model."""

    def test_create_valid_hotl_request(self):
        """Test creating valid HOTL request."""
        request_id = uuid4()
        campaign_id = uuid4()

        request = HOTLRequest(
            request_id=request_id,
            campaign_id=campaign_id,
            action_type=ActionType.EXPLOITATION,
            description="Exploit SQL injection",
            risk_level=RiskLevel.HIGH,
            context={"vuln_type": "SQLi"},
        )

        assert request.request_id == request_id
        assert request.campaign_id == campaign_id
        assert request.action_type == ActionType.EXPLOITATION
        assert request.risk_level == RiskLevel.HIGH
        assert isinstance(request.timestamp, datetime)

    def test_hotl_request_auto_timestamp(self):
        """Test HOTL request auto-generates timestamp."""
        request = HOTLRequest(
            campaign_id=uuid4(),
            action_type=ActionType.EXPLOITATION,
            description="Test action",
            risk_level=RiskLevel.MEDIUM,
            context={},
        )

        assert request.timestamp is not None
        assert isinstance(request.timestamp, datetime)


@pytest.mark.unit
class TestHOTLResponse:
    """Test HOTLResponse Pydantic model."""

    def test_create_hotl_response_approved(self):
        """Test creating approved HOTL response."""
        request_id = uuid4()

        response = HOTLResponse(
            request_id=request_id,
            status=ApprovalStatus.APPROVED,
            approved=True,
            operator="operator1",
            reasoning="Safe to proceed",
        )

        assert response.request_id == request_id
        assert response.status == ApprovalStatus.APPROVED
        assert response.approved is True
        assert response.operator == "operator1"
        assert isinstance(response.timestamp, datetime)

    def test_create_hotl_response_rejected(self):
        """Test creating rejected HOTL response."""
        response = HOTLResponse(
            request_id=uuid4(),
            status=ApprovalStatus.REJECTED,
            approved=False,
            operator="operator2",
            reasoning="Too risky",
        )

        assert response.status == ApprovalStatus.REJECTED
        assert response.approved is False
        assert response.reasoning == "Too risky"


@pytest.mark.unit
class TestHealthResponse:
    """Test HealthResponse Pydantic model."""

    def test_create_health_response(self):
        """Test creating health response."""
        health = HealthResponse(
            status="healthy",
            service="test_service",
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        assert health.status == "healthy"
        assert health.service == "test_service"
        assert health.version == "1.0.0"


# ============================================================================
# SQLAlchemy Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.db
class TestCampaignDB:
    """Test CampaignDB SQLAlchemy model."""

    def test_create_campaign_db(self, test_db_session):
        """Test creating campaign in database."""
        campaign = CampaignDB(
            target="example.com",
            scope=["web"],
            objectives=["test"],
            constraints={"time": "4h"},
            priority=7,
            status=CampaignStatus.PLANNED,
            created_by="operator1",
        )

        test_db_session.add(campaign)
        test_db_session.commit()
        test_db_session.refresh(campaign)

        assert campaign.id is not None
        assert isinstance(campaign.id, UUID)
        assert campaign.target == "example.com"
        assert campaign.status == CampaignStatus.PLANNED
        assert campaign.created_at is not None

    def test_campaign_db_timestamps(self, test_db_session):
        """Test campaign timestamps are set automatically."""
        campaign = CampaignDB(
            target="test.com",
            scope=["test"],
            objectives=["test"],
            constraints={},
            priority=5,
            status=CampaignStatus.PLANNED,
        )

        test_db_session.add(campaign)
        test_db_session.commit()
        test_db_session.refresh(campaign)

        assert campaign.created_at is not None
        assert campaign.updated_at is not None
        assert campaign.completed_at is None


@pytest.mark.unit
@pytest.mark.db
class TestHOTLDecisionDB:
    """Test HOTLDecisionDB SQLAlchemy model."""

    def test_create_hotl_decision_db(self, test_db_session):
        """Test creating HOTL decision in database."""
        campaign = CampaignDB(
            target="example.com",
            scope=["web"],
            objectives=["test"],
            constraints={},
            priority=5,
            status=CampaignStatus.PLANNED,
        )
        test_db_session.add(campaign)
        test_db_session.commit()

        decision = HOTLDecisionDB(
            campaign_id=campaign.id,
            action_type="exploitation",
            description="Exploit SQLi",
            risk_level="high",
            context={"vuln": "SQLi"},
        )

        test_db_session.add(decision)
        test_db_session.commit()
        test_db_session.refresh(decision)

        assert decision.id is not None
        assert decision.campaign_id == campaign.id
        assert decision.status == "pending"
        assert decision.approved is None


@pytest.mark.unit
@pytest.mark.db
class TestAttackMemoryDB:
    """Test AttackMemoryDB SQLAlchemy model."""

    def test_create_attack_memory_db(self, test_db_session):
        """Test creating attack memory in database."""
        campaign = CampaignDB(
            target="example.com",
            scope=["web"],
            objectives=["test"],
            constraints={},
            priority=5,
            status=CampaignStatus.PLANNED,
        )
        test_db_session.add(campaign)
        test_db_session.commit()

        memory = AttackMemoryDB(
            campaign_id=campaign.id,
            action_type="reconnaissance",
            target="example.com",
            technique="nmap",
            success=True,
            result={"ports": [80, 443]},
            lessons_learned="Target has standard web ports open",
        )

        test_db_session.add(memory)
        test_db_session.commit()
        test_db_session.refresh(memory)

        assert memory.id is not None
        assert memory.campaign_id == campaign.id
        assert memory.success is True
        assert memory.result == {"ports": [80, 443]}
