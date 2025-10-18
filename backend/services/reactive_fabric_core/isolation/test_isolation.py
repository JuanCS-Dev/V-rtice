"""
Tests for Network Isolation Components
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from .data_diode import DataDiode, DiodeDirection
from .firewall import NetworkFirewall, FirewallRule, FirewallAction, Protocol
from .network_segmentation import NetworkSegmentation, DockerNetwork
from .kill_switch import KillSwitch, EmergencyShutdown, ShutdownLevel, ComponentType, KillTarget


class TestDataDiode:
    """Test Data Diode implementation"""

    def test_initialization(self):
        """Test data diode initialization"""
        diode = DataDiode(
            direction=DiodeDirection.L2_TO_L1,
            buffer_size=100,
            transmission_rate_limit=10
        )

        assert diode.direction == DiodeDirection.L2_TO_L1
        assert diode.buffer_size == 100
        assert diode.rate_limit == 10
        assert diode.integrity_check is True

    def test_start_stop(self):
        """Test starting and stopping the diode"""
        diode = DataDiode()

        # Start
        diode.start()
        assert diode._running is True

        # Stop
        diode.stop()
        assert diode._running is False

    def test_validate_direction_allowed(self):
        """Test validation of allowed transmission direction"""
        diode = DataDiode(direction=DiodeDirection.L2_TO_L1)

        # Allowed: L2 -> L1
        assert diode._validate_direction("layer2_dmz", "layer1_prod") is True

        # Blocked: L1 -> L2
        assert diode._validate_direction("layer1_prod", "layer2_dmz") is False

    def test_validate_direction_blocked(self):
        """Test blocking of invalid directions"""
        diode = DataDiode(direction=DiodeDirection.L2_TO_L1)

        # All these should be blocked
        assert diode._validate_direction("L1", "L3") is False
        assert diode._validate_direction("L2", "L3") is False
        assert diode._validate_direction("L3", "L1") is False

    def test_transmit_valid(self):
        """Test transmitting data in valid direction"""
        diode = DataDiode(direction=DiodeDirection.L2_TO_L1)
        diode.start()

        data = {"threat": "detected", "confidence": 0.95}
        result = diode.transmit(data, "layer2", "layer1")

        assert result is True
        stats = diode.get_stats()
        assert stats["buffer_usage"] > 0

        diode.stop()

    def test_transmit_blocked(self):
        """Test blocking transmission in invalid direction"""
        diode = DataDiode(direction=DiodeDirection.L2_TO_L1)
        diode.start()

        data = {"malicious": "payload"}
        result = diode.transmit(data, "layer1", "layer2")  # Wrong direction

        assert result is False
        stats = diode.get_stats()
        assert stats["violations_blocked"] == 1

        diode.stop()

    def test_packet_integrity(self):
        """Test packet integrity verification"""
        diode = DataDiode(enable_integrity_check=True)

        packet = diode._create_packet(
            {"test": "data"},
            "layer2",
            "layer1"
        )

        # Valid packet
        assert diode._verify_packet_integrity(packet) is True

        # Tampered packet
        packet.payload["tampered"] = True
        assert diode._verify_packet_integrity(packet) is False

    def test_emergency_flush(self):
        """Test emergency flush of buffer"""
        diode = DataDiode(buffer_size=10)
        diode.start()

        # Fill buffer
        for i in range(5):
            diode.transmit({"data": i}, "layer2", "layer1")

        # Flush
        flushed = diode.emergency_flush()
        assert flushed == 5

        stats = diode.get_stats()
        assert stats["buffer_usage"] == 0

        diode.stop()


class TestNetworkFirewall:
    """Test Network Firewall implementation"""

    def test_initialization(self):
        """Test firewall initialization"""
        firewall = NetworkFirewall(
            enable_dpi=True,
            default_action=FirewallAction.DENY
        )

        assert firewall.enable_dpi is True
        assert firewall.default_action == FirewallAction.DENY
        assert len(firewall._rules) == 0

    def test_add_rule(self):
        """Test adding firewall rules"""
        firewall = NetworkFirewall()

        rule = FirewallRule(
            id="test_rule",
            name="Test Rule",
            source_ip="10.0.0.0/24",
            destination_ip="192.168.0.0/24",
            action=FirewallAction.ALLOW,
            priority=100
        )

        result = firewall.add_rule(rule)
        assert result is True
        assert "test_rule" in firewall._rules

    def test_remove_rule(self):
        """Test removing firewall rules"""
        firewall = NetworkFirewall()

        rule = FirewallRule(
            id="test_rule",
            name="Test",
            source_ip="0.0.0.0/0",
            destination_ip="0.0.0.0/0"
        )

        firewall.add_rule(rule)
        result = firewall.remove_rule("test_rule")

        assert result is True
        assert "test_rule" not in firewall._rules

    def test_initialize_default_rules(self):
        """Test initialization of default isolation rules"""
        firewall = NetworkFirewall()
        firewall.initialize_default_rules()

        # Should have rules for layer isolation
        assert len(firewall._rules) > 0

        # Check key isolation rules exist
        assert "l1_outbound_deny" in firewall._rules
        assert "l2_to_l1_allow" in firewall._rules
        assert "l2_to_l3_deny" in firewall._rules

    def test_process_packet_allowed(self):
        """Test processing allowed packet"""
        firewall = NetworkFirewall(default_action=FirewallAction.DENY)

        # Add allow rule
        rule = FirewallRule(
            id="allow_http",
            name="Allow HTTP",
            source_ip="10.0.0.0/8",
            destination_ip="192.168.1.0/24",
            destination_port="80",
            protocol=Protocol.TCP,
            action=FirewallAction.ALLOW,
            priority=100
        )
        firewall.add_rule(rule)

        # Test packet
        packet = {
            "source_ip": "10.0.0.5",
            "destination_ip": "192.168.1.100",
            "destination_port": 80,
            "protocol": "tcp"
        }

        action, rule_id = firewall.process_packet(packet)
        assert action == FirewallAction.ALLOW
        assert rule_id == "allow_http"

    def test_process_packet_denied(self):
        """Test processing denied packet"""
        firewall = NetworkFirewall(default_action=FirewallAction.DENY)

        packet = {
            "source_ip": "10.0.0.5",
            "destination_ip": "192.168.1.100",
            "destination_port": 22,
            "protocol": "tcp"
        }

        action, rule_id = firewall.process_packet(packet)
        assert action == FirewallAction.DENY
        assert rule_id is None

    @pytest.mark.asyncio
    async def test_dpi_threat_detection(self):
        """Test deep packet inspection threat detection"""
        firewall = NetworkFirewall(enable_dpi=True)

        # SQL injection attempt
        packet = {
            "source_ip": "10.0.0.5",
            "destination_ip": "192.168.1.100",
            "payload": "SELECT * FROM users WHERE id=1 OR 1=1"
        }

        action, rule_id = firewall.process_packet(packet)
        assert action == FirewallAction.DENY
        assert "dpi_sql_injection" in rule_id

    @pytest.mark.asyncio
    async def test_ip_blocking(self):
        """Test IP blocking functionality"""
        firewall = NetworkFirewall()

        # Block an IP
        firewall._block_ip("10.0.0.5", duration_minutes=1)

        # Try packet from blocked IP
        packet = {
            "source_ip": "10.0.0.5",
            "destination_ip": "192.168.1.100"
        }

        action, rule_id = firewall.process_packet(packet)
        assert action == FirewallAction.DENY
        assert rule_id == "ip_blocked"


class TestNetworkSegmentation:
    """Test Network Segmentation implementation"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test network segmentation initialization"""
        segmentation = NetworkSegmentation()
        assert segmentation._initialized is False

    @patch('subprocess.run')
    @pytest.mark.asyncio
    async def test_create_layer_networks(self, mock_run):
        """Test creation of layer networks"""
        # Mock subprocess to simulate Docker
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="network created"
        )

        segmentation = NetworkSegmentation()
        await segmentation._create_layer_networks()

        # Should have created 4 networks
        assert len(segmentation.networks) == 4
        assert "reactive_fabric_layer1" in segmentation.networks
        assert "reactive_fabric_layer2" in segmentation.networks
        assert "reactive_fabric_layer3" in segmentation.networks
        assert "reactive_fabric_diode" in segmentation.networks

    def test_get_network_info(self):
        """Test getting network info for a layer"""
        segmentation = NetworkSegmentation()

        # Add test network
        segmentation.networks["reactive_fabric_layer1"] = DockerNetwork(
            name="reactive_fabric_layer1",
            subnet="10.1.0.0/16",
            gateway="10.1.0.1"
        )

        info = segmentation.get_network_info(1)
        assert info is not None
        assert info.subnet == "10.1.0.0/16"

    @patch('subprocess.run')
    @pytest.mark.asyncio
    async def test_connect_container(self, mock_run):
        """Test connecting container to network"""
        mock_run.return_value = MagicMock(returncode=0)

        segmentation = NetworkSegmentation()
        segmentation.networks["reactive_fabric_layer2"] = DockerNetwork(
            name="reactive_fabric_layer2"
        )

        await segmentation.connect_container("container123", layer=2)
        assert "container123" in segmentation.containers
        assert segmentation.containers["container123"] == "reactive_fabric_layer2"


