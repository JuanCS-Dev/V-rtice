"""
Tests for Phase 3: Orchestration Components.

Validates attack chains, campaign management, and intelligence fusion.
"""
import pytest
import asyncio
from datetime import datetime
from .attack_chain import (
    AttackChain,
    AttackStage,
    StageType,
    StageStatus
)
from .campaign_manager import (
    CampaignManager,
    Campaign,
    CampaignTarget,
    CampaignStatus,
    TargetPriority
)
from .intelligence_fusion import (
    IntelligenceFusion,
    IntelligenceSource,
    ThreatLevel
)
from backend.security.offensive.core.base import OffensiveTool, ToolResult


class MockTool(OffensiveTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, should_succeed: bool = True):
        super().__init__(name=name, category="test")
        self.should_succeed = should_succeed
        self.execution_count = 0
    
    async def execute(self, **kwargs) -> ToolResult:
        self.execution_count += 1
        await asyncio.sleep(0.1)  # Simulate work
        
        return ToolResult(
            success=self.should_succeed,
            data={"result": f"executed_{self.execution_count}"},
            message=f"Tool {self.name} executed"
        )
    
    async def validate(self) -> bool:
        return True


# ============================================================================
# ATTACK CHAIN TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_attack_chain_creation():
    """Test attack chain creation."""
    chain = AttackChain("test_chain")
    
    assert chain.chain_name == "test_chain"
    assert len(chain.stages) == 0
    assert len(chain.tools) == 0


@pytest.mark.asyncio
async def test_attack_chain_add_stage():
    """Test adding stages to chain."""
    chain = AttackChain("test_chain")
    
    stage = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={"target": "$target"}
    )
    
    chain.add_stage(stage)
    
    assert len(chain.stages) == 1
    assert chain.stages[0].name == "recon"


@pytest.mark.asyncio
async def test_attack_chain_dependency_validation():
    """Test stage dependency validation."""
    chain = AttackChain("test_chain")
    
    # Add stage with non-existent dependency - should raise error
    with pytest.raises(Exception):
        stage = AttackStage(
            name="exploit",
            stage_type=StageType.EXPLOITATION,
            tool_name="exploiter",
            config={},
            dependencies=["nonexistent"]
        )
        chain.add_stage(stage)


@pytest.mark.asyncio
async def test_attack_chain_execution_order():
    """Test stage execution order with dependencies."""
    chain = AttackChain("test_chain")
    
    # Add stages with dependencies
    stage1 = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={}
    )
    
    stage2 = AttackStage(
        name="weaponize",
        stage_type=StageType.WEAPONIZATION,
        tool_name="payload_gen",
        config={},
        dependencies=["recon"]
    )
    
    stage3 = AttackStage(
        name="exploit",
        stage_type=StageType.EXPLOITATION,
        tool_name="exploiter",
        config={},
        dependencies=["weaponize"]
    )
    
    chain.add_stage(stage1)
    chain.add_stage(stage2)
    chain.add_stage(stage3)
    
    order = chain._get_execution_order()
    
    assert order[0].name == "recon"
    assert order[1].name == "weaponize"
    assert order[2].name == "exploit"


@pytest.mark.asyncio
async def test_attack_chain_full_execution():
    """Test complete attack chain execution."""
    chain = AttackChain("test_chain")
    
    # Register tools
    tool1 = MockTool("scanner")
    tool2 = MockTool("exploiter")
    
    chain.register_tool(tool1)
    chain.register_tool(tool2)
    
    # Add stages
    stage1 = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={"target": "$target"}
    )
    
    stage2 = AttackStage(
        name="exploit",
        stage_type=StageType.EXPLOITATION,
        tool_name="exploiter",
        config={},
        dependencies=["recon"]
    )
    
    chain.add_stage(stage1)
    chain.add_stage(stage2)
    
    # Execute chain
    result = await chain.execute(target="192.168.1.1")
    
    assert result.success
    assert result.data.success
    assert len(result.data.stages) == 2
    assert result.data.stages[0].status == StageStatus.SUCCESS
    assert result.data.stages[1].status == StageStatus.SUCCESS


