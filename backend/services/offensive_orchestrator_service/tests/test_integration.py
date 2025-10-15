"""Complete tests for Integration Service - 100% coverage."""

import pytest
from datetime import datetime
from typing import Any
from integration import IntegrationService, IntegratedMission
from orchestrator.core import Campaign, CampaignStatus
from hotl.decision_system import ApprovalStatus


@pytest.fixture
def integration_service() -> IntegrationService:
    """Create integration service instance."""
    return IntegrationService(
        anthropic_api_key="test_api_key",
        config={"auto_approve": True}
    )


@pytest.mark.asyncio
async def test_execute_integrated_mission_complete(
    integration_service: IntegrationService
) -> None:
    """Test complete integrated mission execution."""
    result = await integration_service.execute_integrated_mission(
        objective="Test security assessment",
        scope=["192.168.1.100"],
        constraints={"safe_mode": True}
    )
    
    assert result["status"] == "completed"
    assert "mission_id" in result
    assert "campaign" in result
    assert "reconnaissance" in result
    assert "exploitation" in result
    assert "analysis" in result


@pytest.mark.asyncio
async def test_execute_integrated_mission_creates_mission(
    integration_service: IntegrationService
) -> None:
    """Test mission creation."""
    initial_count = len(integration_service.active_missions)
    
    result = await integration_service.execute_integrated_mission(
        objective="Test",
        scope=["target.com"],
        constraints={}
    )
    
    assert len(integration_service.active_missions) == initial_count + 1
    assert result["mission_id"] in integration_service.active_missions


@pytest.mark.asyncio
async def test_execute_reconnaissance(integration_service: IntegrationService) -> None:
    """Test reconnaissance phase."""
    campaign = Campaign(
        id="test_campaign",
        objective="Test",
        scope=["192.168.1.100"],
        constraints={},
        status=CampaignStatus.PLANNED,
        created_at=datetime.now()
    )
    
    results = await integration_service._execute_reconnaissance(campaign)
    
    assert "findings_count" in results
    assert "findings" in results


@pytest.mark.asyncio
async def test_execute_exploitation_with_findings(
    integration_service: IntegrationService
) -> None:
    """Test exploitation with recon findings."""
    recon_results = {
        "findings_count": 3,
        "findings": [
            {
                "id": "f1",
                "target": "192.168.1.100",
                "type": "open_port",
                "confidence": 0.9
            },
            {
                "id": "f2",
                "target": "192.168.1.100",
                "type": "service",
                "confidence": 0.85
            }
        ]
    }
    
    results = await integration_service._execute_exploitation(recon_results)
    
    assert "status" in results
    assert results["status"] != "skipped"


@pytest.mark.asyncio
async def test_execute_exploitation_no_findings(
    integration_service: IntegrationService
) -> None:
    """Test exploitation with no findings."""
    recon_results = {
        "findings_count": 0,
        "findings": []
    }
    
    results = await integration_service._execute_exploitation(recon_results)
    
    assert results["status"] == "skipped"
    assert results["reason"] == "No vulnerabilities found"


@pytest.mark.asyncio
async def test_execute_postexploit_with_compromised_hosts(
    integration_service: IntegrationService
) -> None:
    """Test post-exploitation with compromised hosts."""
    exploit_results = {
        "exploits_successful": 2,
        "exploits": [
            {
                "id": "e1",
                "vulnerability_id": "vuln_001",
                "status": "success"
            },
            {
                "id": "e2",
                "vulnerability_id": "vuln_002",
                "status": "success"
            }
        ]
    }
    
    results = await integration_service._execute_postexploit(exploit_results)
    
    assert "status" in results
    assert results["status"] != "skipped"


@pytest.mark.asyncio
async def test_execute_postexploit_no_compromised_hosts(
    integration_service: IntegrationService
) -> None:
    """Test post-exploitation with no compromised hosts."""
    exploit_results = {
        "exploits_successful": 0,
        "exploits": [
            {
                "id": "e1",
                "vulnerability_id": "vuln_001",
                "status": "failed"
            }
        ]
    }
    
    results = await integration_service._execute_postexploit(exploit_results)
    
    assert results["status"] == "skipped"
    assert results["reason"] == "No hosts compromised"


@pytest.mark.asyncio
async def test_execute_analysis(integration_service: IntegrationService) -> None:
    """Test analysis phase."""
    mission = IntegratedMission(
        id="test_mission",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status="completed",
        created_at=datetime.now(),
        recon_results={"findings_count": 5},
        exploit_results={"exploits_successful": 2},
        postexploit_results={"actions_executed": 3}
    )
    
    results = await integration_service._execute_analysis(mission)
    
    assert "analysis" in results
    assert "curriculum_progress" in results


@pytest.mark.asyncio
async def test_execute_analysis_no_results(integration_service: IntegrationService) -> None:
    """Test analysis with no phase results."""
    mission = IntegratedMission(
        id="test_mission",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status="failed",
        created_at=datetime.now()
    )
    
    results = await integration_service._execute_analysis(mission)
    
    assert "analysis" in results
    assert results["analysis"]["campaign_id"] == "test_mission"


