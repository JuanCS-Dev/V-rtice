"""Tests for Zone Isolation Engine

Comprehensive test suite for zone isolation, firewall control,
network segmentation, and zero-trust enforcement.

Target: 90%+ coverage

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância vence!
"""

import pytest
from datetime import datetime
from prometheus_client import REGISTRY

from containment.zone_isolation import (
    DynamicFirewallController,
    FirewallRule,
    IsolationLevel,
    NetworkSegmenter,
    TrustLevel,
    ZeroTrustAccessController,
    ZoneIsolationEngine,
    ZoneIsolationMetrics,
    ZoneIsolationResult,
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
def firewall_controller():
    """Create DynamicFirewallController instance"""
    return DynamicFirewallController()


@pytest.fixture
def network_segmenter():
    """Create NetworkSegmenter instance"""
    return NetworkSegmenter()


@pytest.fixture
def zero_trust_controller():
    """Create ZeroTrustAccessController instance"""
    return ZeroTrustAccessController()


@pytest.fixture
def zone_isolation_engine():
    """Create ZoneIsolationEngine instance"""
    return ZoneIsolationEngine()


class TestTrustLevel:
    """Test TrustLevel enum"""

    def test_trust_levels_exist(self):
        """Test all trust levels are defined"""
        assert TrustLevel.UNTRUSTED.value == 0
        assert TrustLevel.LIMITED.value == 1
        assert TrustLevel.RESTRICTED.value == 2
        assert TrustLevel.CRITICAL.value == 3

    def test_trust_levels_comparable(self):
        """Test trust levels can be compared by value"""
        assert TrustLevel.UNTRUSTED.value < TrustLevel.CRITICAL.value
        assert TrustLevel.CRITICAL.value > TrustLevel.LIMITED.value


class TestIsolationLevel:
    """Test IsolationLevel enum"""

    def test_isolation_levels_exist(self):
        """Test all isolation levels are defined"""
        assert IsolationLevel.MONITORING.value == "monitoring"
        assert IsolationLevel.RATE_LIMITING.value == "rate_limiting"
        assert IsolationLevel.BLOCKING.value == "blocking"
        assert IsolationLevel.FULL_ISOLATION.value == "full_isolation"


class TestFirewallRule:
    """Test FirewallRule dataclass"""

    def test_rule_creation_minimal(self):
        """Test firewall rule with minimal fields"""
        rule = FirewallRule(action="DROP")
        assert rule.action == "DROP"
        assert rule.protocol is None
        assert rule.source_ip is None

    def test_rule_creation_full(self):
        """Test firewall rule with all fields"""
        rule = FirewallRule(
            action="DROP",
            protocol="tcp",
            source_ip="192.168.1.100",
            destination_ip="10.0.0.50",
            source_port=12345,
            destination_port=80,
            interface="eth0",
            comment="Block malicious traffic",
        )
        assert rule.action == "DROP"
        assert rule.protocol == "tcp"
        assert rule.source_ip == "192.168.1.100"
        assert rule.destination_port == 80
        assert rule.comment == "Block malicious traffic"


class TestZoneIsolationResult:
    """Test ZoneIsolationResult dataclass"""

    def test_result_creation(self):
        """Test isolation result creation"""
        result = ZoneIsolationResult(
            status="SUCCESS",
            zones_isolated=["DMZ", "APP"],
            firewall_rules_applied=5,
            network_policies_created=2,
            zero_trust_enforced=True,
        )
        assert result.status == "SUCCESS"
        assert len(result.zones_isolated) == 2
        assert result.firewall_rules_applied == 5
        assert result.zero_trust_enforced is True
        assert isinstance(result.timestamp, datetime)


class TestDynamicFirewallController:
    """Test DynamicFirewallController"""

    def test_initialization(self, firewall_controller):
        """Test firewall controller initialization"""
        assert firewall_controller.backend == "iptables"
        assert firewall_controller.active_rules == {}

    def test_initialization_custom_backend(self):
        """Test initialization with custom backend"""
        controller = DynamicFirewallController(backend="nftables")
        assert controller.backend == "nftables"

    @pytest.mark.asyncio
    async def test_apply_rule(self, firewall_controller):
        """Test applying single firewall rule"""
        rule = FirewallRule(
            action="DROP",
            protocol="tcp",
            source_ip="1.2.3.4",
        )

        result = await firewall_controller.apply_rule(rule, chain="INPUT")

        assert result is True
        assert "INPUT" in firewall_controller.active_rules
        assert rule in firewall_controller.active_rules["INPUT"]

    @pytest.mark.asyncio
    async def test_apply_multiple_rules(self, firewall_controller):
        """Test applying multiple rules to same chain"""
        rule1 = FirewallRule(action="DROP", source_ip="1.2.3.4")
        rule2 = FirewallRule(action="REJECT", source_ip="5.6.7.8")

        await firewall_controller.apply_rule(rule1, "INPUT")
        await firewall_controller.apply_rule(rule2, "INPUT")

        assert len(firewall_controller.active_rules["INPUT"]) == 2

    @pytest.mark.asyncio
    async def test_apply_rules_batch(self, firewall_controller):
        """Test applying rules in batch"""
        rules = [
            FirewallRule(action="DROP", source_ip=f"192.168.1.{i}")
            for i in range(10, 15)
        ]

        applied = await firewall_controller.apply_rules_batch(rules, "FORWARD")

        assert applied == 5
        assert len(firewall_controller.active_rules["FORWARD"]) == 5

    @pytest.mark.asyncio
    async def test_remove_rule(self, firewall_controller):
        """Test removing firewall rule"""
        rule = FirewallRule(action="DROP", source_ip="1.2.3.4")
        await firewall_controller.apply_rule(rule, "INPUT")

        removed = await firewall_controller.remove_rule(rule, "INPUT")

        assert removed is True
        assert rule not in firewall_controller.active_rules.get("INPUT", [])

    def test_get_active_rules_all(self, firewall_controller):
        """Test getting all active rules"""
        rules = firewall_controller.get_active_rules()
        assert isinstance(rules, dict)

    @pytest.mark.asyncio
    async def test_get_active_rules_specific_chain(self, firewall_controller):
        """Test getting rules for specific chain"""
        rule = FirewallRule(action="ACCEPT", destination_port=443)
        await firewall_controller.apply_rule(rule, "OUTPUT")

        rules = firewall_controller.get_active_rules(chain="OUTPUT")

        assert "OUTPUT" in rules
        assert len(rules["OUTPUT"]) == 1


class TestNetworkSegmenter:
    """Test NetworkSegmenter"""

    def test_initialization(self, network_segmenter):
        """Test network segmenter initialization"""
        assert network_segmenter.active_segments == {}

    @pytest.mark.asyncio
    async def test_create_segment(self, network_segmenter):
        """Test creating network segment"""
        result = await network_segmenter.create_segment("DMZ", vlan_id=100)

        assert result is True
        assert "DMZ" in network_segmenter.active_segments
        assert network_segmenter.active_segments["DMZ"]["vlan_id"] == 100
        assert network_segmenter.active_segments["DMZ"]["isolated"] is True

    @pytest.mark.asyncio
    async def test_create_segment_without_vlan(self, network_segmenter):
        """Test creating segment without VLAN"""
        result = await network_segmenter.create_segment("APP")

        assert result is True
        assert "APP" in network_segmenter.active_segments
        assert network_segmenter.active_segments["APP"]["vlan_id"] is None

    @pytest.mark.asyncio
    async def test_remove_segment(self, network_segmenter):
        """Test removing network segment"""
        await network_segmenter.create_segment("DMZ", vlan_id=100)

        removed = await network_segmenter.remove_segment("DMZ")

        assert removed is True
        assert "DMZ" not in network_segmenter.active_segments

    @pytest.mark.asyncio
    async def test_remove_nonexistent_segment(self, network_segmenter):
        """Test removing segment that doesn't exist"""
        removed = await network_segmenter.remove_segment("NONEXISTENT")
        assert removed is True  # Should not error

    def test_get_active_segments(self, network_segmenter):
        """Test getting active segments"""
        segments = network_segmenter.get_active_segments()
        assert isinstance(segments, dict)
        assert len(segments) == 0


class TestZeroTrustAccessController:
    """Test ZeroTrustAccessController"""

    def test_initialization(self, zero_trust_controller):
        """Test zero-trust controller initialization"""
        assert zero_trust_controller.access_policies == {}

    @pytest.mark.asyncio
    async def test_enforce_policy(self, zero_trust_controller):
        """Test enforcing zero-trust policy"""
        policy = {"allow_all": False, "require_mfa": True}

        result = await zero_trust_controller.enforce_policy(
            "DMZ", TrustLevel.UNTRUSTED, policy
        )

        assert result is True
        assert "DMZ" in zero_trust_controller.access_policies
        assert zero_trust_controller.access_policies["DMZ"]["trust_level"] == TrustLevel.UNTRUSTED
        assert zero_trust_controller.access_policies["DMZ"]["policy"] == policy

    @pytest.mark.asyncio
    async def test_enforce_multiple_policies(self, zero_trust_controller):
        """Test enforcing policies on multiple zones"""
        await zero_trust_controller.enforce_policy(
            "DMZ", TrustLevel.UNTRUSTED, {"allow_all": False}
        )
        await zero_trust_controller.enforce_policy(
            "DATA", TrustLevel.RESTRICTED, {"encryption": "required"}
        )

        assert len(zero_trust_controller.access_policies) == 2

    @pytest.mark.asyncio
    async def test_revoke_access(self, zero_trust_controller):
        """Test revoking access to zone"""
        await zero_trust_controller.enforce_policy(
            "DMZ", TrustLevel.UNTRUSTED, {"allow_all": True}
        )

        revoked = await zero_trust_controller.revoke_access("DMZ")

        assert revoked is True
        assert zero_trust_controller.access_policies["DMZ"]["policy"]["allow_all"] is False

    @pytest.mark.asyncio
    async def test_revoke_access_nonexistent(self, zero_trust_controller):
        """Test revoking access to nonexistent zone"""
        revoked = await zero_trust_controller.revoke_access("NONEXISTENT")
        assert revoked is True  # Should not error

    def test_get_active_policies(self, zero_trust_controller):
        """Test getting active policies"""
        policies = zero_trust_controller.get_active_policies()
        assert isinstance(policies, dict)


class TestZoneIsolationEngine:
    """Test ZoneIsolationEngine main functionality"""

    def test_initialization(self, zone_isolation_engine):
        """Test zone isolation engine initialization"""
        assert zone_isolation_engine.firewall is not None
        assert zone_isolation_engine.network is not None
        assert zone_isolation_engine.zero_trust is not None
        assert zone_isolation_engine.active_isolations == {}
        assert zone_isolation_engine.metrics is not None

    def test_initialization_with_dependencies(self):
        """Test initialization with custom dependencies"""
        firewall = DynamicFirewallController()
        network = NetworkSegmenter()
        zero_trust = ZeroTrustAccessController()

        engine = ZoneIsolationEngine(
            firewall_controller=firewall,
            network_segmenter=network,
            zero_trust_controller=zero_trust,
        )

        assert engine.firewall == firewall
        assert engine.network == network
        assert engine.zero_trust == zero_trust

    @pytest.mark.asyncio
    async def test_isolate_single_zone(self, zone_isolation_engine):
        """Test isolating single zone"""
        result = await zone_isolation_engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        assert result.status == "SUCCESS"
        assert "DMZ" in result.zones_isolated
        # Firewall rules may be 0 if no block_ips in policy
        assert result.firewall_rules_applied >= 0
        assert result.network_policies_created > 0
        assert result.zero_trust_enforced is True

    @pytest.mark.asyncio
    async def test_isolate_multiple_zones(self, zone_isolation_engine):
        """Test isolating multiple zones"""
        result = await zone_isolation_engine.isolate(
            zones=["DMZ", "APP", "DATA"],
            isolation_level=IsolationLevel.FULL_ISOLATION,
        )

        assert result.status == "SUCCESS"
        assert len(result.zones_isolated) == 3
        assert "DMZ" in result.zones_isolated
        assert "APP" in result.zones_isolated
        assert "DATA" in result.zones_isolated

    @pytest.mark.asyncio
    async def test_isolate_with_monitoring_level(self, zone_isolation_engine):
        """Test isolation with MONITORING level"""
        result = await zone_isolation_engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.MONITORING,
        )

        assert result.status == "SUCCESS"
        assert result.firewall_rules_applied >= 1  # At least LOG rule

    @pytest.mark.asyncio
    async def test_isolate_with_rate_limiting(self, zone_isolation_engine):
        """Test isolation with RATE_LIMITING level"""
        result = await zone_isolation_engine.isolate(
            zones=["APP"],
            isolation_level=IsolationLevel.RATE_LIMITING,
        )

        assert result.status == "SUCCESS"

    @pytest.mark.asyncio
    async def test_isolate_with_custom_policy(self, zone_isolation_engine):
        """Test isolation with custom policy"""
        policy = {
            "block_ips": ["1.2.3.4", "5.6.7.8"],
            "allow_ports": [80, 443],
        }

        result = await zone_isolation_engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.BLOCKING,
            policy=policy,
        )

        assert result.status == "SUCCESS"
        assert result.firewall_rules_applied >= 2  # IP blocks

    @pytest.mark.asyncio
    async def test_isolate_tracks_active_isolations(self, zone_isolation_engine):
        """Test that isolations are tracked"""
        await zone_isolation_engine.isolate(
            zones=["DMZ", "APP"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        assert len(zone_isolation_engine.active_isolations) == 2
        assert "DMZ" in zone_isolation_engine.active_isolations
        assert "APP" in zone_isolation_engine.active_isolations

    @pytest.mark.asyncio
    async def test_remove_isolation(self, zone_isolation_engine):
        """Test removing isolation"""
        await zone_isolation_engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        removed = await zone_isolation_engine.remove_isolation(zones=["DMZ"])

        assert removed is True
        assert "DMZ" not in zone_isolation_engine.active_isolations

    @pytest.mark.asyncio
    async def test_remove_isolation_multiple(self, zone_isolation_engine):
        """Test removing isolation from multiple zones"""
        await zone_isolation_engine.isolate(
            zones=["DMZ", "APP"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        removed = await zone_isolation_engine.remove_isolation(zones=["DMZ", "APP"])

        assert removed is True
        assert len(zone_isolation_engine.active_isolations) == 0

    def test_get_isolated_zones(self, zone_isolation_engine):
        """Test getting list of isolated zones"""
        zones = zone_isolation_engine.get_isolated_zones()
        assert isinstance(zones, list)
        assert len(zones) == 0  # Initially empty

    @pytest.mark.asyncio
    async def test_get_isolated_zones_after_isolation(self, zone_isolation_engine):
        """Test getting isolated zones after isolation"""
        await zone_isolation_engine.isolate(
            zones=["DMZ", "APP"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        zones = zone_isolation_engine.get_isolated_zones()
        assert len(zones) == 2
        assert "DMZ" in zones

    def test_get_isolation_details(self, zone_isolation_engine):
        """Test getting isolation details for zone"""
        details = zone_isolation_engine.get_isolation_details("DMZ")
        assert details is None  # Not isolated yet

    @pytest.mark.asyncio
    async def test_get_isolation_details_after_isolation(self, zone_isolation_engine):
        """Test getting details after isolation"""
        await zone_isolation_engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        details = zone_isolation_engine.get_isolation_details("DMZ")
        assert details is not None
        assert details["level"] == IsolationLevel.BLOCKING

    def test_is_zone_isolated(self, zone_isolation_engine):
        """Test checking if zone is isolated"""
        assert zone_isolation_engine.is_zone_isolated("DMZ") is False

    @pytest.mark.asyncio
    async def test_is_zone_isolated_after_isolation(self, zone_isolation_engine):
        """Test checking isolation status after isolation"""
        await zone_isolation_engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        assert zone_isolation_engine.is_zone_isolated("DMZ") is True
        assert zone_isolation_engine.is_zone_isolated("APP") is False

    def test_determine_trust_level(self, zone_isolation_engine):
        """Test trust level determination"""
        assert zone_isolation_engine._determine_trust_level("DMZ") == TrustLevel.UNTRUSTED
        assert zone_isolation_engine._determine_trust_level("APPLICATION") == TrustLevel.LIMITED
        assert zone_isolation_engine._determine_trust_level("DATA") == TrustLevel.RESTRICTED
        assert zone_isolation_engine._determine_trust_level("MANAGEMENT") == TrustLevel.CRITICAL
        assert zone_isolation_engine._determine_trust_level("UNKNOWN") == TrustLevel.LIMITED

    def test_generate_firewall_rules_monitoring(self, zone_isolation_engine):
        """Test firewall rule generation for MONITORING level"""
        rules = zone_isolation_engine._generate_firewall_rules(
            "DMZ", IsolationLevel.MONITORING, {}
        )

        assert len(rules) > 0
        assert rules[0].action == "LOG"

    def test_generate_firewall_rules_blocking(self, zone_isolation_engine):
        """Test firewall rule generation for BLOCKING level"""
        policy = {"block_ips": ["1.2.3.4", "5.6.7.8"]}
        rules = zone_isolation_engine._generate_firewall_rules(
            "DMZ", IsolationLevel.BLOCKING, policy
        )

        assert len(rules) == 2
        assert all(r.action == "DROP" for r in rules)

    def test_generate_firewall_rules_full_isolation(self, zone_isolation_engine):
        """Test firewall rule generation for FULL_ISOLATION"""
        rules = zone_isolation_engine._generate_firewall_rules(
            "DMZ", IsolationLevel.FULL_ISOLATION, {}
        )

        assert len(rules) > 0
        assert rules[0].action == "DROP"
        assert rules[0].protocol == "all"


class TestZoneIsolationMetrics:
    """Test Prometheus metrics integration"""

    def test_metrics_initialization(self):
        """Test metrics are initialized"""
        metrics = ZoneIsolationMetrics()

        assert metrics.isolations_total is not None
        assert metrics.active_isolations is not None
        assert metrics.firewall_rules_total is not None
        assert metrics.isolation_duration is not None


class TestZoneIsolationErrorHandling:
    """Test error handling in zone isolation"""

    @pytest.mark.asyncio
    async def test_isolate_with_exception_in_zone(self, zone_isolation_engine):
        """Test isolation continues when one zone fails"""
        # Mock firewall to raise exception for specific zone
        original_apply = zone_isolation_engine.firewall.apply_rules_batch

        async def mock_apply_with_error(rules, chain="INPUT"):
            # Raise error to simulate failure
            raise Exception("Simulated firewall error")

        zone_isolation_engine.firewall.apply_rules_batch = mock_apply_with_error

        result = await zone_isolation_engine.isolate(
            zones=["DMZ", "APP"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        # Should have partial or failed status
        assert result.status in ["PARTIAL", "FAILED"]
        assert len(result.errors) > 0

        # Restore
        zone_isolation_engine.firewall.apply_rules_batch = original_apply

    @pytest.mark.asyncio
    async def test_isolate_exception_handling(self, zone_isolation_engine):
        """Test exception handling in isolate method"""
        # Mock network segmenter to raise exception
        async def mock_raise(*args, **kwargs):
            raise Exception("Simulated network error")

        zone_isolation_engine.network.create_segment = mock_raise

        result = await zone_isolation_engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        # Should return failed result
        assert result.status in ["FAILED", "PARTIAL"]

    @pytest.mark.asyncio
    async def test_remove_isolation_with_exception(self, zone_isolation_engine):
        """Test remove_isolation handles exceptions"""
        # Setup isolation
        await zone_isolation_engine.isolate(
            zones=["DMZ", "APP"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        # Mock to raise exception on first zone
        original_remove = zone_isolation_engine.network.remove_segment

        async def mock_remove_with_error(zone):
            if zone == "DMZ":
                raise Exception("Simulated removal error")
            return await original_remove(zone)

        zone_isolation_engine.network.remove_segment = mock_remove_with_error

        # Should handle gracefully
        removed = await zone_isolation_engine.remove_isolation(zones=["DMZ", "APP"])

        # May be False since one failed
        assert removed is False

        # Restore
        zone_isolation_engine.network.remove_segment = original_remove

    @pytest.mark.asyncio
    async def test_isolate_partial_success(self):
        """Test partial isolation when some zones fail"""
        # Create fresh engine to avoid prometheus conflicts
        from containment.zone_isolation import (
            DynamicFirewallController,
            NetworkSegmenter,
            ZeroTrustAccessController,
        )
        from unittest.mock import AsyncMock

        mock_network = NetworkSegmenter()
        # Patch create_segment to fail on specific zone
        original_create = mock_network.create_segment

        async def mock_create_with_fail(zone, vlan_id=None):
            if zone == "FAIL_ZONE":
                raise Exception("Simulated zone failure")
            return await original_create(zone, vlan_id)

        mock_network.create_segment = mock_create_with_fail

        engine = ZoneIsolationEngine(network_segmenter=mock_network)

        result = await engine.isolate(
            zones=["DMZ", "FAIL_ZONE"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        # Should have partial status (one succeeded, one failed)
        assert result.status == "PARTIAL"
        assert "DMZ" in result.zones_isolated
        assert "FAIL_ZONE" not in result.zones_isolated
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_isolate_catastrophic_failure(self):
        """Test complete failure in isolate (exception in main try block)"""
        from containment.zone_isolation import ZoneIsolationEngine

        engine = ZoneIsolationEngine()

        # Mock _determine_trust_level to raise exception early
        def mock_raise(*args, **kwargs):
            raise RuntimeError("Catastrophic system error")

        engine._determine_trust_level = mock_raise

        result = await engine.isolate(
            zones=["DMZ"],
            isolation_level=IsolationLevel.BLOCKING,
        )

        assert result.status == "FAILED"
        assert len(result.errors) > 0
        assert "Catastrophic" in str(result.errors[0])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
