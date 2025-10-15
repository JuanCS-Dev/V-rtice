"""Complete tests for Reconnaissance Agent - 100% coverage."""

import pytest
from datetime import datetime
from typing import Any
from agents.recon.agent import (
    ReconAgent,
    ReconMission,
    ReconPhase,
    Target,
    Finding,
    FindingType
)


@pytest.fixture
def recon_agent() -> ReconAgent:
    """Create recon agent instance."""
    return ReconAgent()


@pytest.fixture
def sample_targets() -> list[Target]:
    """Create sample targets."""
    return [
        Target(
            identifier="192.168.1.100",
            target_type="ip",
            metadata={"priority": "high"}
        ),
        Target(
            identifier="example.com",
            target_type="domain",
            metadata={}
        )
    ]


@pytest.fixture
def sample_mission(sample_targets: list[Target]) -> ReconMission:
    """Create sample mission."""
    return ReconMission(
        id="mission_001",
        targets=sample_targets,
        phases=[ReconPhase.PASSIVE, ReconPhase.ACTIVE],
        constraints={"timeout": 300, "rate_limit": 10},
        status="pending",
        created_at=datetime.now()
    )


@pytest.mark.asyncio
async def test_execute_mission_complete(
    recon_agent: ReconAgent,
    sample_mission: ReconMission
) -> None:
    """Test complete mission execution."""
    result = await recon_agent.execute_mission(sample_mission)
    
    assert result["status"] == "completed"
    assert result["mission_id"] == "mission_001"
    assert result["findings_count"] > 0
    assert isinstance(result["findings"], list)
    assert "correlated" in result
    assert result["targets_scanned"] == 2


@pytest.mark.asyncio
async def test_execute_mission_all_phases(
    recon_agent: ReconAgent,
    sample_targets: list[Target]
) -> None:
    """Test mission with all phases."""
    mission = ReconMission(
        id="mission_002",
        targets=sample_targets,
        phases=[
            ReconPhase.PASSIVE,
            ReconPhase.ACTIVE,
            ReconPhase.DEEP_SCAN,
            ReconPhase.ENUMERATION
        ],
        constraints={},
        status="pending",
        created_at=datetime.now()
    )
    
    result = await recon_agent.execute_mission(mission)
    
    assert result["status"] == "completed"
    assert len(mission.findings) > 0


@pytest.mark.asyncio
async def test_passive_recon_domain(recon_agent: ReconAgent) -> None:
    """Test passive reconnaissance for domain."""
    targets = [
        Target(identifier="test.com", target_type="domain", metadata={})
    ]
    
    findings = await recon_agent._passive_recon(targets, {})
    
    assert len(findings) > 0
    assert findings[0].finding_type == FindingType.SUBDOMAIN
    assert findings[0].target == "test.com"
    assert findings[0].confidence >= 0.8


@pytest.mark.asyncio
async def test_passive_recon_ip(recon_agent: ReconAgent) -> None:
    """Test passive reconnaissance for IP (no subdomains)."""
    targets = [
        Target(identifier="192.168.1.1", target_type="ip", metadata={})
    ]
    
    findings = await recon_agent._passive_recon(targets, {})
    
    # IPs don't generate subdomain findings in passive phase
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_active_recon_ip(recon_agent: ReconAgent) -> None:
    """Test active reconnaissance for IP."""
    targets = [
        Target(identifier="192.168.1.100", target_type="ip", metadata={})
    ]
    
    findings = await recon_agent._active_recon(targets, {})
    
    assert len(findings) > 0
    port_findings = [f for f in findings if f.finding_type == FindingType.OPEN_PORT]
    assert len(port_findings) > 0
    assert all(f.confidence >= 0.9 for f in port_findings)


@pytest.mark.asyncio
async def test_active_recon_domain(recon_agent: ReconAgent) -> None:
    """Test active reconnaissance for domain."""
    targets = [
        Target(identifier="example.com", target_type="domain", metadata={})
    ]
    
    findings = await recon_agent._active_recon(targets, {})
    
    assert len(findings) > 0


@pytest.mark.asyncio
async def test_active_recon_unsupported_type(recon_agent: ReconAgent) -> None:
    """Test active recon with unsupported target type."""
    targets = [
        Target(identifier="test", target_type="url", metadata={})
    ]
    
    findings = await recon_agent._active_recon(targets, {})
    
    # URL type not supported in active_recon
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_deep_scan(recon_agent: ReconAgent, sample_targets: list[Target]) -> None:
    """Test deep scanning."""
    findings = await recon_agent._deep_scan(sample_targets, {})
    
    assert len(findings) > 0
    service_findings = [f for f in findings if f.finding_type == FindingType.SERVICE]
    assert len(service_findings) > 0
    assert service_findings[0].data["service"] == "http"