@pytest.mark.asyncio
async def test_attack_chain_failed_stage():
    """Test chain behavior with failed stage."""
    chain = AttackChain("test_chain")
    
    # Register tools - one fails
    tool1 = MockTool("scanner", should_succeed=False)
    tool2 = MockTool("exploiter")
    
    chain.register_tool(tool1)
    chain.register_tool(tool2)
    
    # Add stages
    stage1 = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={},
        required=True,
        retry_count=1  # Only 1 attempt
    )
    
    stage2 = AttackStage(
        name="exploit",
        stage_type=StageType.EXPLOITATION,
        tool_name="exploiter",
        config={},
        dependencies=["recon"]
    )
    
    chain.add_stage(stage1)
    chain.add_stage(stage2)
    
    # Execute chain
    result = await chain.execute(target="192.168.1.1")
    
    assert not result.success
    assert result.data.stages[0].status == StageStatus.FAILED
    assert result.data.stages[1].status == StageStatus.SKIPPED


@pytest.mark.asyncio
async def test_attack_chain_validation():
    """Test attack chain validation."""
    chain = AttackChain("test_chain")
    
    tool1 = MockTool("scanner")
    chain.register_tool(tool1)
    
    stage1 = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={}
    )
    chain.add_stage(stage1)
    
    is_valid = await chain.validate()
    assert is_valid


# ============================================================================
# CAMPAIGN MANAGER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_campaign_creation():
    """Test campaign creation."""
    manager = CampaignManager()
    
    target1 = CampaignTarget(
        identifier="192.168.1.1",
        priority=TargetPriority.HIGH,
        attack_chain="basic_chain"
    )
    
    campaign = Campaign(
        name="test_campaign",
        description="Test campaign",
        objectives=["Gain access"],
        targets=[target1],
        start_date=datetime.utcnow()
    )
    
    manager.create_campaign(campaign)
    
    assert "test_campaign" in manager.campaigns
    assert manager.campaigns["test_campaign"].status == CampaignStatus.PLANNED


@pytest.mark.asyncio
async def test_campaign_execution():
    """Test campaign execution."""
    manager = CampaignManager()
    
    # Create attack chain
    chain = AttackChain("basic_chain")
    tool = MockTool("scanner")
    chain.register_tool(tool)
    
    stage = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={}
    )
    chain.add_stage(stage)
    
    manager.register_attack_chain(chain)
    
    # Create campaign
    target1 = CampaignTarget(
        identifier="192.168.1.1",
        priority=TargetPriority.HIGH,
        attack_chain="basic_chain"
    )
    
    campaign = Campaign(
        name="test_campaign",
        description="Test",
        objectives=["Test"],
        targets=[target1],
        start_date=datetime.utcnow(),
        max_concurrent=1,
        retry_failed=False
    )
    
    manager.create_campaign(campaign)
    
    # Execute
    result = await manager.execute("test_campaign")
    
    assert result.success
    assert result.data.status == CampaignStatus.COMPLETED
    assert len(result.data.completed_targets) == 1


@pytest.mark.asyncio
async def test_campaign_multi_target():
    """Test campaign with multiple targets."""
    manager = CampaignManager()
    
    # Create chain
    chain = AttackChain("basic_chain")
    tool = MockTool("scanner")
    chain.register_tool(tool)
    
    stage = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={}
    )
    chain.add_stage(stage)
    
    manager.register_attack_chain(chain)
    
    # Create campaign with multiple targets
    targets = [
        CampaignTarget(
            identifier=f"192.168.1.{i}",
            priority=TargetPriority.HIGH,
            attack_chain="basic_chain"
        )
        for i in range(1, 4)
    ]
    
    campaign = Campaign(
        name="multi_target",
        description="Multi-target test",
        objectives=["Test"],
        targets=targets,
        start_date=datetime.utcnow(),
        max_concurrent=2,
        retry_failed=False
    )
    
    manager.create_campaign(campaign)
    
    # Execute
    result = await manager.execute("multi_target")
    
    assert result.success
    assert len(result.data.completed_targets) == 3


