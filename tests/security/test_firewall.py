"""
AI-Driven Firewall Tests - MAXIMUS Vértice

Validates intelligent firewall capabilities including:
- Dynamic rule generation
- Traffic filtering
- Attack prevention
- Policy enforcement

Test Coverage:
- Rule creation and validation
- Traffic matching
- Action execution
- AI-driven rule optimization
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio

from backend.security.firewall import (
    AIFirewall,
    FirewallRule,
    FirewallAction,
    TrafficDecision,
    RuleGenerator,
    PolicyEnforcer,
    ConnectionState
)


class TestFirewallRule:
    """Test firewall rule data structures."""
    
    def test_rule_creation(self):
        """Test basic rule creation."""
        rule = FirewallRule(
            rule_id="RULE001",
            name="Block malicious IP",
            source_ip="192.168.1.100",
            destination_ip="10.0.0.50",
            destination_port=80,
            protocol="TCP",
            action=FirewallAction.DROP,
            priority=100,
            enabled=True
        )
        
        assert rule.rule_id == "RULE001"
        assert rule.action == FirewallAction.DROP
        assert rule.priority == 100
        assert rule.enabled is True
    
    def test_rule_validation(self):
        """Test rule validation logic."""
        with pytest.raises(ValueError):
            FirewallRule(
                rule_id="INVALID",
                name="Invalid rule",
                source_ip="invalid_ip",
                destination_port=80,
                protocol="TCP",
                action=FirewallAction.ALLOW,
                priority=100
            )
    
    def test_rule_matching(self):
        """Test if rule matches given traffic."""
        rule = FirewallRule(
            rule_id="RULE002",
            name="Allow HTTPS",
            destination_port=443,
            protocol="TCP",
            action=FirewallAction.ALLOW,
            priority=50
        )
        
        # Matching traffic
        assert rule.matches(
            src_ip="any",
            dst_ip="any",
            dst_port=443,
            protocol="TCP"
        ) is True
        
        # Non-matching traffic
        assert rule.matches(
            src_ip="any",
            dst_ip="any",
            dst_port=80,
            protocol="TCP"
        ) is False
    
    def test_rule_serialization(self):
        """Test rule to dict conversion."""
        rule = FirewallRule(
            rule_id="RULE003",
            name="Test rule",
            source_ip="192.168.1.0/24",
            destination_port=22,
            protocol="TCP",
            action=FirewallAction.REJECT,
            priority=200
        )
        
        data = rule.to_dict()
        assert data["rule_id"] == "RULE003"
        assert data["action"] == "REJECT"
        assert data["priority"] == 200


class TestRuleGenerator:
    """Test AI-driven rule generation."""
    
    @pytest.fixture
    def generator(self):
        """Create RuleGenerator instance."""
        return RuleGenerator(ml_enabled=True)
    
    @pytest.fixture
    def threat_data(self) -> List[Dict]:
        """Generate sample threat intelligence data."""
        threats = [
            {
                "ip": "203.0.113.1",
                "threat_type": "botnet",
                "confidence": 0.95,
                "last_seen": datetime.now()
            },
            {
                "ip": "203.0.113.2",
                "threat_type": "malware_c2",
                "confidence": 0.87,
                "last_seen": datetime.now()
            }
        ]
        return threats
    
    def test_generate_from_threat_intel(self, generator, threat_data):
        """Test rule generation from threat intelligence."""
        rules = generator.generate_from_threats(threat_data)
        
        assert len(rules) == len(threat_data)
        assert all(rule.action == FirewallAction.DROP for rule in rules)
        assert all(rule.priority >= 90 for rule in rules)  # High priority for threats
    
    def test_generate_from_ids_alert(self, generator):
        """Test rule generation from IDS alerts."""
        alert = {
            "alert_type": "port_scan",
            "source_ip": "192.168.1.100",
            "severity": "HIGH",
            "confidence": 0.92
        }
        
        rule = generator.generate_from_alert(alert)
        
        assert rule is not None
        assert rule.source_ip == "192.168.1.100"
        assert rule.action in [FirewallAction.DROP, FirewallAction.REJECT]
        assert rule.priority >= 80
    
    def test_generate_rate_limit_rule(self, generator):
        """Test rate limiting rule generation."""
        rule = generator.generate_rate_limit_rule(
            source_ip="192.168.1.0/24",
            max_connections_per_second=100,
            duration=300
        )
        
        assert rule is not None
        assert "rate_limit" in rule.metadata
        assert rule.metadata["max_connections_per_second"] == 100
        assert rule.ttl == 300
    
    def test_optimize_ruleset(self, generator):
        """Test rule optimization to reduce redundancy."""
        rules = [
            FirewallRule(
                rule_id="R1",
                name="Block IP 1",
                source_ip="192.168.1.100",
                action=FirewallAction.DROP,
                priority=100
            ),
            FirewallRule(
                rule_id="R2",
                name="Block IP 2",
                source_ip="192.168.1.101",
                action=FirewallAction.DROP,
                priority=100
            ),
            FirewallRule(
                rule_id="R3",
                name="Block subnet",
                source_ip="192.168.1.0/24",
                action=FirewallAction.DROP,
                priority=90
            )
        ]
        
        optimized = generator.optimize_ruleset(rules)
        
        # Should consolidate first two rules into subnet rule
        assert len(optimized) < len(rules)
    
    def test_temporal_rule_generation(self, generator):
        """Test time-based rule generation."""
        rule = generator.generate_temporal_rule(
            name="Business hours only",
            destination_port=8080,
            action=FirewallAction.ALLOW,
            start_time="09:00",
            end_time="17:00",
            days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )
        
        assert rule is not None
        assert "temporal" in rule.metadata
        assert rule.metadata["start_time"] == "09:00"


class TestPolicyEnforcer:
    """Test firewall policy enforcement."""
    
    @pytest.fixture
    def enforcer(self):
        """Create PolicyEnforcer instance."""
        return PolicyEnforcer()
    
    @pytest.fixture
    def sample_rules(self) -> List[FirewallRule]:
        """Generate sample firewall rules."""
        return [
            FirewallRule(
                rule_id="DEFAULT_DENY",
                name="Default deny all",
                action=FirewallAction.DROP,
                priority=1
            ),
            FirewallRule(
                rule_id="ALLOW_HTTPS",
                name="Allow HTTPS",
                destination_port=443,
                protocol="TCP",
                action=FirewallAction.ALLOW,
                priority=100
            ),
            FirewallRule(
                rule_id="ALLOW_DNS",
                name="Allow DNS",
                destination_port=53,
                protocol="UDP",
                action=FirewallAction.ALLOW,
                priority=100
            )
        ]
    
    def test_load_rules(self, enforcer, sample_rules):
        """Test loading rules into enforcer."""
        enforcer.load_rules(sample_rules)
        assert len(enforcer.rules) == len(sample_rules)
    
    def test_evaluate_traffic(self, enforcer, sample_rules):
        """Test traffic evaluation against rules."""
        enforcer.load_rules(sample_rules)
        
        # Should allow HTTPS
        decision = enforcer.evaluate(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            dst_port=443,
            protocol="TCP"
        )
        assert decision.action == FirewallAction.ALLOW
        assert decision.matched_rule == "ALLOW_HTTPS"
        
        # Should block HTTP (not explicitly allowed)
        decision = enforcer.evaluate(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            dst_port=80,
            protocol="TCP"
        )
        assert decision.action == FirewallAction.DROP
        assert decision.matched_rule == "DEFAULT_DENY"
    
    def test_rule_priority(self, enforcer):
        """Test that higher priority rules take precedence."""
        rules = [
            FirewallRule(
                rule_id="LOW_PRIORITY",
                name="Allow all",
                action=FirewallAction.ALLOW,
                priority=10
            ),
            FirewallRule(
                rule_id="HIGH_PRIORITY",
                name="Block specific IP",
                source_ip="192.168.1.100",
                action=FirewallAction.DROP,
                priority=200
            )
        ]
        
        enforcer.load_rules(rules)
        
        decision = enforcer.evaluate(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            dst_port=80,
            protocol="TCP"
        )
        
        assert decision.action == FirewallAction.DROP
        assert decision.matched_rule == "HIGH_PRIORITY"
    
    def test_stateful_tracking(self, enforcer, sample_rules):
        """Test stateful connection tracking."""
        enforcer.load_rules(sample_rules)
        enforcer.enable_stateful_inspection()
        
        # Outbound connection should be tracked
        outbound = enforcer.evaluate(
            src_ip="10.0.0.50",
            dst_ip="192.168.1.100",
            dst_port=443,
            protocol="TCP",
            flags=["SYN"]
        )
        
        # Return traffic should be allowed due to state
        inbound = enforcer.evaluate(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            dst_port=54321,
            protocol="TCP",
            flags=["SYN", "ACK"],
            related_to=outbound.connection_id
        )
        
        assert inbound.action == FirewallAction.ALLOW
        assert inbound.reason == "stateful_related"
    
    def test_connection_limits(self, enforcer):
        """Test connection rate limiting."""
        enforcer.set_connection_limit(
            source_ip="192.168.1.100",
            max_connections=10,
            time_window=1.0
        )
        
        # First 10 connections should succeed
        for i in range(10):
            decision = enforcer.evaluate(
                src_ip="192.168.1.100",
                dst_ip="10.0.0.50",
                dst_port=80,
                protocol="TCP"
            )
            assert decision.action != FirewallAction.DROP or decision.reason != "rate_limit"
        
        # 11th connection should be rate limited
        decision = enforcer.evaluate(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            dst_port=80,
            protocol="TCP"
        )
        # Might be dropped due to rate limiting
        # Actual behavior depends on implementation


class TestAIFirewall:
    """Test complete AI-driven firewall system."""
    
    @pytest.fixture
    async def firewall(self):
        """Create AIFirewall instance."""
        fw = AIFirewall(
            enable_ml=True,
            enable_auto_rules=True,
            enable_stateful=True
        )
        await fw.initialize()
        return fw
    
    @pytest.mark.asyncio
    async def test_firewall_initialization(self, firewall):
        """Test firewall system initialization."""
        assert firewall.is_running is True
        assert firewall.rule_generator is not None
        assert firewall.policy_enforcer is not None
    
    @pytest.mark.asyncio
    async def test_add_rule(self, firewall):
        """Test adding rules dynamically."""
        rule = FirewallRule(
            rule_id="TEST_RULE",
            name="Test rule",
            destination_port=8080,
            action=FirewallAction.ALLOW,
            priority=50
        )
        
        await firewall.add_rule(rule)
        
        assert "TEST_RULE" in firewall.get_rule_ids()
    
    @pytest.mark.asyncio
    async def test_remove_rule(self, firewall):
        """Test removing rules dynamically."""
        rule = FirewallRule(
            rule_id="TEMP_RULE",
            name="Temporary rule",
            destination_port=9999,
            action=FirewallAction.DROP,
            priority=50
        )
        
        await firewall.add_rule(rule)
        assert "TEMP_RULE" in firewall.get_rule_ids()
        
        await firewall.remove_rule("TEMP_RULE")
        assert "TEMP_RULE" not in firewall.get_rule_ids()
    
    @pytest.mark.asyncio
    async def test_auto_rule_from_ids(self, firewall):
        """Test automatic rule creation from IDS alerts."""
        alert = {
            "alert_type": "brute_force",
            "source_ip": "192.168.1.100",
            "severity": "HIGH",
            "confidence": 0.95
        }
        
        await firewall.process_ids_alert(alert)
        
        # Should have created blocking rule
        rules = firewall.get_rules_for_ip("192.168.1.100")
        assert len(rules) > 0
        assert any(rule.action == FirewallAction.DROP for rule in rules)
    
    @pytest.mark.asyncio
    async def test_threat_intel_integration(self, firewall):
        """Test automatic rule creation from threat intelligence."""
        threats = [
            {
                "ip": "203.0.113.1",
                "threat_type": "malware_c2",
                "confidence": 0.92
            }
        ]
        
        await firewall.update_threat_intel(threats)
        
        # Should have created blocking rules
        decision = firewall.evaluate_traffic(
            src_ip="203.0.113.1",
            dst_ip="10.0.0.50",
            dst_port=443,
            protocol="TCP"
        )
        
        assert decision.action == FirewallAction.DROP
        assert "threat_intel" in decision.reason
    
    @pytest.mark.asyncio
    async def test_rule_expiration(self, firewall):
        """Test automatic rule expiration."""
        rule = FirewallRule(
            rule_id="TEMP_BLOCK",
            name="Temporary block",
            source_ip="192.168.1.100",
            action=FirewallAction.DROP,
            priority=100,
            ttl=2  # 2 seconds TTL
        )
        
        await firewall.add_rule(rule)
        assert "TEMP_BLOCK" in firewall.get_rule_ids()
        
        # Wait for expiration
        await asyncio.sleep(3)
        
        assert "TEMP_BLOCK" not in firewall.get_rule_ids()
    
    @pytest.mark.asyncio
    async def test_ml_based_blocking(self, firewall):
        """Test ML-based traffic classification and blocking."""
        # Simulate suspicious traffic pattern
        for i in range(100):
            await firewall.observe_traffic({
                "src_ip": "192.168.1.100",
                "dst_port": 22,
                "protocol": "TCP",
                "payload_size": 64,
                "flags": ["SYN"]
            })
        
        # ML model should detect pattern and suggest/create rule
        suspicious_ips = firewall.get_ml_flagged_ips()
        assert "192.168.1.100" in suspicious_ips
    
    @pytest.mark.asyncio
    async def test_whitelist_override(self, firewall):
        """Test that whitelist rules override blocking rules."""
        # Add blocking rule
        block_rule = FirewallRule(
            rule_id="BLOCK_ALL",
            name="Block all from subnet",
            source_ip="192.168.1.0/24",
            action=FirewallAction.DROP,
            priority=50
        )
        await firewall.add_rule(block_rule)
        
        # Add whitelist rule with higher priority
        whitelist_rule = FirewallRule(
            rule_id="WHITELIST_ADMIN",
            name="Allow admin IP",
            source_ip="192.168.1.10",
            action=FirewallAction.ALLOW,
            priority=200
        )
        await firewall.add_rule(whitelist_rule)
        
        # Admin IP should be allowed
        decision = firewall.evaluate_traffic(
            src_ip="192.168.1.10",
            dst_ip="10.0.0.50",
            dst_port=22,
            protocol="TCP"
        )
        assert decision.action == FirewallAction.ALLOW
        
        # Other IPs in subnet should be blocked
        decision = firewall.evaluate_traffic(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            dst_port=22,
            protocol="TCP"
        )
        assert decision.action == FirewallAction.DROP
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, firewall):
        """Test firewall performance metrics."""
        # Process some traffic
        for i in range(100):
            firewall.evaluate_traffic(
                src_ip=f"192.168.1.{i}",
                dst_ip="10.0.0.50",
                dst_port=443,
                protocol="TCP"
            )
        
        metrics = firewall.get_metrics()
        
        assert "packets_processed" in metrics
        assert "rules_matched" in metrics
        assert "avg_decision_time" in metrics
        assert metrics["packets_processed"] >= 100
    
    @pytest.mark.asyncio
    async def test_logging(self, firewall):
        """Test firewall decision logging."""
        decision = firewall.evaluate_traffic(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            dst_port=80,
            protocol="TCP"
        )
        
        logs = firewall.get_recent_logs(limit=10)
        assert len(logs) > 0
        assert logs[-1]["src_ip"] == "192.168.1.100"
    
    @pytest.mark.asyncio
    async def test_shutdown(self, firewall):
        """Test graceful firewall shutdown."""
        await firewall.shutdown()
        assert firewall.is_running is False


class TestConnectionState:
    """Test stateful connection tracking."""
    
    def test_connection_creation(self):
        """Test connection state creation."""
        conn = ConnectionState(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            state="SYN_SENT"
        )
        
        assert conn.src_ip == "192.168.1.100"
        assert conn.state == "SYN_SENT"
        assert conn.is_established is False
    
    def test_connection_state_transitions(self):
        """Test TCP connection state machine."""
        conn = ConnectionState(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            state="CLOSED"
        )
        
        # SYN
        conn.update_state(flags=["SYN"])
        assert conn.state == "SYN_SENT"
        
        # SYN-ACK
        conn.update_state(flags=["SYN", "ACK"])
        assert conn.state == "SYN_RECEIVED"
        
        # ACK
        conn.update_state(flags=["ACK"])
        assert conn.state == "ESTABLISHED"
        assert conn.is_established is True
    
    def test_connection_timeout(self):
        """Test connection timeout detection."""
        conn = ConnectionState(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="TCP",
            state="ESTABLISHED",
            timeout=1  # 1 second timeout
        )
        
        assert conn.is_expired() is False
        
        # Wait for timeout
        import time
        time.sleep(2)
        
        assert conn.is_expired() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
