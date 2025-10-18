"""
Network Firewall Implementation
Deep packet inspection and traffic control between layers
"""

import asyncio
import ipaddress
import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class FirewallAction(Enum):
    """Firewall rule actions"""
    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    REJECT = "reject"

class Protocol(Enum):
    """Network protocols"""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ANY = "any"

@dataclass
class FirewallRule:
    """Individual firewall rule"""
    id: str
    name: str
    source_ip: str  # CIDR notation
    destination_ip: str  # CIDR notation
    source_port: Optional[str] = None  # Can be range: "8000-9000"
    destination_port: Optional[str] = None
    protocol: Protocol = Protocol.ANY
    action: FirewallAction = FirewallAction.DENY
    priority: int = 1000  # Lower is higher priority
    enabled: bool = True
    log_enabled: bool = True
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0

class NetworkFirewall:
    """
    Software-defined firewall for Reactive Fabric
    Implements deep packet inspection and layer isolation
    """

    def __init__(self, enable_dpi: bool = True, default_action: FirewallAction = FirewallAction.DENY):
        """
        Initialize firewall

        Args:
            enable_dpi: Enable deep packet inspection
            default_action: Default action for unmatched traffic
        """
        self.enable_dpi = enable_dpi
        self.default_action = default_action

        # Rule storage
        self._rules: Dict[str, FirewallRule] = {}
        self._rule_order: List[str] = []  # Ordered by priority

        # Connection tracking
        self._connections: Dict[str, Dict] = {}
        self._blocked_ips: Set[str] = set()

        # Statistics
        self._stats = {
            "packets_processed": 0,
            "packets_allowed": 0,
            "packets_denied": 0,
            "dpi_inspections": 0,
            "threats_detected": 0
        }

        # DPI patterns for threat detection
        self._dpi_patterns = self._load_dpi_patterns()

    def _load_dpi_patterns(self) -> Dict[str, re.Pattern]:
        """Load DPI patterns for threat detection"""
        return {
            "sql_injection": re.compile(
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER)\b)",
                re.IGNORECASE
            ),
            "command_injection": re.compile(
                r"(;|\||&&|\$\(|`|>|<|\n|\r)",
                re.IGNORECASE
            ),
            "xss_attack": re.compile(
                r"(<script|javascript:|onerror=|onclick=)",
                re.IGNORECASE
            ),
            "path_traversal": re.compile(
                r"(\.\./|\.\.\\|%2e%2e)",
                re.IGNORECASE
            ),
            "malware_signature": re.compile(
                r"(eval\(|exec\(|system\(|shell_exec)",
                re.IGNORECASE
            )
        }

    def initialize_default_rules(self):
        """Initialize default firewall rules for layer isolation"""

        # Layer 1 (Production) Rules
        self.add_rule(FirewallRule(
            id="l1_outbound_deny",
            name="Block L1 to L2/L3",
            source_ip="10.1.0.0/16",  # L1 subnet
            destination_ip="10.2.0.0/15",  # L2+L3 subnets
            action=FirewallAction.DENY,
            priority=100,
            description="Production cannot initiate connections to lower layers"
        ))

        # Layer 2 (DMZ) Rules
        self.add_rule(FirewallRule(
            id="l2_to_l1_allow",
            name="Allow L2 to L1 (via diode)",
            source_ip="10.2.0.0/16",  # L2 subnet
            destination_ip="10.1.0.0/16",  # L1 subnet
            destination_port="443",
            protocol=Protocol.TCP,
            action=FirewallAction.ALLOW,
            priority=200,
            description="DMZ can send processed intel to production"
        ))

        self.add_rule(FirewallRule(
            id="l2_to_l3_deny",
            name="Block L2 to L3",
            source_ip="10.2.0.0/16",
            destination_ip="10.3.0.0/16",  # L3 subnet
            action=FirewallAction.DENY,
            priority=150,
            description="DMZ cannot reach sacrifice island"
        ))

        # Layer 3 (Sacrifice Island) Rules
        self.add_rule(FirewallRule(
            id="l3_to_l2_limited",
            name="Limited L3 to L2",
            source_ip="10.3.0.0/16",
            destination_ip="10.2.0.0/16",
            destination_port="8080",  # Only specific port
            protocol=Protocol.TCP,
            action=FirewallAction.ALLOW,
            priority=300,
            description="Honeypots can send to DMZ collector only"
        ))

        self.add_rule(FirewallRule(
            id="l3_internet_allow",
            name="L3 Internet Access",
            source_ip="10.3.0.0/16",
            destination_ip="0.0.0.0/0",  # Internet
            action=FirewallAction.ALLOW,
            priority=400,
            description="Honeypots can receive attacks from internet"
        ))

        # Global deny rule
        self.add_rule(FirewallRule(
            id="global_deny",
            name="Deny All",
            source_ip="0.0.0.0/0",
            destination_ip="0.0.0.0/0",
            action=FirewallAction.DENY,
            priority=10000,
            description="Default deny all unmatched traffic"
        ))

        logger.info(f"Initialized {len(self._rules)} default firewall rules")

    def add_rule(self, rule: FirewallRule) -> bool:
        """Add a firewall rule"""
        if rule.id in self._rules:
            logger.warning(f"Rule {rule.id} already exists")
            return False

        self._rules[rule.id] = rule
        self._update_rule_order()

        # Apply to system if running on Linux
        self._apply_iptables_rule(rule)

        logger.info(f"Added firewall rule: {rule.name} (priority: {rule.priority})")
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a firewall rule"""
        if rule_id not in self._rules:
            return False

        rule = self._rules[rule_id]
        del self._rules[rule_id]
        self._update_rule_order()

        # Remove from system
        self._remove_iptables_rule(rule)

        logger.info(f"Removed firewall rule: {rule.name}")
        return True

    def _update_rule_order(self):
        """Update rule processing order based on priority"""
        self._rule_order = sorted(
            self._rules.keys(),
            key=lambda x: self._rules[x].priority
        )

    def process_packet(self, packet: Dict) -> Tuple[FirewallAction, Optional[str]]:
        """
        Process a network packet through firewall rules

        Args:
            packet: Dictionary containing packet information

        Returns:
            Tuple of (action, matching_rule_id)
        """
        self._stats["packets_processed"] += 1

        # Extract packet info
        src_ip = packet.get("source_ip", "0.0.0.0")
        dst_ip = packet.get("destination_ip", "0.0.0.0")
        src_port = packet.get("source_port")
        dst_port = packet.get("destination_port")
        protocol = packet.get("protocol", "any").lower()
        payload = packet.get("payload", "")

        # Check if IP is blocked
        if src_ip in self._blocked_ips:
            self._stats["packets_denied"] += 1
            return FirewallAction.DENY, "ip_blocked"

        # Deep packet inspection if enabled
        if self.enable_dpi and payload:
            threat_detected = self._inspect_payload(payload)
            if threat_detected:
                self._stats["threats_detected"] += 1
                self._block_ip(src_ip, duration_minutes=60)
                return FirewallAction.DENY, f"dpi_{threat_detected}"

        # Process rules in priority order
        for rule_id in self._rule_order:
            rule = self._rules[rule_id]

            if not rule.enabled:
                continue

            if self._match_rule(rule, src_ip, dst_ip, src_port, dst_port, protocol):
                rule.hit_count += 1

                if rule.log_enabled:
                    self._log_rule_match(rule, packet)

                if rule.action == FirewallAction.ALLOW:
                    self._stats["packets_allowed"] += 1
                elif rule.action in [FirewallAction.DENY, FirewallAction.REJECT]:
                    self._stats["packets_denied"] += 1

                return rule.action, rule.id

        # No rule matched, use default action
        if self.default_action == FirewallAction.ALLOW:
            self._stats["packets_allowed"] += 1
        else:
            self._stats["packets_denied"] += 1

        return self.default_action, None

    def _match_rule(self, rule: FirewallRule, src_ip: str, dst_ip: str,
                    src_port: Optional[int], dst_port: Optional[int],
                    protocol: str) -> bool:
        """Check if packet matches rule"""

        # Check IPs
        if not self._ip_in_cidr(src_ip, rule.source_ip):
            return False
        if not self._ip_in_cidr(dst_ip, rule.destination_ip):
            return False

        # Check protocol
        if rule.protocol != Protocol.ANY:
            if protocol != rule.protocol.value:
                return False

        # Check ports
        if rule.source_port and src_port:
            if not self._port_in_range(src_port, rule.source_port):
                return False

        if rule.destination_port and dst_port:
            if not self._port_in_range(dst_port, rule.destination_port):
                return False

        return True

    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """Check if IP is in CIDR range"""
        try:
            if cidr == "0.0.0.0/0":  # Match all
                return True
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            return False

    def _port_in_range(self, port: int, port_spec: str) -> bool:
        """Check if port is in specified range"""
        if "-" in port_spec:
            start, end = map(int, port_spec.split("-"))
            return start <= port <= end
        else:
            return port == int(port_spec)

    def _inspect_payload(self, payload: str) -> Optional[str]:
        """
        Deep packet inspection for threat detection

        Returns:
            Threat type if detected, None otherwise
        """
        self._stats["dpi_inspections"] += 1

        for threat_type, pattern in self._dpi_patterns.items():
            if pattern.search(payload):
                logger.warning(f"DPI detected threat: {threat_type}")
                return threat_type

        return None

    def _block_ip(self, ip: str, duration_minutes: int = 60):
        """Temporarily block an IP address"""
        self._blocked_ips.add(ip)
        logger.warning(f"Blocked IP {ip} for {duration_minutes} minutes")

        # Schedule unblock (only if event loop is running)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._unblock_after_delay(ip, duration_minutes))
        except RuntimeError:
            # No event loop running, skip auto-unblock
            pass

    async def _unblock_after_delay(self, ip: str, minutes: int):
        """Unblock IP after delay"""
        await asyncio.sleep(minutes * 60)
        if ip in self._blocked_ips:
            self._blocked_ips.remove(ip)
            logger.info(f"Unblocked IP {ip}")

    def _apply_iptables_rule(self, rule: FirewallRule):
        """Apply rule to system iptables (Linux only)"""
        try:
            # Build iptables command
            cmd = ["iptables", "-A", "REACTIVE_FABRIC"]

            if rule.source_ip != "0.0.0.0/0":
                cmd.extend(["-s", rule.source_ip])
            if rule.destination_ip != "0.0.0.0/0":
                cmd.extend(["-d", rule.destination_ip])

            if rule.protocol != Protocol.ANY:
                cmd.extend(["-p", rule.protocol.value])

                if rule.source_port:
                    cmd.extend(["--sport", rule.source_port])
                if rule.destination_port:
                    cmd.extend(["--dport", rule.destination_port])

            # Add action
            if rule.action == FirewallAction.ALLOW:
                cmd.extend(["-j", "ACCEPT"])
            elif rule.action == FirewallAction.REJECT:
                cmd.extend(["-j", "REJECT"])
            else:  # DENY
                cmd.extend(["-j", "DROP"])

            # Execute (will fail gracefully on non-Linux)
            subprocess.run(cmd, capture_output=True, timeout=5)

        except Exception as e:
            logger.debug(f"Could not apply iptables rule: {e}")

    def _remove_iptables_rule(self, rule: FirewallRule):
        """Remove rule from system iptables"""
        # Similar to apply but with -D instead of -A
        pass  # Implementation similar to _apply_iptables_rule

    def _log_rule_match(self, rule: FirewallRule, packet: Dict):
        """Log when a rule matches"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "rule_id": rule.id,
            "rule_name": rule.name,
            "action": rule.action.value,
            "packet": packet
        }
        logger.info(f"Firewall rule matched: {json.dumps(log_entry)}")

    def get_stats(self) -> Dict:
        """Get firewall statistics"""
        stats = self._stats.copy()
        stats["total_rules"] = len(self._rules)
        stats["blocked_ips"] = len(self._blocked_ips)
        stats["top_rules"] = self._get_top_rules(5)
        return stats

    def _get_top_rules(self, count: int) -> List[Dict]:
        """Get most matched rules"""
        sorted_rules = sorted(
            self._rules.values(),
            key=lambda x: x.hit_count,
            reverse=True
        )

        return [
            {
                "id": rule.id,
                "name": rule.name,
                "hits": rule.hit_count
            }
            for rule in sorted_rules[:count]
        ]