@pytest.mark.asyncio
async def test_campaign_status():
    """Test campaign status tracking."""
    manager = CampaignManager()
    
    # Create simple campaign
    chain = AttackChain("basic_chain")
    tool = MockTool("scanner")
    chain.register_tool(tool)
    
    stage = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={}
    )
    chain.add_stage(stage)
    
    manager.register_attack_chain(chain)
    
    target = CampaignTarget(
        identifier="192.168.1.1",
        priority=TargetPriority.HIGH,
        attack_chain="basic_chain"
    )
    
    campaign = Campaign(
        name="status_test",
        description="Test",
        objectives=["Test"],
        targets=[target],
        start_date=datetime.utcnow()
    )
    
    manager.create_campaign(campaign)
    
    # Get initial status
    status = manager.get_campaign_status("status_test")
    
    assert status["status"] == CampaignStatus.PLANNED.value
    assert status["progress"]["total"] == 1
    assert status["progress"]["completed"] == 0


# ============================================================================
# INTELLIGENCE FUSION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_intelligence_fusion_creation():
    """Test intelligence fusion creation."""
    fusion = IntelligenceFusion()
    
    assert len(fusion.profiles) == 0
    assert len(fusion.intelligence_history) == 0


@pytest.mark.asyncio
async def test_intelligence_ingest():
    """Test intelligence data ingestion."""
    fusion = IntelligenceFusion()
    
    data = {
        "ip_addresses": ["192.168.1.1"],
        "domains": ["example.com"],
        "open_ports": {80: "http", 443: "https"},
        "os_fingerprint": "Linux",
        "vulnerabilities": ["CVE-2021-1234"]
    }
    
    result = await fusion.execute(
        operation="ingest",
        target="test_target",
        intelligence_data=data
    )
    
    assert result.success
    assert "test_target" in fusion.profiles
    
    profile = fusion.profiles["test_target"]
    assert "192.168.1.1" in profile.ip_addresses
    assert "example.com" in profile.domains
    assert 80 in profile.open_ports
    assert len(profile.vulnerabilities) > 0


@pytest.mark.asyncio
async def test_intelligence_analyze():
    """Test target analysis."""
    fusion = IntelligenceFusion()
    
    # Ingest data
    data = {
        "ip_addresses": ["192.168.1.1"],
        "open_ports": {22: "ssh", 80: "http", 443: "https"},
        "vulnerabilities": ["CVE-2021-1234", "CVE-2021-5678"]
    }
    
    await fusion.execute(
        operation="ingest",
        target="test_target",
        intelligence_data=data
    )
    
    # Analyze
    result = await fusion.execute(
        operation="analyze",
        target="test_target"
    )
    
    assert result.success
    
    profile = result.data
    assert profile.attack_surface_score > 0.0
    assert profile.threat_level != ThreatLevel.MINIMAL
    assert len(profile.recommended_strategies) > 0


@pytest.mark.asyncio
async def test_intelligence_query():
    """Test intelligence querying."""
    fusion = IntelligenceFusion()
    
    # Ingest multiple targets
    for i in range(1, 4):
        data = {
            "ip_addresses": [f"192.168.1.{i}"],
            "vulnerabilities": ["CVE-2021-1234"] if i < 3 else []
        }
        
        await fusion.execute(
            operation="ingest",
            target=f"target_{i}",
            intelligence_data=data
        )
        
        await fusion.execute(
            operation="analyze",
            target=f"target_{i}"
        )
    
    # Query all
    result = await fusion.execute(operation="query")
    
    assert result.success
    assert len(result.data.targets) == 3
    
    # Query with filter
    result = await fusion.execute(
        operation="query",
        filters={"has_vulnerabilities": True}
    )
    
    assert result.success
    assert len(result.data.targets) == 2


@pytest.mark.asyncio
async def test_intelligence_export():
    """Test intelligence export."""
    fusion = IntelligenceFusion()
    
    # Ingest data
    data = {
        "ip_addresses": ["192.168.1.1"],
        "domains": ["example.com"]
    }
    
    await fusion.execute(
        operation="ingest",
        target="test_target",
        intelligence_data=data
    )
    
    # Export single target
    result = await fusion.execute(
        operation="export",
        target="test_target"
    )
    
    assert result.success
    assert result.data["identifier"] == "test_target"
    assert "192.168.1.1" in result.data["ip_addresses"]
    
    # Export all
    result = await fusion.execute(operation="export")
    
    assert result.success
    assert "profiles" in result.data
    assert "test_target" in result.data["profiles"]