class TestKillSwitch:
    """Test Kill Switch implementation"""

    def test_initialization(self):
        """Test kill switch initialization"""
        kill_switch = KillSwitch(require_confirmation=True)

        assert kill_switch.require_confirmation is True
        assert kill_switch._armed is False
        assert len(kill_switch._targets) == 0

    def test_arm_with_valid_code(self):
        """Test arming kill switch with valid code"""
        kill_switch = KillSwitch()

        with patch.dict('os.environ', {'KILL_SWITCH_AUTH_CODE': 'TEST123'}):
            result = kill_switch.arm('TEST123')
            assert result is True
            assert kill_switch._armed is True

    def test_arm_with_invalid_code(self):
        """Test arming kill switch with invalid code"""
        kill_switch = KillSwitch()

        with patch.dict('os.environ', {'KILL_SWITCH_AUTH_CODE': 'TEST123'}):
            result = kill_switch.arm('WRONG')
            assert result is False
            assert kill_switch._armed is False

    def test_register_target(self):
        """Test registering kill targets"""
        kill_switch = KillSwitch()

        target = KillTarget(
            id="container_123",
            name="honeypot_ssh",
            component_type=ComponentType.CONTAINER,
            layer=3
        )

        kill_switch.register_target(target)
        assert "container_123" in kill_switch._targets

    @patch('subprocess.run')
    def test_graceful_shutdown(self, mock_run):
        """Test graceful shutdown"""
        mock_run.return_value = MagicMock(returncode=0)

        kill_switch = KillSwitch()
        kill_switch.arm("VERTICE-EMERGENCY-2025")

        # Register targets
        target = KillTarget(
            id="container_123",
            name="test_container",
            component_type=ComponentType.CONTAINER,
            layer=3
        )
        kill_switch.register_target(target)

        # Activate graceful shutdown
        event = kill_switch.activate(
            level=ShutdownLevel.GRACEFUL,
            reason="Test",
            initiated_by="TEST"
        )

        assert event.success is True
        assert len(event.targets_killed) > 0

    @patch('subprocess.Popen')
    def test_emergency_shutdown(self, mock_popen):
        """Test emergency shutdown"""
        mock_process = MagicMock()
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        kill_switch = KillSwitch()
        kill_switch.arm("VERTICE-EMERGENCY-2025")

        # Register multiple targets
        for i in range(3):
            target = KillTarget(
                id=f"container_{i}",
                name=f"target_{i}",
                component_type=ComponentType.CONTAINER,
                layer=3
            )
            kill_switch.register_target(target)

        # Emergency shutdown
        event = kill_switch.activate(
            level=ShutdownLevel.EMERGENCY,
            reason="Breach detected",
            initiated_by="BREACH_DETECTOR"
        )

        assert len(event.targets_killed) == 3

    @pytest.mark.asyncio
    async def test_deadmans_switch(self):
        """Test dead man's switch"""
        kill_switch = KillSwitch()
        kill_switch.arm("VERTICE-EMERGENCY-2025")

        # Start with short timeout
        await kill_switch.start_deadmans_switch(timeout_seconds=1)
        assert kill_switch._deadmans_active is True

        # Heartbeat resets timer
        kill_switch.heartbeat()
        await asyncio.sleep(0.5)

        # Another heartbeat
        kill_switch.heartbeat()
        await asyncio.sleep(0.5)

        # Stop before timeout
        await kill_switch.stop_deadmans_switch()
        assert kill_switch._deadmans_active is False


