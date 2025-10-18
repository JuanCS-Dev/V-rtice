"""Complete tests for orchestrator core - 100% coverage."""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from orchestrator.core import (
    MaximusOrchestratorAgent,
    Campaign,
    CampaignStatus,
    AgentType
)


@pytest.fixture
def orchestrator() -> MaximusOrchestratorAgent:
    """Create orchestrator instance."""
    return MaximusOrchestratorAgent(api_key="test_key_12345")


@pytest.fixture
def mock_anthropic_response() -> Mock:
    """Mock Anthropic API response."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = json.dumps({
        "campaign_id": "test_camp_001",
        "phases": [
            {
                "name": "reconnaissance",
                "objectives": ["Network mapping"],
                "estimated_duration": "2h"
            }
        ],
        "agent_commands": [
            {
                "agent_type": "recon",
                "action": "scan_network",
                "parameters": {"target": "test"},
                "requires_approval": False
            }
        ],
        "risk_assessment": {
            "level": "medium",
            "factors": ["Unknown scope"]
        },
        "hotl_checkpoints": ["Before exploitation"]
    })
    mock_response.content = [mock_content]
    return mock_response


@pytest.mark.asyncio
async def test_plan_campaign_llm_success(orchestrator: MaximusOrchestratorAgent, mock_anthropic_response: Mock) -> None:
    """Test campaign planning with successful LLM response."""
    with patch.object(orchestrator.client.messages, 'create', return_value=mock_anthropic_response):
        campaign = await orchestrator.plan_campaign(
            objective="Test web application security",
            scope=["192.168.1.0/24"],
            constraints={"no_dos": True}
        )
        
        assert campaign.objective == "Test web application security"
        assert campaign.status == CampaignStatus.PLANNED
        assert len(campaign.phases) > 0
        assert campaign.risk_assessment is not None
        assert len(campaign.hotl_checkpoints) > 0


@pytest.mark.asyncio
async def test_plan_campaign_llm_invalid_json(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test campaign planning with invalid JSON response."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "This is not JSON at all"
    mock_response.content = [mock_content]
    
    with patch.object(orchestrator.client.messages, 'create', return_value=mock_response):
        campaign = await orchestrator.plan_campaign(
            objective="Test",
            scope=["target.com"],
            constraints={}
        )
        
        # Should fallback to basic plan
        assert campaign.status == CampaignStatus.PLANNED
        assert len(campaign.phases) > 0


@pytest.mark.asyncio
async def test_plan_campaign_llm_exception(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test campaign planning with LLM exception."""
    with patch.object(orchestrator.client.messages, 'create', side_effect=Exception("API Error")):
        campaign = await orchestrator.plan_campaign(
            objective="Test",
            scope=["target.com"],
            constraints={}
        )
        
        # Should fallback to basic plan
        assert campaign.status == CampaignStatus.PLANNED
        assert len(campaign.phases) > 0
        assert campaign.id.startswith("camp_")


