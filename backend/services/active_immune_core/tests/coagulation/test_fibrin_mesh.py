"""Tests for Fibrin Mesh Containment - Secondary Hemostasis

Comprehensive test suite for FibrinMeshContainment system.
Target: 90%+ coverage

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH
"""

import asyncio
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from prometheus_client import REGISTRY

from coagulation.fibrin_mesh import (
    FibrinMeshContainment,
    FibrinMeshMetrics,
    FibrinMeshPolicy,
    FibrinMeshResult,
    FibrinStrength,
)
from coagulation.models import (
    BlastRadius,
    ContainmentResult,
    EnrichedThreat,
    FibrinMeshDeploymentError,
    ThreatSeverity,
    ThreatSource,
)


@pytest.fixture(autouse=True)
def cleanup_prometheus():
    """Clean up Prometheus registry between tests"""
    # Collect all metrics to remove
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    yield
    # Clean up after test
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


@pytest.fixture
def fibrin_mesh():
    """Create FibrinMeshContainment instance"""
    return FibrinMeshContainment()


@pytest.fixture
def low_threat():
    """Create low severity threat"""
    source = ThreatSource(ip="192.168.1.100", subnet="192.168.1.0/24")
    blast_radius = BlastRadius(
        affected_hosts=["host1"],
        affected_zones=["DMZ"],
    )
    return EnrichedThreat(
        threat_id="threat_low_001",
        source=source,
        severity=ThreatSeverity.LOW,
        threat_type="port_scan",
        blast_radius=blast_radius,
    )


@pytest.fixture
def high_threat():
    """Create high severity threat"""
    source = ThreatSource(ip="10.0.0.50", subnet="10.0.0.0/24")
    blast_radius = BlastRadius(
        affected_hosts=["host1", "host2", "host3"],
        affected_zones=["DMZ", "APPLICATION"],
        estimated_spread_rate=2.5,
        max_impact_score=0.8,
    )
    return EnrichedThreat(
        threat_id="threat_high_001",
        source=source,
        severity=ThreatSeverity.HIGH,
        threat_type="malware",
        targeted_ports=[445, 139],
        compromised_credentials=["admin"],
        affected_hosts=["host1", "host2"],
        blast_radius=blast_radius,
    )


@pytest.fixture
def critical_threat():
    """Create critical severity threat"""
    source = ThreatSource(
        ip="172.16.0.100",
        hostname="malicious.example.com",
        subnet="172.16.0.0/24",
    )
    blast_radius = BlastRadius(
        affected_hosts=["critical1", "critical2"],
        affected_zones=["DATA", "MANAGEMENT"],
        estimated_spread_rate=5.0,
        max_impact_score=0.95,
    )
    return EnrichedThreat(
        threat_id="threat_critical_001",
        source=source,
        severity=ThreatSeverity.CRITICAL,
        threat_type="ransomware",
        signature="wannacry",
        ttps=["T1486", "T1027"],
        blast_radius=blast_radius,
    )


class TestFibrinStrength:
    """Test FibrinStrength constants"""

    def test_strength_levels_exist(self):
        """Test all strength levels are defined"""
        assert FibrinStrength.LIGHT == "light"
        assert FibrinStrength.MODERATE == "moderate"
        assert FibrinStrength.STRONG == "strong"
        assert FibrinStrength.ABSOLUTE == "absolute"


class TestFibrinMeshPolicy:
    """Test FibrinMeshPolicy"""

    def test_policy_creation(self):
        """Test policy creation with all fields"""
        policy = FibrinMeshPolicy(
            strength=FibrinStrength.MODERATE,
            affected_zones=["DMZ", "APP"],
            isolation_rules={"block_ip": "1.2.3.4"},
            duration=timedelta(minutes=30),
            auto_dissolve=True,
        )

        assert policy.strength == FibrinStrength.MODERATE
        assert len(policy.affected_zones) == 2
        assert policy.duration == timedelta(minutes=30)
        assert policy.auto_dissolve is True
        assert policy.created_at is not None

    def test_policy_defaults(self):
        """Test policy with default values"""
        policy = FibrinMeshPolicy(
            strength=FibrinStrength.LIGHT,
            affected_zones=["DMZ"],
            isolation_rules={},
            duration=timedelta(minutes=15),
        )

        assert policy.auto_dissolve is False