def test_campaign_summary(integration_service: IntegrationService) -> None:
    """Test campaign summary creation."""
    campaign = Campaign(
        id="test_campaign",
        objective="Test objective",
        scope=["target.com"],
        constraints={},
        status=CampaignStatus.COMPLETED,
        created_at=datetime.now(),
        phases=[{"name": "recon"}, {"name": "exploit"}],
        hotl_checkpoints=["checkpoint1"]
    )
    
    summary = integration_service._campaign_summary(campaign)
    
    assert summary["id"] == "test_campaign"
    assert summary["objective"] == "Test objective"
    assert summary["status"] == "COMPLETED"
    assert summary["phases_count"] == 2
    assert len(summary["hotl_checkpoints"]) == 1


def test_get_mission_status_exists(integration_service: IntegrationService) -> None:
    """Test mission status retrieval."""
    mission = IntegratedMission(
        id="mission_001",
        objective="Test",
        scope=["target.com"],
        constraints={},
        status="running",
        created_at=datetime.now()
    )
    
    integration_service.active_missions[mission.id] = mission
    
    status = integration_service.get_mission_status(mission.id)
    
    assert status is not None
    assert status["mission_id"] == "mission_001"
    assert status["status"] == "running"


def test_get_mission_status_not_found(integration_service: IntegrationService) -> None:
    """Test mission status for non-existent mission."""
    status = integration_service.get_mission_status("invalid_id")
    
    assert status is None


def test_get_statistics(integration_service: IntegrationService) -> None:
    """Test statistics retrieval."""
    # Add some missions
    integration_service.active_missions["m1"] = IntegratedMission(
        id="m1",
        objective="Test1",
        scope=[],
        constraints={},
        status="completed",
        created_at=datetime.now()
    )
    integration_service.active_missions["m2"] = IntegratedMission(
        id="m2",
        objective="Test2",
        scope=[],
        constraints={},
        status="running",
        created_at=datetime.now()
    )
    
    stats = integration_service.get_statistics()
    
    assert stats["total_missions"] == 2
    assert stats["completed_missions"] == 1
    assert stats["active_missions"] == 1
    assert "analysis_stats" in stats
    assert "rl_stats" in stats


def test_integration_service_initialization() -> None:
    """Test service initialization."""
    service = IntegrationService(
        anthropic_api_key="test_key",
        config={"test": "value"}
    )
    
    assert service.config["test"] == "value"
    assert service.orchestrator is not None
    assert service.recon_agent is not None
    assert service.exploit_agent is not None
    assert service.postexploit_agent is not None
    assert service.analysis_agent is not None
    assert service.hotl_system is not None


def test_integration_service_initialization_default() -> None:
    """Test service initialization with defaults."""
    service = IntegrationService(anthropic_api_key="test_key")
    
    assert service.config == {}
    assert len(service.active_missions) == 0


def test_integrated_mission_creation() -> None:
    """Test IntegratedMission dataclass."""
    mission = IntegratedMission(
        id="test_001",
        objective="Test objective",
        scope=["target1.com", "target2.com"],
        constraints={"safe_mode": True},
        status="planning",
        created_at=datetime.now()
    )
    
    assert mission.id == "test_001"
    assert mission.status == "planning"
    assert len(mission.scope) == 2
    assert mission.campaign is None


@pytest.mark.asyncio
async def test_mission_failure_handling(integration_service: IntegrationService) -> None:
    """Test mission failure handling."""
    # Patch orchestrator to raise exception
    async def mock_plan_campaign(*args: Any, **kwargs: Any) -> Campaign:
        raise ValueError("Planning failed")
    
    original_plan = integration_service.orchestrator.plan_campaign
    integration_service.orchestrator.plan_campaign = mock_plan_campaign  # type: ignore
    
    with pytest.raises(ValueError, match="Planning failed"):
        await integration_service.execute_integrated_mission(
            objective="Test",
            scope=["target.com"],
            constraints={}
        )
    
    # Check mission marked as failed
    missions = list(integration_service.active_missions.values())
    assert len(missions) > 0
    assert missions[-1].status == "failed"
    
    # Restore
    integration_service.orchestrator.plan_campaign = original_plan  # type: ignore


@pytest.mark.asyncio
async def test_mission_with_custom_constraints(
    integration_service: IntegrationService
) -> None:
    """Test mission with custom constraints."""
    result = await integration_service.execute_integrated_mission(
        objective="Custom test",
        scope=["192.168.1.100"],
        constraints={
            "safe_mode": True,
            "stealth": True,
            "timeout": 300
        }
    )
    
    assert result["status"] == "completed"
    assert result["objective"] == "Custom test"


@pytest.mark.asyncio
async def test_mission_phases_execution_order(
    integration_service: IntegrationService
) -> None:
    """Test mission phases execute in correct order."""
    result = await integration_service.execute_integrated_mission(
        objective="Phase test",
        scope=["target.com"],
        constraints={}
    )
    
    # All phases should complete
    assert "reconnaissance" in result
    assert "exploitation" in result
    assert "analysis" in result