@pytest.mark.asyncio
async def test_plan_campaign_no_json_markers(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test campaign planning with response without JSON markers."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "Some text without curly braces"
    mock_response.content = [mock_content]
    
    with patch.object(orchestrator.client.messages, 'create', return_value=mock_response):
        campaign = await orchestrator.plan_campaign(
            objective="Test",
            scope=["target.com"],
            constraints={}
        )
        
        # Should use fallback
        assert campaign.status == CampaignStatus.PLANNED


@pytest.mark.asyncio
async def test_coordinate_agents_recon_only(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test agent coordination with reconnaissance only."""
    campaign = Campaign(
        id="test_001",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now(),
        phases=[
            {"name": "reconnaissance", "objectives": ["Scan"]}
        ]
    )
    
    commands = await orchestrator.coordinate_agents(campaign)
    
    assert len(commands) >= 1
    assert commands[0].agent_type == AgentType.RECON
    assert commands[0].priority == 10


@pytest.mark.asyncio
async def test_coordinate_agents_exploit_phase(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test agent coordination with exploitation phase."""
    campaign = Campaign(
        id="test_002",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now(),
        phases=[
            {"name": "exploitation", "objectives": ["Exploit"]}
        ]
    )
    
    commands = await orchestrator.coordinate_agents(campaign)
    
    exploit_commands = [c for c in commands if c.agent_type == AgentType.EXPLOIT]
    assert len(exploit_commands) > 0
    assert exploit_commands[0].requires_approval is True


@pytest.mark.asyncio
async def test_coordinate_agents_postexploit_phase(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test agent coordination with post-exploitation phase."""
    campaign = Campaign(
        id="test_003",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now(),
        phases=[
            {"name": "post-exploitation", "objectives": ["Assess"]}
        ]
    )
    
    commands = await orchestrator.coordinate_agents(campaign)
    
    postexploit_commands = [c for c in commands if c.agent_type == AgentType.POSTEXPLOIT]
    assert len(postexploit_commands) > 0
    assert postexploit_commands[0].requires_approval is True


@pytest.mark.asyncio
async def test_coordinate_agents_lateral_phase(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test agent coordination with lateral movement phase."""
    campaign = Campaign(
        id="test_004",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now(),
        phases=[
            {"name": "lateral movement", "objectives": ["Move"]}
        ]
    )
    
    commands = await orchestrator.coordinate_agents(campaign)
    
    postexploit_commands = [c for c in commands if c.agent_type == AgentType.POSTEXPLOIT]
    assert len(postexploit_commands) > 0


@pytest.mark.asyncio
async def test_coordinate_agents_priority_sorting(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test commands are sorted by priority."""
    campaign = Campaign(
        id="test_005",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now(),
        phases=[
            {"name": "reconnaissance"},
            {"name": "exploitation"},
            {"name": "post-exploitation"}
        ]
    )
    
    commands = await orchestrator.coordinate_agents(campaign)
    
    # Commands should be sorted by priority (descending)
    priorities = [c.priority for c in commands]
    assert priorities == sorted(priorities, reverse=True)


@pytest.mark.asyncio
async def test_analyze_results_success(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test results analysis with successful LLM response."""
    campaign = Campaign(
        id="test_006",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.COMPLETED,
        created_at=datetime.now()
    )
    
    results = {
        "findings": [{"type": "vuln", "severity": "high"}]
    }
    
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = json.dumps({
        "success_metrics": {"findings": 1},
        "key_findings": ["High severity vulnerability"],
        "recommendations": ["Patch immediately"]
    })
    mock_response.content = [mock_content]
    
    with patch.object(orchestrator.client.messages, 'create', return_value=mock_response):
        analysis = await orchestrator.analyze_results(campaign, results)
        
        assert "success_metrics" in analysis
        assert "key_findings" in analysis


@pytest.mark.asyncio
async def test_analyze_results_no_json(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test results analysis with non-JSON response."""
    campaign = Campaign(
        id="test_007",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.COMPLETED,
        created_at=datetime.now()
    )
    
    results = {"test": "data"}
    
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "Plain text analysis without JSON"
    mock_response.content = [mock_content]
    
    with patch.object(orchestrator.client.messages, 'create', return_value=mock_response):
        analysis = await orchestrator.analyze_results(campaign, results)
        
        assert "raw_analysis" in analysis


@pytest.mark.asyncio
async def test_analyze_results_exception(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test results analysis with LLM exception."""
    campaign = Campaign(
        id="test_008",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.COMPLETED,
        created_at=datetime.now()
    )
    
    results = {"test": "data"}
    
    with patch.object(orchestrator.client.messages, 'create', side_effect=Exception("API Error")):
        analysis = await orchestrator.analyze_results(campaign, results)
        
        assert "error" in analysis
        assert "results" in analysis


@pytest.mark.asyncio
async def test_plan_campaign_content_block_without_text(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test plan campaign with content block without text attribute."""
    mock_response = Mock()
    mock_content = Mock(spec=[])  # No text attribute
    mock_response.content = [mock_content]
    
    with patch.object(orchestrator.client.messages, 'create', return_value=mock_response):
        campaign = await orchestrator.plan_campaign(
            objective="Test",
            scope=["target.com"],
            constraints={}
        )
        
        assert campaign.status == CampaignStatus.PLANNED


@pytest.mark.asyncio
async def test_analyze_results_content_block_without_text(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test analyze results with content block without text attribute."""
    campaign = Campaign(
        id="test_009",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.COMPLETED,
        created_at=datetime.now()
    )
    
    mock_response = Mock()
    mock_content = Mock(spec=[])  # No text attribute
    mock_response.content = [mock_content]
    
    with patch.object(orchestrator.client.messages, 'create', return_value=mock_response):
        analysis = await orchestrator.analyze_results(campaign, {})
        
        assert isinstance(analysis, dict)


def test_orchestrator_initialization() -> None:
    """Test orchestrator initialization."""
    orchestrator = MaximusOrchestratorAgent(api_key="test_key", model="custom-model")
    
    assert orchestrator.model == "custom-model"
    assert orchestrator.client is not None


def test_orchestrator_default_model() -> None:
    """Test orchestrator with default model."""
    orchestrator = MaximusOrchestratorAgent(api_key="test_key")
    
    assert orchestrator.model == "claude-sonnet-4-20250514"