@pytest.mark.asyncio
async def test_intelligence_correlation():
    """Test intelligence correlation."""
    fusion = IntelligenceFusion()
    
    # Ingest targets with shared IP
    data1 = {
        "ip_addresses": ["192.168.1.1"],
        "domains": ["site1.com"]
    }
    
    data2 = {
        "ip_addresses": ["192.168.1.1"],
        "domains": ["site2.com"]
    }
    
    await fusion.execute(
        operation="ingest",
        target="target_1",
        intelligence_data=data1
    )
    
    await fusion.execute(
        operation="ingest",
        target="target_2",
        intelligence_data=data2
    )
    
    # Query and check correlations
    result = await fusion.execute(operation="query")
    
    assert result.success
    assert len(result.data.correlations) > 0


@pytest.mark.asyncio
async def test_intelligence_threat_assessment():
    """Test threat level assessment."""
    fusion = IntelligenceFusion()
    
    # Low threat target
    low_threat = {
        "ip_addresses": ["192.168.1.1"],
        "open_ports": {22: "ssh"}
    }
    
    # High threat target
    high_threat = {
        "ip_addresses": ["192.168.1.2"],
        "open_ports": {
            21: "ftp", 22: "ssh", 23: "telnet",
            80: "http", 443: "https", 445: "smb"
        },
        "vulnerabilities": [
            "CVE-2021-1234",
            "CVE-2021-5678",
            "CVE-2020-9999"
        ]
    }
    
    await fusion.execute(
        operation="ingest",
        target="low_target",
        intelligence_data=low_threat
    )
    
    await fusion.execute(
        operation="ingest",
        target="high_target",
        intelligence_data=high_threat
    )
    
    # Analyze both
    low_profile = await fusion.execute(
        operation="analyze",
        target="low_target"
    )
    
    high_profile = await fusion.execute(
        operation="analyze",
        target="high_target"
    )
    
    # Compare threat levels numerically using enum values
    threat_levels = {
        ThreatLevel.MINIMAL: 1,
        ThreatLevel.LOW: 2,
        ThreatLevel.MODERATE: 3,
        ThreatLevel.HIGH: 4,
        ThreatLevel.CRITICAL: 5
    }
    
    assert threat_levels[low_profile.data.threat_level] < threat_levels[high_profile.data.threat_level]
    assert high_profile.data.attack_surface_score > low_profile.data.attack_surface_score


@pytest.mark.asyncio
async def test_intelligence_validation():
    """Test intelligence fusion validation."""
    fusion = IntelligenceFusion()
    
    is_valid = await fusion.validate()
    assert is_valid


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_chain_with_intelligence_fusion():
    """Test attack chain integrated with intelligence fusion."""
    fusion = IntelligenceFusion()
    chain = AttackChain("intel_chain")
    
    # Mock tool that generates intelligence
    class IntelTool(MockTool):
        async def execute(self, **kwargs):
            return ToolResult(
                success=True,
                data={
                    "ports": [
                        type('Port', (), {'number': 80, 'state': 'open'})(),
                        type('Port', (), {'number': 443, 'state': 'open'})()
                    ]
                },
                message="Scan complete"
            )
    
    tool = IntelTool("scanner")
    chain.register_tool(tool)
    
    stage = AttackStage(
        name="recon",
        stage_type=StageType.RECONNAISSANCE,
        tool_name="scanner",
        config={}
    )
    chain.add_stage(stage)
    
    # Execute chain
    result = await chain.execute(target="192.168.1.1")
    
    assert result.success
    
    # Ingest results into intelligence fusion
    chain_result = result.data
    intel_data = {
        "ip_addresses": ["192.168.1.1"],
        "open_ports": {80: "http", 443: "https"}
    }
    
    await fusion.execute(
        operation="ingest",
        target="192.168.1.1",
        intelligence_data=intel_data,
        source=IntelligenceSource.RECONNAISSANCE
    )
    
    # Verify intelligence
    profile_result = await fusion.execute(
        operation="analyze",
        target="192.168.1.1"
    )
    
    assert profile_result.success
    assert len(profile_result.data.recommended_strategies) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