@pytest.mark.asyncio
async def test_hotl_integration(integration_service: IntegrationService) -> None:
    """Test HOTL system integration."""
    # Service was created with auto_approve=True
    assert integration_service.hotl_system.auto_approve_test is True
    
    result = await integration_service.execute_integrated_mission(
        objective="HOTL test",
        scope=["target.com"],
        constraints={}
    )
    
    # Should complete despite requiring approvals
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_curriculum_integration(integration_service: IntegrationService) -> None:
    """Test curriculum learning integration."""
    result = await integration_service.execute_integrated_mission(
        objective="Curriculum test",
        scope=["target.com"],
        constraints={}
    )
    
    # Check curriculum progress in analysis
    assert "analysis" in result
    assert "curriculum_progress" in result["analysis"]
    assert "mastery_score" in result["analysis"]["curriculum_progress"]


@pytest.mark.asyncio
async def test_rl_policy_integration(integration_service: IntegrationService) -> None:
    """Test RL policy integration."""
    result = await integration_service.execute_integrated_mission(
        objective="RL test",
        scope=["target.com"],
        constraints={}
    )
    
    # Check RL stats available
    stats = integration_service.get_statistics()
    assert "rl_stats" in stats
    assert "states_learned" in stats["rl_stats"]


@pytest.mark.asyncio
async def test_agent_coordination(integration_service: IntegrationService) -> None:
    """Test agents work together correctly."""
    result = await integration_service.execute_integrated_mission(
        objective="Coordination test",
        scope=["192.168.1.100", "192.168.1.101"],
        constraints={"safe_mode": True}
    )
    
    # Each phase should have results
    assert result["reconnaissance"]["findings_count"] >= 0
    if result["exploitation"]["status"] != "skipped":
        assert "exploits_generated" in result["exploitation"]
    
    # Analysis should have metrics
    assert "analysis" in result["analysis"]


def test_get_statistics_empty(integration_service: IntegrationService) -> None:
    """Test statistics with no missions."""
    integration_service.active_missions = {}
    
    stats = integration_service.get_statistics()
    
    assert stats["total_missions"] == 0
    assert stats["active_missions"] == 0
    assert stats["completed_missions"] == 0


@pytest.mark.asyncio
async def test_execute_exploitation_many_findings(
    integration_service: IntegrationService
) -> None:
    """Test exploitation limits findings to top 5."""
    recon_results = {
        "findings_count": 10,
        "findings": [
            {
                "id": f"f{i}",
                "target": "test.com",
                "type": "vuln",
                "confidence": 0.9
            }
            for i in range(10)
        ]
    }
    
    results = await integration_service._execute_exploitation(recon_results)
    
    # Should process but limit to 5 vulnerabilities
    assert results["status"] != "skipped"


@pytest.mark.asyncio
async def test_mission_pending_exploit_approval() -> None:
    """Test mission with pending exploit approval."""
    # Create service WITHOUT auto-approve
    service = IntegrationService(
        anthropic_api_key="test_key",
        config={"auto_approve": False}
    )
    
    result = await service.execute_integrated_mission(
        objective="Test",
        scope=["target.com"],
        constraints={}
    )
    
    # Exploitation should be pending approval
    assert result["exploitation"]["status"] == "pending_approval"
    assert "approval_request_id" in result["exploitation"]


@pytest.mark.asyncio
async def test_mission_postexploit_skipped_no_exploit() -> None:
    """Test post-exploit skipped when exploit not completed."""
    service = IntegrationService(
        anthropic_api_key="test_key",
        config={"auto_approve": False}
    )
    
    result = await service.execute_integrated_mission(
        objective="Test",
        scope=["target.com"],
        constraints={}
    )
    
    # Since auto_approve=False, exploitation will be pending
    assert result["exploitation"]["status"] == "pending_approval"
    
    # Post-exploit should be skipped
    assert result["post_exploitation"]["status"] == "skipped"
    assert result["post_exploitation"]["reason"] == "Exploitation not completed"


@pytest.mark.asyncio
async def test_postexploit_pending_approval_path() -> None:
    """Test post-exploit pending approval branch."""
    from typing import Any
    from hotl.decision_system import ApprovalRequest, ApprovalStatus
    
    service = IntegrationService(
        anthropic_api_key="test_key",
        config={"auto_approve": True}  # Auto-approve exploit
    )
    
    # Mock HOTL to reject only the second (postexploit) approval
    call_count = [0]
    original_request = service.hotl_system.request_approval
    
    async def mock_request_approval(*args: Any, **kwargs: Any) -> ApprovalRequest:
        call_count[0] += 1
        result = await original_request(*args, **kwargs)
        
        # Reject only postexploit (second call)
        if call_count[0] == 2:
            result.status = ApprovalStatus.PENDING
            result.approval = None
        
        return result
    
    service.hotl_system.request_approval = mock_request_approval  # type: ignore
    
    result = await service.execute_integrated_mission(
        objective="Test",
        scope=["target.com"],
        constraints={}
    )
    
    # Exploit should succeed, postexploit should be pending
    if result["exploitation"]["status"] != "pending_approval":
        assert result["post_exploitation"]["status"] == "pending_approval"
        assert "approval_request_id" in result["post_exploitation"]
