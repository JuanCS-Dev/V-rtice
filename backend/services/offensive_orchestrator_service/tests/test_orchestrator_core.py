"""Tests for orchestrator core."""

import pytest
from datetime import datetime
from orchestrator.core import (
    MaximusOrchestratorAgent,
    Campaign,
    CampaignStatus,
    AgentType,
    AgentCommand
)


@pytest.fixture
def orchestrator() -> MaximusOrchestratorAgent:
    """Create orchestrator instance."""
    return MaximusOrchestratorAgent(api_key="test_key_12345")


@pytest.mark.asyncio
async def test_plan_campaign_basic(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test basic campaign planning."""
    campaign = await orchestrator.plan_campaign(
        objective="Test web application security",
        scope=["192.168.1.0/24"],
        constraints={"no_dos": True}
    )
    
    assert campaign.objective == "Test web application security"
    assert campaign.status == CampaignStatus.PLANNED
    assert "192.168.1.0/24" in campaign.scope
    assert campaign.constraints["no_dos"] is True
    assert isinstance(campaign.id, str)
    assert len(campaign.phases) > 0


@pytest.mark.asyncio
async def test_plan_campaign_with_scope(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test campaign planning with multiple targets."""
    scope = ["target1.com", "target2.com", "192.168.1.0/24"]
    
    campaign = await orchestrator.plan_campaign(
        objective="Assess network security posture",
        scope=scope,
        constraints={"stealth": True, "no_dos": True}
    )
    
    assert campaign.scope == scope
    assert len(campaign.phases) > 0
    assert campaign.risk_assessment is not None


@pytest.mark.asyncio
async def test_coordinate_agents(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test agent coordination."""
    campaign = Campaign(
        id="test_campaign_001",
        objective="Test objective",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now(),
        phases=[
            {
                "name": "reconnaissance",
                "objectives": ["Network mapping"],
                "estimated_duration": "1h"
            }
        ]
    )
    
    commands = await orchestrator.coordinate_agents(campaign)
    
    assert len(commands) > 0
    assert commands[0].agent_type == AgentType.RECON
    assert commands[0].action == "execute_recon_mission"
    assert "targets" in commands[0].parameters
    assert commands[0].parameters["targets"] == campaign.scope


@pytest.mark.asyncio
async def test_coordinate_agents_multi_phase(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test coordination with multiple phases."""
    campaign = Campaign(
        id="test_campaign_002",
        objective="Full security assessment",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now(),
        phases=[
            {
                "name": "reconnaissance",
                "objectives": ["Mapping"],
                "estimated_duration": "2h"
            },
            {
                "name": "exploitation",
                "objectives": ["Find vulnerabilities"],
                "estimated_duration": "4h"
            },
            {
                "name": "post-exploitation",
                "objectives": ["Assess impact"],
                "estimated_duration": "2h"
            }
        ]
    )
    
    commands = await orchestrator.coordinate_agents(campaign)
    
    # Should have commands for all phases
    assert len(commands) >= 3
    
    # First should be recon
    assert commands[0].agent_type == AgentType.RECON
    
    # Should have exploit and postexploit commands
    agent_types = [cmd.agent_type for cmd in commands]
    assert AgentType.EXPLOIT in agent_types
    assert AgentType.POSTEXPLOIT in agent_types
    
    # Critical commands should require approval
    critical_commands = [cmd for cmd in commands if cmd.requires_approval]
    assert len(critical_commands) > 0


@pytest.mark.asyncio
async def test_analyze_results(orchestrator: MaximusOrchestratorAgent) -> None:
    """Test results analysis."""
    campaign = Campaign(
        id="test_campaign_003",
        objective="Web app test",
        scope=["webapp.example.com"],
        constraints={},
        status=CampaignStatus.COMPLETED,
        created_at=datetime.now()
    )
    
    results = {
        "phase": "reconnaissance",
        "findings": [
            {"type": "open_port", "port": 80, "service": "http"},
            {"type": "open_port", "port": 443, "service": "https"}
        ],
        "vulnerabilities": []
    }
    
    analysis = await orchestrator.analyze_results(campaign, results)
    
    assert isinstance(analysis, dict)
    assert len(analysis) > 0


def test_campaign_creation() -> None:
    """Test Campaign dataclass creation."""
    campaign = Campaign(
        id="test_001",
        objective="Test",
        scope=["target.com"],
        constraints={"test": True},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now()
    )
    
    assert campaign.id == "test_001"
    assert campaign.status == CampaignStatus.PLANNED
    assert len(campaign.phases) == 0
    assert len(campaign.hotl_checkpoints) == 0


def test_agent_command_creation() -> None:
    """Test AgentCommand dataclass creation."""
    command = AgentCommand(
        agent_type=AgentType.RECON,
        action="scan_network",
        parameters={"target": "192.168.1.0/24"},
        priority=10,
        requires_approval=False
    )
    
    assert command.agent_type == AgentType.RECON
    assert command.action == "scan_network"
    assert command.priority == 10
    assert command.requires_approval is False


def test_campaign_status_enum() -> None:
    """Test CampaignStatus enum."""
    assert CampaignStatus.PLANNED.value == "PLANNED"
    assert CampaignStatus.ACTIVE.value == "ACTIVE"
    assert CampaignStatus.COMPLETED.value == "COMPLETED"


def test_agent_type_enum() -> None:
    """Test AgentType enum."""
    assert AgentType.RECON.value == "recon"
    assert AgentType.EXPLOIT.value == "exploit"
    assert AgentType.POSTEXPLOIT.value == "postexploit"
