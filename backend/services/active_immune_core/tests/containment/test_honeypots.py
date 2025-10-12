"""Tests for Dynamic Honeypots - Deception & TTP Collection

Comprehensive test suite for honeypot orchestration,
deception engine, and threat intelligence collection.

Target: 90%+ coverage

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import pytest
from datetime import datetime
from prometheus_client import REGISTRY

from containment.honeypots import (
    AttackerProfile,
    DeceptionEngine,
    HoneypotConfig,
    HoneypotDeployment,
    HoneypotLevel,
    HoneypotMetrics,
    HoneypotOrchestrator,
    HoneypotResult,
    HoneypotType,
    TTPs,
)


@pytest.fixture(autouse=True)
def cleanup_prometheus():
    """Clean up Prometheus registry between tests"""
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    yield
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


@pytest.fixture
def ssh_honeypot_config():
    """Create SSH honeypot config"""
    return HoneypotConfig(
        name="ssh_test",
        honeypot_type=HoneypotType.SSH,
        level=HoneypotLevel.MEDIUM,
        ports=[22],
        image="cowrie/cowrie:latest",
    )


@pytest.fixture
def web_honeypot_config():
    """Create web honeypot config"""
    return HoneypotConfig(
        name="web_test",
        honeypot_type=HoneypotType.HTTP,
        level=HoneypotLevel.HIGH,
        ports=[80, 443],
        image="mushorg/glutton:latest",
    )


@pytest.fixture
def honeypot_orchestrator():
    """Create HoneypotOrchestrator instance"""
    return HoneypotOrchestrator()


@pytest.fixture
def deception_engine():
    """Create DeceptionEngine instance"""
    return DeceptionEngine()


class TestHoneypotType:
    """Test HoneypotType enum"""

    def test_honeypot_types_exist(self):
        """Test all honeypot types are defined"""
        assert HoneypotType.SSH.value == "ssh"
        assert HoneypotType.HTTP.value == "http"
        assert HoneypotType.FTP.value == "ftp"
        assert HoneypotType.SMTP.value == "smtp"
        assert HoneypotType.DATABASE.value == "database"
        assert HoneypotType.INDUSTRIAL.value == "industrial"


class TestHoneypotLevel:
    """Test HoneypotLevel enum"""

    def test_honeypot_levels_exist(self):
        """Test all interaction levels are defined"""
        assert HoneypotLevel.LOW.value == "low"
        assert HoneypotLevel.MEDIUM.value == "medium"
        assert HoneypotLevel.HIGH.value == "high"


class TestHoneypotConfig:
    """Test HoneypotConfig dataclass"""

    def test_config_creation(self, ssh_honeypot_config):
        """Test honeypot config creation"""
        assert ssh_honeypot_config.name == "ssh_test"
        assert ssh_honeypot_config.honeypot_type == HoneypotType.SSH
        assert ssh_honeypot_config.level == HoneypotLevel.MEDIUM
        assert 22 in ssh_honeypot_config.ports
        assert ssh_honeypot_config.log_all_traffic is True


class TestTTPs:
    """Test TTPs dataclass"""

    def test_ttps_creation(self):
        """Test TTPs creation"""
        ttps = TTPs(
            tactics=["Initial Access"],
            techniques=["T1078"],
            tools_used=["nmap"],
            commands=["ls -la"],
        )

        assert "Initial Access" in ttps.tactics
        assert "T1078" in ttps.techniques
        assert "nmap" in ttps.tools_used


class TestAttackerProfile:
    """Test AttackerProfile dataclass"""

    def test_profile_creation(self):
        """Test attacker profile creation"""
        profile = AttackerProfile(
            source_ip="192.168.1.100",
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            total_attempts=10,
            threat_score=0.75,
        )

        assert profile.source_ip == "192.168.1.100"
        assert profile.total_attempts == 10
        assert profile.threat_score == 0.75


class TestHoneypotOrchestrator:
    """Test HoneypotOrchestrator"""

    def test_initialization(self, honeypot_orchestrator):
        """Test orchestrator initialization"""
        assert honeypot_orchestrator.active_honeypots == {}
        assert honeypot_orchestrator.metrics is not None

    @pytest.mark.asyncio
    async def test_deploy_honeypot(
        self, honeypot_orchestrator, ssh_honeypot_config
    ):
        """Test deploying honeypot"""
        deployment = await honeypot_orchestrator.deploy_honeypot(
            ssh_honeypot_config
        )

        assert deployment.honeypot_id.startswith("honeypot_ssh_test_")
        assert deployment.status == "RUNNING"
        assert deployment.deployed_at is not None
        assert deployment.container_id is not None

    @pytest.mark.asyncio
    async def test_deploy_multiple_honeypots(
        self, honeypot_orchestrator, ssh_honeypot_config, web_honeypot_config
    ):
        """Test deploying multiple honeypots"""
        deployment1 = await honeypot_orchestrator.deploy_honeypot(
            ssh_honeypot_config
        )
        deployment2 = await honeypot_orchestrator.deploy_honeypot(
            web_honeypot_config
        )

        assert len(honeypot_orchestrator.active_honeypots) == 2
        assert deployment1.honeypot_id != deployment2.honeypot_id

    @pytest.mark.asyncio
    async def test_stop_honeypot(
        self, honeypot_orchestrator, ssh_honeypot_config
    ):
        """Test stopping honeypot"""
        deployment = await honeypot_orchestrator.deploy_honeypot(
            ssh_honeypot_config
        )

        stopped = await honeypot_orchestrator.stop_honeypot(
            deployment.honeypot_id
        )

        assert stopped is True
        assert deployment.honeypot_id not in honeypot_orchestrator.active_honeypots

    @pytest.mark.asyncio
    async def test_stop_nonexistent_honeypot(self, honeypot_orchestrator):
        """Test stopping nonexistent honeypot"""
        stopped = await honeypot_orchestrator.stop_honeypot("nonexistent")
        assert stopped is False

    @pytest.mark.asyncio
    async def test_collect_ttps(
        self, honeypot_orchestrator, ssh_honeypot_config
    ):
        """Test collecting TTPs from honeypot"""
        deployment = await honeypot_orchestrator.deploy_honeypot(
            ssh_honeypot_config
        )

        ttps = await honeypot_orchestrator.collect_ttps(deployment.honeypot_id)

        assert ttps is not None
        assert len(ttps.tactics) > 0
        assert len(ttps.techniques) > 0

    @pytest.mark.asyncio
    async def test_collect_ttps_nonexistent(self, honeypot_orchestrator):
        """Test collecting TTPs from nonexistent honeypot"""
        ttps = await honeypot_orchestrator.collect_ttps("nonexistent")
        assert ttps is None

    def test_get_active_honeypots(self, honeypot_orchestrator):
        """Test getting active honeypots list"""
        active = honeypot_orchestrator.get_active_honeypots()
        assert isinstance(active, list)
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_get_active_honeypots_after_deployment(
        self, honeypot_orchestrator, ssh_honeypot_config
    ):
        """Test getting active honeypots after deployment"""
        deployment = await honeypot_orchestrator.deploy_honeypot(
            ssh_honeypot_config
        )

        active = honeypot_orchestrator.get_active_honeypots()
        assert len(active) == 1
        assert deployment.honeypot_id in active

    def test_get_honeypot_status(self, honeypot_orchestrator):
        """Test getting honeypot status"""
        status = honeypot_orchestrator.get_honeypot_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_honeypot_status_after_deployment(
        self, honeypot_orchestrator, ssh_honeypot_config
    ):
        """Test getting status after deployment"""
        deployment = await honeypot_orchestrator.deploy_honeypot(
            ssh_honeypot_config
        )

        status = honeypot_orchestrator.get_honeypot_status(
            deployment.honeypot_id
        )
        assert status is not None
        assert status.status == "RUNNING"


class TestDeceptionEngine:
    """Test DeceptionEngine"""

    def test_initialization(self, deception_engine):
        """Test deception engine initialization"""
        assert deception_engine.orchestrator is not None
        assert deception_engine.deployment_strategy == {}

    def test_initialization_with_orchestrator(self):
        """Test initialization with custom orchestrator"""
        orchestrator = HoneypotOrchestrator()
        engine = DeceptionEngine(orchestrator=orchestrator)

        assert engine.orchestrator == orchestrator

    @pytest.mark.asyncio
    async def test_deploy_adaptive_honeypots_default(self, deception_engine):
        """Test adaptive deployment with no threat intel"""
        result = await deception_engine.deploy_adaptive_honeypots({})

        assert result.status == "SUCCESS"
        assert len(result.honeypots_deployed) == 1  # Default SSH

    @pytest.mark.asyncio
    async def test_deploy_adaptive_honeypots_ssh_threat(
        self, deception_engine
    ):
        """Test adaptive deployment for SSH threat"""
        threat_intel = {"targeted_services": ["ssh"]}

        result = await deception_engine.deploy_adaptive_honeypots(threat_intel)

        assert result.status == "SUCCESS"
        assert len(result.honeypots_deployed) >= 1

    @pytest.mark.asyncio
    async def test_deploy_adaptive_honeypots_web_threat(
        self, deception_engine
    ):
        """Test adaptive deployment for web threat"""
        threat_intel = {"targeted_services": ["http", "web"]}

        result = await deception_engine.deploy_adaptive_honeypots(threat_intel)

        assert result.status == "SUCCESS"
        assert len(result.honeypots_deployed) >= 1

    @pytest.mark.asyncio
    async def test_deploy_adaptive_honeypots_database_threat(
        self, deception_engine
    ):
        """Test adaptive deployment for database threat"""
        threat_intel = {"targeted_services": ["database"]}

        result = await deception_engine.deploy_adaptive_honeypots(threat_intel)

        assert result.status == "SUCCESS"

    @pytest.mark.asyncio
    async def test_deploy_adaptive_honeypots_multiple_threats(
        self, deception_engine
    ):
        """Test adaptive deployment for multiple threats"""
        threat_intel = {"targeted_services": ["ssh", "http", "database"]}

        result = await deception_engine.deploy_adaptive_honeypots(threat_intel)

        assert result.status == "SUCCESS"
        assert len(result.honeypots_deployed) >= 3

    @pytest.mark.asyncio
    async def test_collect_intelligence(self, deception_engine):
        """Test collecting intelligence from honeypots"""
        # Deploy some honeypots first
        await deception_engine.deploy_adaptive_honeypots({})

        intelligence = await deception_engine.collect_intelligence()

        assert "total_honeypots" in intelligence
        assert "total_interactions" in intelligence
        assert "unique_attackers" in intelligence
        assert "ttps" in intelligence

    @pytest.mark.asyncio
    async def test_collect_intelligence_empty(self, deception_engine):
        """Test collecting intelligence with no honeypots"""
        intelligence = await deception_engine.collect_intelligence()

        assert intelligence["total_honeypots"] == 0
        assert intelligence["total_interactions"] == 0

    @pytest.mark.asyncio
    async def test_adapt_to_threat_low(self, deception_engine):
        """Test adapting to low threat level"""
        await deception_engine.adapt_to_threat("low")

        assert deception_engine.deployment_strategy["count"] == 1
        assert deception_engine.deployment_strategy["level"] == HoneypotLevel.LOW

    @pytest.mark.asyncio
    async def test_adapt_to_threat_high(self, deception_engine):
        """Test adapting to high threat level"""
        await deception_engine.adapt_to_threat("high")

        assert deception_engine.deployment_strategy["count"] == 3
        assert deception_engine.deployment_strategy["level"] == HoneypotLevel.HIGH

    @pytest.mark.asyncio
    async def test_adapt_to_threat_critical(self, deception_engine):
        """Test adapting to critical threat level"""
        await deception_engine.adapt_to_threat("critical")

        assert deception_engine.deployment_strategy["count"] == 5

    def test_get_deployment_stats(self, deception_engine):
        """Test getting deployment statistics"""
        stats = deception_engine.get_deployment_stats()

        assert "active_honeypots" in stats
        assert "deployment_strategy" in stats

    def test_generate_honeypot_configs_empty(self, deception_engine):
        """Test config generation with empty threat intel"""
        configs = deception_engine._generate_honeypot_configs({})

        assert len(configs) == 1
        assert configs[0].honeypot_type == HoneypotType.SSH

    def test_generate_honeypot_configs_ssh(self, deception_engine):
        """Test config generation for SSH threat"""
        threat_intel = {"targeted_services": ["ssh"]}
        configs = deception_engine._generate_honeypot_configs(threat_intel)

        assert any(c.honeypot_type == HoneypotType.SSH for c in configs)

    def test_generate_honeypot_configs_web(self, deception_engine):
        """Test config generation for web threat"""
        threat_intel = {"targeted_services": ["web"]}
        configs = deception_engine._generate_honeypot_configs(threat_intel)

        assert any(c.honeypot_type == HoneypotType.HTTP for c in configs)


class TestHoneypotMetrics:
    """Test Prometheus metrics"""

    def test_metrics_initialization(self):
        """Test metrics are initialized"""
        metrics = HoneypotMetrics()

        assert metrics.deployments_total is not None
        assert metrics.active_honeypots is not None
        assert metrics.interactions_total is not None
        assert metrics.ttps_collected_total is not None


class TestHoneypotErrorHandling:
    """Test error handling in honeypots"""

    @pytest.mark.asyncio
    async def test_deploy_with_exception(self):
        """Test deployment handles exceptions"""
        orchestrator = HoneypotOrchestrator()

        # Mock deploy to raise exception
        async def mock_raise(*args, **kwargs):
            raise Exception("Simulated deployment error")

        original_deploy = orchestrator.deploy_honeypot
        orchestrator.deploy_honeypot = mock_raise

        engine = DeceptionEngine(orchestrator=orchestrator)

        result = await engine.deploy_adaptive_honeypots({})

        # Should handle gracefully
        assert result.status == "FAILED"
        assert len(result.errors) > 0

        # Restore
        orchestrator.deploy_honeypot = original_deploy

    @pytest.mark.asyncio
    async def test_adaptive_deployment_exception_handling(
        self, deception_engine
    ):
        """Test exception handling in adaptive deployment"""
        # Mock _generate_honeypot_configs to raise exception
        def mock_raise(*args, **kwargs):
            raise RuntimeError("Config generation error")

        deception_engine._generate_honeypot_configs = mock_raise

        result = await deception_engine.deploy_adaptive_honeypots({})

        assert result.status == "FAILED"
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