@pytest.mark.asyncio
async def test_enumeration(recon_agent: ReconAgent, sample_targets: list[Target]) -> None:
    """Test enumeration phase."""
    findings = await recon_agent._enumeration(sample_targets, {})
    
    assert len(findings) > 0
    tech_findings = [f for f in findings if f.finding_type == FindingType.TECHNOLOGY]
    assert len(tech_findings) > 0
    assert tech_findings[0].data["technology"] == "nginx"


def test_correlate_findings_empty(recon_agent: ReconAgent) -> None:
    """Test correlation with no findings."""
    correlated = recon_agent._correlate_findings([])
    
    assert correlated["targets_with_findings"] == 0
    assert correlated["high_confidence_findings"] == 0


def test_correlate_findings_multiple(recon_agent: ReconAgent) -> None:
    """Test correlation with multiple findings."""
    findings = [
        Finding(
            id="f1",
            target="192.168.1.100",
            finding_type=FindingType.OPEN_PORT,
            data={"port": 80},
            confidence=0.95,
            timestamp=datetime.now(),
            source="scanner"
        ),
        Finding(
            id="f2",
            target="192.168.1.100",
            finding_type=FindingType.SERVICE,
            data={"service": "http"},
            confidence=0.85,
            timestamp=datetime.now(),
            source="detector"
        ),
        Finding(
            id="f3",
            target="192.168.1.101",
            finding_type=FindingType.OPEN_PORT,
            data={"port": 443},
            confidence=0.92,
            timestamp=datetime.now(),
            source="scanner"
        )
    ]
    
    correlated = recon_agent._correlate_findings(findings)
    
    assert correlated["targets_with_findings"] == 2
    assert correlated["findings_by_type"]["open_port"] == 2
    assert correlated["findings_by_type"]["service"] == 1
    assert correlated["high_confidence_findings"] == 2


def test_finding_to_dict(recon_agent: ReconAgent) -> None:
    """Test finding conversion to dict."""
    finding = Finding(
        id="test_001",
        target="test.com",
        finding_type=FindingType.SUBDOMAIN,
        data={"subdomain": "www.test.com"},
        confidence=0.9,
        timestamp=datetime.now(),
        source="dns"
    )
    
    result = recon_agent._finding_to_dict(finding)
    
    assert result["id"] == "test_001"
    assert result["target"] == "test.com"
    assert result["type"] == "subdomain"
    assert result["confidence"] == 0.9
    assert result["source"] == "dns"


def test_get_mission_status_exists(
    recon_agent: ReconAgent,
    sample_mission: ReconMission
) -> None:
    """Test mission status retrieval."""
    recon_agent.active_missions[sample_mission.id] = sample_mission
    
    status = recon_agent.get_mission_status(sample_mission.id)
    
    assert status is not None
    assert status["mission_id"] == "mission_001"
    assert status["status"] == "pending"
    assert status["targets_count"] == 2


def test_get_mission_status_not_found(recon_agent: ReconAgent) -> None:
    """Test mission status for non-existent mission."""
    status = recon_agent.get_mission_status("invalid_id")
    
    assert status is None


def test_recon_agent_initialization() -> None:
    """Test agent initialization with config."""
    config = {"timeout": 300, "rate_limit": 10}
    agent = ReconAgent(collectors_config=config)
    
    assert agent.collectors_config == config
    assert len(agent.active_missions) == 0


def test_recon_agent_initialization_default() -> None:
    """Test agent initialization with defaults."""
    agent = ReconAgent()
    
    assert agent.collectors_config == {}
    assert isinstance(agent.active_missions, dict)


def test_target_creation() -> None:
    """Test Target dataclass."""
    target = Target(
        identifier="test.com",
        target_type="domain",
        metadata={"priority": "high"}
    )
    
    assert target.identifier == "test.com"
    assert target.target_type == "domain"
    assert target.metadata["priority"] == "high"


def test_finding_creation() -> None:
    """Test Finding dataclass."""
    now = datetime.now()
    finding = Finding(
        id="f001",
        target="test.com",
        finding_type=FindingType.OPEN_PORT,
        data={"port": 80},
        confidence=0.95,
        timestamp=now,
        source="nmap"
    )
    
    assert finding.id == "f001"
    assert finding.finding_type == FindingType.OPEN_PORT
    assert finding.confidence == 0.95


