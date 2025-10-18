"""
Tests for MaximusOrchestratorAgent.

Covers:
- Initialization (with/without dependencies)
- Campaign planning (LLM integration, parsing, validation)
- Campaign execution (phases, actions, HOTL)
- Historical context retrieval
- Error handling and retry logic
- LLM prompt building
"""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from orchestrator import MaximusOrchestratorAgent
from models import (
    CampaignObjective,
    CampaignPlan,
    CampaignStatus,
    RiskLevel,
    HOTLResponse,
    ApprovalStatus,
)
from config import LLMConfig


@pytest.fixture
def mock_llm_config():
    """Create mock LLM config."""
    return LLMConfig(
        api_key="test_key",
        model="gemini-1.5-pro",
        temperature=0.7,
        max_tokens=4096,
        timeout_seconds=60,
    )


@pytest.fixture
def sample_campaign_objective():
    """Create sample campaign objective."""
    return CampaignObjective(
        target="example.com",
        scope=["*.example.com", "10.0.0.0/24"],
        objectives=["Find vulnerabilities", "Test security controls"],
        constraints={"time_window": "09:00-17:00", "no_dos": True},
        priority=8,
    )


@pytest.fixture
def sample_llm_campaign_response():
    """Sample valid LLM response for campaign planning."""
    return json.dumps({
        "phases": [
            {
                "name": "Phase 1: Reconnaissance",
                "actions": [
                    {
                        "action": "DNS enumeration",
                        "ttp": "T1590.002",
                        "agent": "recon_agent",
                        "estimated_duration_min": 15,
                        "requires_hotl": False,
                    },
                    {
                        "action": "Port scanning",
                        "ttp": "T1595.001",
                        "agent": "recon_agent",
                        "estimated_duration_min": 30,
                        "requires_hotl": False,
                    },
                ],
            },
            {
                "name": "Phase 2: Exploitation",
                "actions": [
                    {
                        "action": "Exploit SQL injection",
                        "ttp": "T1190",
                        "agent": "exploit_agent",
                        "estimated_duration_min": 60,
                        "requires_hotl": True,
                    },
                ],
            },
        ],
        "ttps": ["T1590.002", "T1595.001", "T1190"],
        "estimated_duration_minutes": 105,
        "risk_assessment": "high",
        "success_criteria": [
            "Identify all exposed services",
            "Discover exploitable vulnerability",
            "Demonstrate proof of concept",
        ],
        "hotl_checkpoints": ["Before executing exploits"],
    })