class TestEmergencyShutdown:
    """Test Emergency Shutdown Coordinator"""

    def test_initialization(self):
        """Test emergency shutdown initialization"""
        shutdown = EmergencyShutdown()

        # Should have kill switch for each layer
        assert len(shutdown.kill_switches) == 3
        assert 1 in shutdown.kill_switches
        assert 2 in shutdown.kill_switches
        assert 3 in shutdown.kill_switches

    @patch.object(KillSwitch, 'activate')
    def test_containment_breach_layer3(self, mock_activate):
        """Test containment breach in Layer 3"""
        shutdown = EmergencyShutdown()

        # Arm all switches
        for switch in shutdown.kill_switches.values():
            switch._armed = True

        # L3 breach
        shutdown.containment_breach(source_layer=3)

        # Should kill only L3
        mock_activate.assert_called_once()

    @patch.object(KillSwitch, 'activate')
    def test_containment_breach_layer2(self, mock_activate):
        """Test containment breach in Layer 2"""
        shutdown = EmergencyShutdown()

        # Arm all switches
        for switch in shutdown.kill_switches.values():
            switch._armed = True

        # L2 breach
        shutdown.containment_breach(source_layer=2)

        # Should kill L2 and L3
        assert mock_activate.call_count == 2

    @patch.object(KillSwitch, 'activate')
    def test_containment_breach_layer1(self, mock_activate):
        """Test catastrophic breach in Layer 1"""
        shutdown = EmergencyShutdown()

        # Arm all switches
        for switch in shutdown.kill_switches.values():
            switch._armed = True

        # L1 breach - CATASTROPHIC
        shutdown.containment_breach(source_layer=1)

        # Should trigger nuclear option on all layers
        assert mock_activate.call_count == 3

        # Verify nuclear level was used
        for call in mock_activate.call_args_list:
            assert call[1]['level'] == ShutdownLevel.NUCLEAR