def test_recon_mission_creation(sample_targets: list[Target]) -> None:
    """Test ReconMission dataclass."""
    now = datetime.now()
    mission = ReconMission(
        id="m001",
        targets=sample_targets,
        phases=[ReconPhase.PASSIVE],
        constraints={"timeout": 300},
        status="pending",
        created_at=now
    )
    
    assert mission.id == "m001"
    assert len(mission.targets) == 2
    assert len(mission.findings) == 0


def test_recon_phase_enum() -> None:
    """Test ReconPhase enum."""
    assert ReconPhase.PASSIVE.value == "passive"
    assert ReconPhase.ACTIVE.value == "active"
    assert ReconPhase.DEEP_SCAN.value == "deep_scan"
    assert ReconPhase.ENUMERATION.value == "enumeration"


def test_finding_type_enum() -> None:
    """Test FindingType enum."""
    assert FindingType.OPEN_PORT.value == "open_port"
    assert FindingType.SERVICE.value == "service"
    assert FindingType.SUBDOMAIN.value == "subdomain"
    assert FindingType.TECHNOLOGY.value == "technology"
    assert FindingType.VULNERABILITY_HINT.value == "vulnerability_hint"
    assert FindingType.CREDENTIAL.value == "credential"
    assert FindingType.ENDPOINT.value == "endpoint"


@pytest.mark.asyncio
async def test_execute_phase_passive(
    recon_agent: ReconAgent,
    sample_targets: list[Target]
) -> None:
    """Test execute_phase with PASSIVE."""
    findings = await recon_agent._execute_phase(
        phase=ReconPhase.PASSIVE,
        targets=sample_targets,
        constraints={}
    )
    
    assert isinstance(findings, list)


@pytest.mark.asyncio
async def test_execute_phase_active(
    recon_agent: ReconAgent,
    sample_targets: list[Target]
) -> None:
    """Test execute_phase with ACTIVE."""
    findings = await recon_agent._execute_phase(
        phase=ReconPhase.ACTIVE,
        targets=sample_targets,
        constraints={}
    )
    
    assert len(findings) > 0


@pytest.mark.asyncio
async def test_execute_phase_deep_scan(
    recon_agent: ReconAgent,
    sample_targets: list[Target]
) -> None:
    """Test execute_phase with DEEP_SCAN."""
    findings = await recon_agent._execute_phase(
        phase=ReconPhase.DEEP_SCAN,
        targets=sample_targets,
        constraints={}
    )
    
    assert len(findings) > 0


@pytest.mark.asyncio
async def test_execute_phase_enumeration(
    recon_agent: ReconAgent,
    sample_targets: list[Target]
) -> None:
    """Test execute_phase with ENUMERATION."""
    findings = await recon_agent._execute_phase(
        phase=ReconPhase.ENUMERATION,
        targets=sample_targets,
        constraints={}
    )
    
    assert len(findings) > 0


@pytest.mark.asyncio
async def test_mission_updates_active_missions(
    recon_agent: ReconAgent,
    sample_mission: ReconMission
) -> None:
    """Test mission is tracked in active_missions."""
    await recon_agent.execute_mission(sample_mission)
    
    assert sample_mission.id in recon_agent.active_missions
    assert sample_mission.status == "completed"


@pytest.mark.asyncio
async def test_mission_failure_handling(recon_agent: ReconAgent) -> None:
    """Test mission failure handling."""
    # Patch _execute_phase to raise exception
    async def mock_execute_phase(*args: Any, **kwargs: Any) -> list[Finding]:
        raise ValueError("Simulated failure")
    
    original_execute_phase = recon_agent._execute_phase
    recon_agent._execute_phase = mock_execute_phase  # type: ignore
    
    mission = ReconMission(
        id="fail_mission",
        targets=[Target(identifier="test.com", target_type="domain", metadata={})],
        phases=[ReconPhase.PASSIVE],
        constraints={},
        status="pending",
        created_at=datetime.now()
    )
    
    # Should raise exception and update status
    with pytest.raises(ValueError, match="Simulated failure"):
        await recon_agent.execute_mission(mission)
    
    assert mission.status == "failed"
    
    # Restore original method
    recon_agent._execute_phase = original_execute_phase  # type: ignore