@pytest.mark.unit
class TestOrchestratorInit:
    """Test MaximusOrchestratorAgent initialization."""

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_orchestrator_init_with_config(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test creating orchestrator with custom config."""
        mock_model_instance = Mock()
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        assert orchestrator.config == mock_llm_config
        assert orchestrator.llm == mock_model_instance
        mock_configure.assert_called_once_with(api_key="test_key")
        mock_generative_model.assert_called_once_with(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 4096,
            },
        )

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    @patch("orchestrator.get_config")
    def test_orchestrator_init_default_config(
        self,
        mock_get_config,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test creating orchestrator with default config."""
        mock_service_config = Mock()
        mock_service_config.llm = mock_llm_config
        mock_get_config.return_value = mock_service_config

        mock_model_instance = Mock()
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent()

        assert orchestrator.config == mock_llm_config
        mock_configure.assert_called_once_with(api_key="test_key")

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_orchestrator_init_with_dependencies(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test creating orchestrator with HOTL and memory dependencies."""
        mock_hotl = Mock()
        mock_memory = Mock()

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            hotl_system=mock_hotl,
            attack_memory=mock_memory,
        )

        assert orchestrator.hotl_system == mock_hotl
        assert orchestrator.attack_memory == mock_memory


@pytest.mark.unit
class TestPlanCampaign:
    """Test campaign planning functionality."""

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_plan_campaign_success(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
        sample_llm_campaign_response,
    ):
        """Test successful campaign planning."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.text = sample_llm_campaign_response
        mock_model_instance = Mock()
        mock_model_instance.generate_content = Mock(return_value=mock_response)
        mock_generative_model.return_value = mock_model_instance

        # Mock attack memory
        mock_memory = Mock()
        mock_memory.find_similar_campaigns = AsyncMock(return_value=[])
        mock_memory.store_campaign_plan = AsyncMock()

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            attack_memory=mock_memory,
        )

        # Plan campaign
        plan = await orchestrator.plan_campaign(sample_campaign_objective)

        # Verify plan
        assert isinstance(plan, CampaignPlan)
        assert plan.target == "example.com"
        assert len(plan.phases) == 2
        assert len(plan.ttps) == 3
        assert plan.estimated_duration_minutes == 105
        assert plan.risk_assessment == RiskLevel.HIGH
        assert len(plan.success_criteria) == 3
        assert plan.campaign_id is not None

        # Verify memory storage
        mock_memory.store_campaign_plan.assert_called_once_with(plan)

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_plan_campaign_with_custom_id(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
        sample_llm_campaign_response,
    ):
        """Test campaign planning with custom campaign ID."""
        custom_id = uuid4()

        mock_response = Mock()
        mock_response.text = sample_llm_campaign_response
        mock_model_instance = Mock()
        mock_model_instance.generate_content = Mock(return_value=mock_response)
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        plan = await orchestrator.plan_campaign(
            sample_campaign_objective,
            campaign_id=custom_id,
        )

        assert plan.campaign_id == custom_id

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_plan_campaign_without_memory(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
        sample_llm_campaign_response,
    ):
        """Test campaign planning without attack memory."""
        mock_response = Mock()
        mock_response.text = sample_llm_campaign_response
        mock_model_instance = Mock()
        mock_model_instance.generate_content = Mock(return_value=mock_response)
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            attack_memory=None,
        )

        plan = await orchestrator.plan_campaign(sample_campaign_objective)

        assert isinstance(plan, CampaignPlan)
        # Should succeed without memory

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_plan_campaign_llm_failure(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
    ):
        """Test campaign planning when LLM call fails."""
        # Mock LLM to raise exception
        mock_model_instance = Mock()
        mock_model_instance.generate_content = Mock(
            side_effect=RuntimeError("API error")
        )
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(RuntimeError) as exc_info:
            await orchestrator.plan_campaign(sample_campaign_objective)

        assert "Failed to plan campaign" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_plan_campaign_invalid_json(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
    ):
        """Test campaign planning with invalid JSON response."""
        mock_response = Mock()
        mock_response.text = "This is not JSON"
        mock_model_instance = Mock()
        mock_model_instance.generate_content = Mock(return_value=mock_response)
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        # Invalid JSON is a validation error, should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.plan_campaign(sample_campaign_objective)

        assert "Failed to parse campaign plan" in str(exc_info.value)