class TestFibrinMeshResult:
    """Test FibrinMeshResult"""

    def test_result_creation(self):
        """Test result creation"""
        policy = FibrinMeshPolicy(
            strength=FibrinStrength.MODERATE,
            affected_zones=["DMZ"],
            isolation_rules={},
            duration=timedelta(minutes=30),
        )

        result = FibrinMeshResult(
            status="DEPLOYED",
            mesh_id="mesh_001",
            policy=policy,
            zone_result={"status": "applied"},
            traffic_result={"status": "applied"},
            firewall_result={"status": "applied"},
        )

        assert result.status == "DEPLOYED"
        assert result.mesh_id == "mesh_001"
        assert result.policy == policy
        assert result.deployed_at is not None


class TestFibrinMeshContainment:
    """Test FibrinMeshContainment main functionality"""

    def test_initialization(self, fibrin_mesh):
        """Test fibrin mesh initialization"""
        assert fibrin_mesh is not None
        assert fibrin_mesh.active_meshes == {}
        assert fibrin_mesh.mesh_metrics is not None
        assert fibrin_mesh.zone_isolator is None
        assert fibrin_mesh.traffic_shaper is None
        assert fibrin_mesh.firewall_controller is None

    def test_set_dependencies(self, fibrin_mesh):
        """Test dependency injection"""
        zone_isolator = MagicMock()
        traffic_shaper = MagicMock()
        firewall_controller = MagicMock()

        fibrin_mesh.set_dependencies(
            zone_isolator=zone_isolator,
            traffic_shaper=traffic_shaper,
            firewall_controller=firewall_controller,
        )

        assert fibrin_mesh.zone_isolator == zone_isolator
        assert fibrin_mesh.traffic_shaper == traffic_shaper
        assert fibrin_mesh.firewall_controller == firewall_controller

    def test_calculate_required_strength_low(self, fibrin_mesh, low_threat):
        """Test strength calculation for low severity"""
        strength = fibrin_mesh._calculate_required_strength(low_threat)
        assert strength == FibrinStrength.LIGHT

    def test_calculate_required_strength_high(self, fibrin_mesh, high_threat):
        """Test strength calculation for high severity"""
        strength = fibrin_mesh._calculate_required_strength(high_threat)
        assert strength == FibrinStrength.MODERATE

    def test_calculate_required_strength_critical(self, fibrin_mesh, critical_threat):
        """Test strength calculation for critical severity"""
        strength = fibrin_mesh._calculate_required_strength(critical_threat)
        assert strength == FibrinStrength.STRONG

    def test_calculate_required_strength_catastrophic(self, fibrin_mesh):
        """Test strength calculation for catastrophic severity"""
        source = ThreatSource(ip="1.2.3.4")
        threat = EnrichedThreat(
            threat_id="threat_cat",
            source=source,
            severity=ThreatSeverity.CATASTROPHIC,
            threat_type="nation_state",
        )
        strength = fibrin_mesh._calculate_required_strength(threat)
        assert strength == FibrinStrength.ABSOLUTE

    def test_identify_affected_zones_from_blast_radius(self, fibrin_mesh, high_threat):
        """Test zone identification from blast radius"""
        zones = fibrin_mesh._identify_affected_zones(
            high_threat.source,
            high_threat.blast_radius,
        )
        assert "DMZ" in zones
        assert "APPLICATION" in zones

    def test_identify_affected_zones_defaults_to_dmz(self, fibrin_mesh):
        """Test zone identification defaults to DMZ"""
        source = ThreatSource(ip="1.2.3.4")
        blast_radius = BlastRadius()  # Empty
        zones = fibrin_mesh._identify_affected_zones(source, blast_radius)
        assert "DMZ" in zones

    def test_generate_isolation_rules_light(self, fibrin_mesh, low_threat):
        """Test isolation rules for LIGHT strength"""
        rules = fibrin_mesh._generate_isolation_rules(
            low_threat,
            FibrinStrength.LIGHT,
        )
        assert "block_source_ip" in rules
        assert rules["block_source_ip"] == low_threat.source.ip
        assert rules["log_all_attempts"] is True
        assert "full_network_isolation" not in rules

    def test_generate_isolation_rules_strong(self, fibrin_mesh, critical_threat):
        """Test isolation rules for STRONG strength"""
        rules = fibrin_mesh._generate_isolation_rules(
            critical_threat,
            FibrinStrength.STRONG,
        )
        assert "block_source_ip" in rules
        assert "isolate_subnet" in rules
        assert "quarantine_hosts" in rules
        assert "disable_lateral_movement" in rules
        assert rules["isolate_subnet"] == critical_threat.source.subnet

    def test_generate_isolation_rules_absolute(self, fibrin_mesh, critical_threat):
        """Test isolation rules for ABSOLUTE strength"""
        rules = fibrin_mesh._generate_isolation_rules(
            critical_threat,
            FibrinStrength.ABSOLUTE,
        )
        assert "full_network_isolation" in rules
        assert rules["full_network_isolation"] is True
        assert "disable_outbound" in rules
        assert "forensics_snapshot" in rules
        assert "memory_dump" in rules

    def test_calculate_duration_low(self, fibrin_mesh, low_threat):
        """Test duration calculation for low severity"""
        duration = fibrin_mesh._calculate_duration(low_threat)
        assert duration == timedelta(minutes=15)

    def test_calculate_duration_high(self, fibrin_mesh, high_threat):
        """Test duration calculation for high severity"""
        duration = fibrin_mesh._calculate_duration(high_threat)
        assert duration == timedelta(hours=1)

    def test_calculate_duration_critical(self, fibrin_mesh, critical_threat):
        """Test duration calculation for critical severity"""
        duration = fibrin_mesh._calculate_duration(critical_threat)
        assert duration == timedelta(hours=4)

    def test_generate_mesh_id(self, fibrin_mesh, low_threat):
        """Test mesh ID generation"""
        mesh_id = fibrin_mesh._generate_mesh_id(low_threat)
        assert mesh_id.startswith("mesh_threat_low_001_")
        assert len(mesh_id) > len("mesh_threat_low_001_")

    @pytest.mark.asyncio
    async def test_deploy_fibrin_mesh_success(self, fibrin_mesh, high_threat):
        """Test successful fibrin mesh deployment"""
        result = await fibrin_mesh.deploy_fibrin_mesh(high_threat)

        assert result.status == "DEPLOYED"
        assert result.mesh_id.startswith("mesh_threat_high_001_")
        assert result.policy.strength == FibrinStrength.MODERATE
        assert len(result.policy.affected_zones) > 0
        assert result.zone_result is not None
        assert result.traffic_result is not None
        assert result.firewall_result is not None

    @pytest.mark.asyncio
    async def test_deploy_fibrin_mesh_tracking(self, fibrin_mesh, high_threat):
        """Test mesh is tracked after deployment"""
        initial_count = fibrin_mesh.get_active_mesh_count()

        result = await fibrin_mesh.deploy_fibrin_mesh(high_threat)

        assert fibrin_mesh.get_active_mesh_count() == initial_count + 1
        assert result.mesh_id in fibrin_mesh.active_meshes

    @pytest.mark.asyncio
    async def test_deploy_fibrin_mesh_auto_dissolve(self, fibrin_mesh, high_threat):
        """Test auto-dissolve is scheduled for non-critical threats"""
        result = await fibrin_mesh.deploy_fibrin_mesh(high_threat)

        assert result.policy.auto_dissolve is True
        # Auto-dissolve task is scheduled (tested via mock in integration)

    @pytest.mark.asyncio
    async def test_deploy_fibrin_mesh_no_auto_dissolve_critical(
        self, fibrin_mesh, critical_threat
    ):
        """Test no auto-dissolve for critical threats"""
        result = await fibrin_mesh.deploy_fibrin_mesh(critical_threat)

        assert result.policy.auto_dissolve is False

    @pytest.mark.asyncio
    async def test_deploy_fibrin_mesh_with_primary_containment(
        self, fibrin_mesh, high_threat
    ):
        """Test deployment with primary containment result"""
        primary = ContainmentResult(
            status="CONTAINED",
            containment_type="primary",
            affected_zones=["DMZ"],
        )

        result = await fibrin_mesh.deploy_fibrin_mesh(
            high_threat,
            primary_containment=primary,
        )

        assert result.status == "DEPLOYED"

    @pytest.mark.asyncio
    async def test_dissolve_mesh_success(self, fibrin_mesh, high_threat):
        """Test successful mesh dissolution"""
        # Deploy first
        result = await fibrin_mesh.deploy_fibrin_mesh(high_threat)
        mesh_id = result.mesh_id

        # Dissolve
        dissolved = await fibrin_mesh.dissolve_mesh(mesh_id)

        assert dissolved is True
        assert mesh_id not in fibrin_mesh.active_meshes
        assert fibrin_mesh.get_active_mesh_count() == 0

    @pytest.mark.asyncio
    async def test_dissolve_mesh_not_found(self, fibrin_mesh):
        """Test dissolving non-existent mesh"""
        dissolved = await fibrin_mesh.dissolve_mesh("non_existent_mesh")
        assert dissolved is False

    @pytest.mark.asyncio
    async def test_check_mesh_health_success(self, fibrin_mesh, high_threat):
        """Test checking mesh health"""
        # Deploy first
        result = await fibrin_mesh.deploy_fibrin_mesh(high_threat)
        mesh_id = result.mesh_id

        # Check health
        health = await fibrin_mesh.check_mesh_health(mesh_id)

        assert health.mesh_id == mesh_id
        assert health.effectiveness > 0.0
        assert health.status in ["HEALTHY", "DEGRADED"]
        assert health.zone_health is not None
        assert health.traffic_health is not None

    @pytest.mark.asyncio
    async def test_check_mesh_health_not_found(self, fibrin_mesh):
        """Test checking health of non-existent mesh"""
        with pytest.raises(ValueError, match="not found"):
            await fibrin_mesh.check_mesh_health("non_existent_mesh")

    def test_get_active_mesh_count(self, fibrin_mesh):
        """Test getting active mesh count"""
        assert fibrin_mesh.get_active_mesh_count() == 0

    def test_get_active_mesh_ids_empty(self, fibrin_mesh):
        """Test getting active mesh IDs when empty"""
        assert fibrin_mesh.get_active_mesh_ids() == []

    @pytest.mark.asyncio
    async def test_get_active_mesh_ids_with_meshes(self, fibrin_mesh, high_threat):
        """Test getting active mesh IDs with meshes"""
        result = await fibrin_mesh.deploy_fibrin_mesh(high_threat)

        mesh_ids = fibrin_mesh.get_active_mesh_ids()
        assert result.mesh_id in mesh_ids
        assert len(mesh_ids) == 1

    @pytest.mark.asyncio
    async def test_multiple_mesh_deployments(
        self, fibrin_mesh, low_threat, high_threat
    ):
        """Test deploying multiple meshes"""
        result1 = await fibrin_mesh.deploy_fibrin_mesh(low_threat)
        result2 = await fibrin_mesh.deploy_fibrin_mesh(high_threat)

        assert fibrin_mesh.get_active_mesh_count() == 2
        assert result1.mesh_id != result2.mesh_id
        assert result1.mesh_id in fibrin_mesh.active_meshes
        assert result2.mesh_id in fibrin_mesh.active_meshes

    @pytest.mark.asyncio
    async def test_apply_zone_isolation(self, fibrin_mesh):
        """Test zone isolation application"""
        policy = FibrinMeshPolicy(
            strength=FibrinStrength.MODERATE,
            affected_zones=["DMZ", "APP"],
            isolation_rules={},
            duration=timedelta(minutes=30),
        )

        result = await fibrin_mesh._apply_zone_isolation(policy)

        assert result["status"] == "applied"
        assert result["zones"] == ["DMZ", "APP"]

    @pytest.mark.asyncio
    async def test_apply_traffic_shaping(self, fibrin_mesh):
        """Test traffic shaping application"""
        policy = FibrinMeshPolicy(
            strength=FibrinStrength.STRONG,
            affected_zones=["DMZ"],
            isolation_rules={},
            duration=timedelta(minutes=30),
        )

        result = await fibrin_mesh._apply_traffic_shaping(policy)

        assert result["status"] == "applied"
        assert result["strength"] == FibrinStrength.STRONG

    @pytest.mark.asyncio
    async def test_apply_firewall_rules(self, fibrin_mesh):
        """Test firewall rules application"""
        policy = FibrinMeshPolicy(
            strength=FibrinStrength.MODERATE,
            affected_zones=["DMZ"],
            isolation_rules={"block_ip": "1.2.3.4", "log": True},
            duration=timedelta(minutes=30),
        )

        result = await fibrin_mesh._apply_firewall_rules(policy)

        assert result["status"] == "applied"
        assert result["rules_count"] == 2

    @pytest.mark.asyncio
    async def test_schedule_fibrinolysis(self, fibrin_mesh):
        """Test fibrinolysis scheduling directly"""
        # Create a simple threat without auto-dissolve
        source = ThreatSource(ip="1.2.3.4")
        threat = EnrichedThreat(
            threat_id="threat_test_fibrinolysis",
            source=source,
            severity=ThreatSeverity.CRITICAL,  # No auto-dissolve
            threat_type="test",
        )
        
        # Deploy mesh
        result = await fibrin_mesh.deploy_fibrin_mesh(threat)
        mesh_id = result.mesh_id

        # Verify it's active
        assert mesh_id in fibrin_mesh.active_meshes

        # Schedule fibrinolysis (short duration for test)
        duration = timedelta(seconds=0.05)
        
        # Wait for scheduled dissolution
        await fibrin_mesh._schedule_fibrinolysis(mesh_id, duration)

        # Should be dissolved
        assert mesh_id not in fibrin_mesh.active_meshes