@pytest.mark.unit
class TestExecuteCampaign:
    """Test campaign execution functionality."""

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_execute_campaign_success(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test successful campaign execution."""
        campaign_id = uuid4()
        plan = CampaignPlan(
            campaign_id=campaign_id,
            target="test.com",
            phases=[
                {
                    "name": "Phase 1: Recon",
                    "actions": [
                        {
                            "action": "DNS enum",
                            "agent": "recon_agent",
                            "requires_hotl": False,
                        },
                    ],
                },
            ],
            ttps=["T1590.002"],
            estimated_duration_minutes=30,
            risk_assessment=RiskLevel.LOW,
            success_criteria=["Complete recon"],
            created_at=datetime.utcnow(),
        )

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        results = await orchestrator.execute_campaign(plan)

        assert results["campaign_id"] == str(campaign_id)
        assert results["target"] == "test.com"
        assert results["status"] == CampaignStatus.COMPLETED
        assert len(results["phases"]) == 1
        assert "start_time" in results
        assert "end_time" in results

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_execute_campaign_with_hotl(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test campaign execution with HOTL approval."""
        campaign_id = uuid4()
        plan = CampaignPlan(
            campaign_id=campaign_id,
            target="test.com",
            phases=[
                {
                    "name": "Phase 1: Exploit",
                    "actions": [
                        {
                            "action": "Exploit SQLi",
                            "agent": "exploit_agent",
                            "ttp": "T1190",
                            "requires_hotl": True,
                        },
                    ],
                },
            ],
            ttps=["T1190"],
            estimated_duration_minutes=60,
            risk_assessment=RiskLevel.HIGH,
            success_criteria=["Exploit success"],
            created_at=datetime.utcnow(),
        )

        # Mock HOTL system to approve
        mock_hotl = Mock()
        mock_approval = HOTLResponse(
            request_id=uuid4(),
            approved=True,
            status=ApprovalStatus.APPROVED,
            reasoning="Approved for testing",
            operator="admin",
            timestamp=datetime.utcnow(),
        )
        mock_hotl.request_approval = AsyncMock(return_value=mock_approval)

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            hotl_system=mock_hotl,
        )

        results = await orchestrator.execute_campaign(plan)

        assert results["status"] == CampaignStatus.COMPLETED
        mock_hotl.request_approval.assert_called_once()

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_execute_campaign_hotl_rejection(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test campaign execution when HOTL rejects action."""
        campaign_id = uuid4()
        plan = CampaignPlan(
            campaign_id=campaign_id,
            target="test.com",
            phases=[
                {
                    "name": "Phase 1: Exploit",
                    "actions": [
                        {
                            "action": "Exploit SQLi",
                            "agent": "exploit_agent",
                            "ttp": "T1190",
                            "requires_hotl": True,
                        },
                    ],
                },
            ],
            ttps=["T1190"],
            estimated_duration_minutes=60,
            risk_assessment=RiskLevel.HIGH,
            success_criteria=["Exploit success"],
            created_at=datetime.utcnow(),
        )

        # Mock HOTL system to reject
        mock_hotl = Mock()
        mock_rejection = HOTLResponse(
            request_id=uuid4(),
            approved=False,
            status=ApprovalStatus.REJECTED,
            reasoning="Too risky",
            operator="admin",
            timestamp=datetime.utcnow(),
        )
        mock_hotl.request_approval = AsyncMock(return_value=mock_rejection)

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            hotl_system=mock_hotl,
        )

        results = await orchestrator.execute_campaign(plan)

        # Check action was rejected
        phase_result = results["phases"][0]
        action_result = phase_result["actions"][0]
        assert action_result["status"] == "rejected"
        assert "HOTL approval denied" in action_result["reason"]

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_execute_campaign_phase_failure(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test campaign execution with phase marked as critical failure."""
        campaign_id = uuid4()
        plan = CampaignPlan(
            campaign_id=campaign_id,
            target="test.com",
            phases=[
                {
                    "name": "Phase 1: Recon",
                    "actions": [
                        {
                            "action": "DNS enum",
                            "agent": "recon_agent",
                            "requires_hotl": False,
                        },
                    ],
                },
                {
                    "name": "Phase 2: Should not execute",
                    "actions": [
                        {
                            "action": "Another action",
                            "agent": "recon_agent",
                            "requires_hotl": False,
                        },
                    ],
                },
            ],
            ttps=["T1590.002"],
            estimated_duration_minutes=60,
            risk_assessment=RiskLevel.MEDIUM,
            success_criteria=["Complete all phases"],
            created_at=datetime.utcnow(),
        )

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        # Patch _execute_phase to return critical failure for first phase
        async def mock_execute_phase(campaign_id, phase):
            if "Phase 1" in phase["name"]:
                return {
                    "name": phase["name"],
                    "actions": [],
                    "critical_failure": True,
                    "start_time": datetime.utcnow().isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                }
            return {
                "name": phase["name"],
                "actions": [],
                "start_time": datetime.utcnow().isoformat(),
                "end_time": datetime.utcnow().isoformat(),
            }

        orchestrator._execute_phase = mock_execute_phase

        results = await orchestrator.execute_campaign(plan)

        # Should stop after first phase
        assert results["status"] == CampaignStatus.FAILED
        assert len(results["phases"]) == 1

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_execute_campaign_exception_handling(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test campaign execution exception handling."""
        campaign_id = uuid4()
        plan = CampaignPlan(
            campaign_id=campaign_id,
            target="test.com",
            phases=[
                {
                    "name": "Phase 1: Recon",
                    "actions": [{"action": "DNS enum"}],
                },
            ],
            ttps=["T1590.002"],
            estimated_duration_minutes=30,
            risk_assessment=RiskLevel.LOW,
            success_criteria=["Complete"],
            created_at=datetime.utcnow(),
        )

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        # Patch _execute_phase to raise exception
        async def mock_execute_phase_error(campaign_id, phase):
            raise RuntimeError("Phase execution failed")

        orchestrator._execute_phase = mock_execute_phase_error

        results = await orchestrator.execute_campaign(plan)

        assert results["status"] == CampaignStatus.FAILED
        assert "error" in results
        assert "Phase execution failed" in results["error"]

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_execute_action_critical_failure(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test action with critical_failure flag propagates to phase."""
        campaign_id = uuid4()
        plan = CampaignPlan(
            campaign_id=campaign_id,
            target="test.com",
            phases=[
                {
                    "name": "Phase 1: Recon",
                    "actions": [
                        {"action": "Action 1", "agent": "recon_agent"},
                        {"action": "Action 2", "agent": "recon_agent"},
                    ],
                },
            ],
            ttps=["T1590.002"],
            estimated_duration_minutes=30,
            risk_assessment=RiskLevel.LOW,
            success_criteria=["Complete"],
            created_at=datetime.utcnow(),
        )

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        # Patch _execute_action to return critical_failure for first action
        original_execute_action = orchestrator._execute_action
        call_count = [0]

        async def mock_execute_action_with_failure(campaign_id, action):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "action": action["action"],
                    "status": "failed",
                    "critical_failure": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            return await original_execute_action(campaign_id, action)

        orchestrator._execute_action = mock_execute_action_with_failure

        results = await orchestrator.execute_campaign(plan)

        # Should stop after first action
        phase_result = results["phases"][0]
        assert phase_result.get("critical_failure") is True
        assert len(phase_result["actions"]) == 1  # Only first action executed


@pytest.mark.unit
class TestCheckHOTL:
    """Test HOTL checkpoint functionality."""

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_check_hotl_approval(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test HOTL approval check returns True."""
        mock_hotl = Mock()
        mock_approval = HOTLResponse(
            request_id=uuid4(),
            approved=True,
            status=ApprovalStatus.APPROVED,
            reasoning="Approved",
            operator="admin",
            timestamp=datetime.utcnow(),
        )
        mock_hotl.request_approval = AsyncMock(return_value=mock_approval)

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            hotl_system=mock_hotl,
        )

        action = {
            "action": "Exploit SQLi",
            "agent": "exploitation",
            "ttp": "T1190",
        }

        approved = await orchestrator._check_hotl(uuid4(), action)

        assert approved is True

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_check_hotl_rejection(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test HOTL rejection check returns False."""
        mock_hotl = Mock()
        mock_rejection = HOTLResponse(
            request_id=uuid4(),
            approved=False,
            status=ApprovalStatus.REJECTED,
            reasoning="Too risky",
            operator="admin",
            timestamp=datetime.utcnow(),
        )
        mock_hotl.request_approval = AsyncMock(return_value=mock_rejection)

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            hotl_system=mock_hotl,
        )

        action = {
            "action": "Exploit SQLi",
            "agent": "exploitation",
            "ttp": "T1190",
        }

        approved = await orchestrator._check_hotl(uuid4(), action)

        assert approved is False

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_check_hotl_no_system_auto_approve(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test HOTL check auto-approves when no HOTL system configured."""
        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            hotl_system=None,
        )

        action = {
            "action": "Exploit SQLi",
            "agent": "exploitation",
            "ttp": "T1190",
        }

        approved = await orchestrator._check_hotl(uuid4(), action)

        assert approved is True


@pytest.mark.unit
class TestGetHistoricalContext:
    """Test historical context retrieval."""

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_get_historical_context_with_campaigns(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
    ):
        """Test retrieving historical context with similar campaigns."""
        mock_memory = Mock()
        mock_memory.find_similar_campaigns = AsyncMock(
            return_value=[
                {
                    "target": "example.com",
                    "success": True,
                    "lessons_learned": "Use stealthy scans",
                },
                {
                    "target": "test.com",
                    "success": False,
                    "lessons_learned": "Avoid IDS triggers",
                },
            ]
        )

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            attack_memory=mock_memory,
        )

        context = await orchestrator._get_historical_context(sample_campaign_objective)

        assert "Campaign 1: Target=example.com" in context
        assert "Success=True" in context
        assert "Use stealthy scans" in context
        assert "Campaign 2: Target=test.com" in context

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_get_historical_context_no_campaigns(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
    ):
        """Test retrieving historical context with no similar campaigns."""
        mock_memory = Mock()
        mock_memory.find_similar_campaigns = AsyncMock(return_value=[])

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            attack_memory=mock_memory,
        )

        context = await orchestrator._get_historical_context(sample_campaign_objective)

        assert context == "No similar campaigns found in history."

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_get_historical_context_no_memory(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
    ):
        """Test historical context without attack memory."""
        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            attack_memory=None,
        )

        context = await orchestrator._get_historical_context(sample_campaign_objective)

        assert context == "No historical campaigns available (first run)."

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_get_historical_context_error(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
    ):
        """Test historical context retrieval error handling."""
        mock_memory = Mock()
        mock_memory.find_similar_campaigns = AsyncMock(
            side_effect=RuntimeError("Database error")
        )

        orchestrator = MaximusOrchestratorAgent(
            config=mock_llm_config,
            attack_memory=mock_memory,
        )

        context = await orchestrator._get_historical_context(sample_campaign_objective)

        assert context == "Historical context unavailable due to error."


@pytest.mark.unit
class TestBuildPlanningPrompt:
    """Test LLM prompt building."""

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_build_planning_prompt(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_campaign_objective,
    ):
        """Test building complete planning prompt."""
        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        historical_context = "Past campaign: example.com, success=True"

        prompt = orchestrator._build_planning_prompt(
            sample_campaign_objective,
            historical_context,
        )

        # Check all components are in prompt
        assert "example.com" in prompt
        assert "*.example.com" in prompt
        assert "Find vulnerabilities" in prompt
        assert "Past campaign: example.com" in prompt
        assert "MAXIMUS" in prompt
        assert "MITRE ATT&CK" in prompt


@pytest.mark.unit
class TestCallLLM:
    """Test LLM calling with retry logic."""

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_call_llm_success(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test successful LLM call."""
        mock_response = Mock()
        mock_response.text = "LLM response"
        mock_model_instance = Mock()
        mock_model_instance.generate_content = Mock(return_value=mock_response)
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        result = await orchestrator._call_llm("Test prompt")

        assert result == "LLM response"
        mock_model_instance.generate_content.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_call_llm_retry_then_success(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test LLM call with retry logic (fail then succeed)."""
        mock_response = Mock()
        mock_response.text = "LLM response"
        mock_model_instance = Mock()
        # First call fails, second succeeds
        mock_model_instance.generate_content = Mock(
            side_effect=[
                RuntimeError("Temporary error"),
                mock_response,
            ]
        )
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        result = await orchestrator._call_llm("Test prompt")

        assert result == "LLM response"
        assert mock_model_instance.generate_content.call_count == 2

    @pytest.mark.asyncio
    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    async def test_call_llm_max_retries_exceeded(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test LLM call fails after max retries."""
        mock_model_instance = Mock()
        # All calls fail
        mock_model_instance.generate_content = Mock(
            side_effect=RuntimeError("Persistent error")
        )
        mock_generative_model.return_value = mock_model_instance

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(RuntimeError) as exc_info:
            await orchestrator._call_llm("Test prompt")

        assert "LLM call failed after 3 attempts" in str(exc_info.value)
        assert mock_model_instance.generate_content.call_count == 3


@pytest.mark.unit
class TestParseCampaignPlan:
    """Test campaign plan parsing and validation."""

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_valid_json(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_llm_campaign_response,
    ):
        """Test parsing valid campaign plan JSON."""
        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        parsed = orchestrator._parse_campaign_plan(sample_llm_campaign_response)

        assert "phases" in parsed
        assert "ttps" in parsed
        assert "estimated_duration_minutes" in parsed
        assert "risk_assessment" in parsed
        assert "success_criteria" in parsed
        assert len(parsed["phases"]) == 2
        assert parsed["estimated_duration_minutes"] == 105

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_with_extra_text(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
        sample_llm_campaign_response,
    ):
        """Test parsing campaign plan with extra text around JSON."""
        raw_response = f"Here is the plan:\n\n{sample_llm_campaign_response}\n\nEnd of plan."

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        parsed = orchestrator._parse_campaign_plan(raw_response)

        assert "phases" in parsed
        assert len(parsed["phases"]) == 2

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_no_json(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test parsing fails when no JSON in response."""
        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(ValueError) as exc_info:
            orchestrator._parse_campaign_plan("This is plain text without JSON")

        assert "No JSON found in LLM response" in str(exc_info.value)

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_missing_fields(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test parsing fails when required fields missing."""
        incomplete_plan = json.dumps({
            "phases": [{"name": "Phase 1", "actions": []}],
            "ttps": [],
            # Missing: estimated_duration_minutes, risk_assessment, success_criteria
        })

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(ValueError) as exc_info:
            orchestrator._parse_campaign_plan(incomplete_plan)

        assert "Missing required fields" in str(exc_info.value)

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_invalid_types(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test parsing fails with invalid data types."""
        invalid_plan = json.dumps({
            "phases": "not a list",  # Should be list
            "ttps": [],
            "estimated_duration_minutes": 120,
            "risk_assessment": "high",
            "success_criteria": [],
        })

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(ValueError) as exc_info:
            orchestrator._parse_campaign_plan(invalid_plan)

        assert "phases must be non-empty list" in str(exc_info.value)

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_empty_phases(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test parsing fails with empty phases list."""
        invalid_plan = json.dumps({
            "phases": [],  # Empty list
            "ttps": [],
            "estimated_duration_minutes": 120,
            "risk_assessment": "high",
            "success_criteria": [],
        })

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(ValueError) as exc_info:
            orchestrator._parse_campaign_plan(invalid_plan)

        assert "phases must be non-empty list" in str(exc_info.value)

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_invalid_json_syntax(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test parsing fails with malformed JSON."""
        invalid_json = '{"phases": [{"name": "Phase 1"}, ttps: []}'  # Invalid syntax

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(ValueError) as exc_info:
            orchestrator._parse_campaign_plan(invalid_json)

        assert "Invalid JSON in LLM response" in str(exc_info.value)

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_wrong_ttps_type(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test parsing fails when ttps is not a list."""
        invalid_plan = json.dumps({
            "phases": [{"name": "Phase 1", "actions": []}],
            "ttps": "T1590.002",  # Should be list
            "estimated_duration_minutes": 120,
            "risk_assessment": "high",
            "success_criteria": [],
        })

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(ValueError) as exc_info:
            orchestrator._parse_campaign_plan(invalid_plan)

        assert "ttps must be list" in str(exc_info.value)

    @patch("orchestrator.genai.configure")
    @patch("orchestrator.genai.GenerativeModel")
    def test_parse_campaign_plan_wrong_duration_type(
        self,
        mock_generative_model,
        mock_configure,
        mock_llm_config,
    ):
        """Test parsing fails when duration is not an integer."""
        invalid_plan = json.dumps({
            "phases": [{"name": "Phase 1", "actions": []}],
            "ttps": [],
            "estimated_duration_minutes": "120 minutes",  # Should be int
            "risk_assessment": "high",
            "success_criteria": [],
        })

        orchestrator = MaximusOrchestratorAgent(config=mock_llm_config)

        with pytest.raises(ValueError) as exc_info:
            orchestrator._parse_campaign_plan(invalid_plan)

        assert "estimated_duration_minutes must be integer" in str(exc_info.value)