class TestFibrinMeshMetrics:
    """Test Prometheus metrics integration"""

    def test_metrics_initialization(self):
        """Test metrics are initialized"""
        metrics = FibrinMeshMetrics()

        assert metrics.deployments_total is not None
        assert metrics.active_meshes is not None
        assert metrics.effectiveness is not None
        assert metrics.deployment_duration is not None

    @pytest.mark.asyncio
    async def test_metrics_updated_on_deployment(self, fibrin_mesh, high_threat):
        """Test metrics are updated on deployment"""
        initial_count = fibrin_mesh.mesh_metrics.active_meshes._value.get()

        await fibrin_mesh.deploy_fibrin_mesh(high_threat)

        # Active meshes gauge should be updated
        current_count = fibrin_mesh.mesh_metrics.active_meshes._value.get()
        assert current_count == initial_count + 1


class TestFibrinMeshErrors:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_deployment_handles_exception(self, fibrin_mesh, high_threat):
        """Test deployment handles exceptions gracefully"""
        # Mock _apply_zone_isolation to raise exception
        async def mock_raise(*args, **kwargs):
            raise Exception("Simulated network error")

        fibrin_mesh._apply_zone_isolation = mock_raise

        with pytest.raises(FibrinMeshDeploymentError, match="Failed to deploy"):
            await fibrin_mesh.deploy_fibrin_mesh(high_threat)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
