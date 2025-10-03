"""
Immunis - Neutrophil Service
============================
First responder - rapid threat neutralization.

Biological inspiration: Neutrophils
- First immune cells to arrive at infection site
- Rapid response (<minutes)
- Phagocytosis of pathogens
- NETosis (neutrophil extracellular traps)
- Short-lived (24-48 hours)
- Auto-scaling based on infection load

Computational implementation:
- Lightweight container (fast spawn)
- Auto-scaling via HPA
- Integration with RTE (reflex triage)
- Ephemeral (TTL 24h)
- Pattern-based rapid response
- Netw trap deployment (block + isolate)
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class NeutrophilState(str, Enum):
    """Neutrophil lifecycle states"""
    CIRCULATING = "circulating"  # Patrolling
    ACTIVATED = "activated"  # Detected threat
    PHAGOCYTOSING = "phagocytosing"  # Attacking pathogen
    NETOSIS = "netosis"  # Deploying NET trap
    APOPTOSIS = "apoptosis"  # Programmed death


class ThreatType(str, Enum):
    """Threat categories for rapid response"""
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    MALWARE_DOWNLOAD = "malware_download"
    C2_COMMUNICATION = "c2_communication"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"


@dataclass
class ThreatEvent:
    """Detected threat event"""
    event_id: str
    timestamp: float
    threat_type: ThreatType
    source_ip: str
    target: str  # IP, port, service
    severity: float  # 0-1
    evidence: Dict  # Supporting data
    rte_correlation_id: Optional[str] = None  # Link to RTE detection


@dataclass
class NeutrophilAction:
    """Action taken by neutrophil"""
    action_type: str  # block_ip, rate_limit, isolate, deploy_net
    target: str
    parameters: Dict
    timestamp: float
    success: bool
    execution_time_ms: float


class NeutrophilCore:
    """
    Neutrophil - Fast-response immune cell.

    Lifecycle:
    1. Born from bone marrow (container spawn)
    2. Circulate (patrol network)
    3. Chemotaxis (attracted to infection - Kafka events)
    4. Activation (respond to threat)
    5. Phagocytosis or NETosis (neutralize threat)
    6. Apoptosis (auto-destroy after 24h)

    Target response time: <100ms
    """

    def __init__(
        self,
        neutrophil_id: str,
        ttl_seconds: int = 86400,  # 24 hours
        max_concurrent_threats: int = 10
    ):
        self.neutrophil_id = neutrophil_id
        self.ttl_seconds = ttl_seconds
        self.max_concurrent_threats = max_concurrent_threats

        self.state = NeutrophilState.CIRCULATING
        self.birth_time = time.time()
        self.death_time = self.birth_time + ttl_seconds

        # Active threats being handled
        self.active_threats: Dict[str, ThreatEvent] = {}

        # Action history
        self.action_history = deque(maxlen=1000)

        # Statistics
        self.stats = {
            "threats_neutralized": 0,
            "actions_taken": 0,
            "phagocytosis_count": 0,
            "netosis_count": 0,
            "avg_response_time_ms": 0.0,
            "age_seconds": 0
        }

        logger.info(
            f"Neutrophil {neutrophil_id} born (TTL={ttl_seconds}s, "
            f"max_concurrent={max_concurrent_threats})"
        )

    async def respond(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """
        Respond to detected threat.

        Decision tree:
        1. Port scan → Rate limit + alert
        2. Brute force → Block IP temporarily
        3. DDoS → Deploy NET (connection limits)
        4. Malware download → Block + quarantine
        5. C2 communication → Block IP permanently
        6. Data exfiltration → Block + isolate host
        7. Lateral movement → Isolate source + target

        Args:
            threat: Detected threat event

        Returns:
            List of actions taken
        """
        start_time = time.time()

        logger.info(
            f"[{self.neutrophil_id}] Responding to {threat.threat_type} "
            f"from {threat.source_ip}"
        )

        # Check capacity
        if len(self.active_threats) >= self.max_concurrent_threats:
            logger.warning(
                f"[{self.neutrophil_id}] At capacity "
                f"({len(self.active_threats)}/{self.max_concurrent_threats}), "
                "skipping threat"
            )
            return []

        # Transition state
        self.state = NeutrophilState.ACTIVATED
        self.active_threats[threat.event_id] = threat

        actions = []

        try:
            # Determine response based on threat type
            if threat.threat_type == ThreatType.PORT_SCAN:
                actions = await self._handle_port_scan(threat)

            elif threat.threat_type == ThreatType.BRUTE_FORCE:
                actions = await self._handle_brute_force(threat)

            elif threat.threat_type == ThreatType.DDoS:
                actions = await self._deploy_net(threat)

            elif threat.threat_type == ThreatType.MALWARE_DOWNLOAD:
                actions = await self._handle_malware_download(threat)

            elif threat.threat_type == ThreatType.C2_COMMUNICATION:
                actions = await self._handle_c2_communication(threat)

            elif threat.threat_type == ThreatType.DATA_EXFILTRATION:
                actions = await self._handle_data_exfiltration(threat)

            elif threat.threat_type == ThreatType.LATERAL_MOVEMENT:
                actions = await self._handle_lateral_movement(threat)

            # Update stats
            self.stats["threats_neutralized"] += 1
            self.stats["actions_taken"] += len(actions)

            response_time_ms = (time.time() - start_time) * 1000
            n = self.stats["threats_neutralized"]
            old_avg = self.stats["avg_response_time_ms"]
            self.stats["avg_response_time_ms"] = (old_avg * (n - 1) + response_time_ms) / n

            logger.info(
                f"[{self.neutrophil_id}] Neutralized {threat.threat_type}: "
                f"{len(actions)} actions in {response_time_ms:.2f}ms"
            )

        except Exception as e:
            logger.error(f"[{self.neutrophil_id}] Response failed: {e}")

        finally:
            # Remove from active threats
            self.active_threats.pop(threat.event_id, None)

            # Return to circulating if no active threats
            if not self.active_threats:
                self.state = NeutrophilState.CIRCULATING

        return actions

    async def _handle_port_scan(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """Handle port scanning activity"""
        self.state = NeutrophilState.PHAGOCYTOSING

        action = await self._execute_action(
            action_type="rate_limit",
            target=threat.source_ip,
            parameters={
                "max_connections_per_minute": 10,
                "duration_seconds": 300  # 5 minutes
            }
        )

        self.stats["phagocytosis_count"] += 1
        return [action]

    async def _handle_brute_force(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """Handle brute force attacks"""
        self.state = NeutrophilState.PHAGOCYTOSING

        # Temporary block
        action = await self._execute_action(
            action_type="block_ip",
            target=threat.source_ip,
            parameters={
                "duration_seconds": 3600,  # 1 hour
                "reason": "brute_force_detected"
            }
        )

        self.stats["phagocytosis_count"] += 1
        return [action]

    async def _deploy_net(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """
        Deploy NET (Neutrophil Extracellular Trap).

        Biological NETosis: Neutrophil releases DNA net to trap pathogens
        Computational NET: Connection rate limits + circuit breaker
        """
        self.state = NeutrophilState.NETOSIS

        actions = []

        # Deploy connection limits
        actions.append(await self._execute_action(
            action_type="deploy_net",
            target=threat.target,
            parameters={
                "type": "connection_limit",
                "max_connections": 100,
                "max_new_per_second": 10,
                "duration_seconds": 600  # 10 minutes
            }
        ))

        # Add circuit breaker
        actions.append(await self._execute_action(
            action_type="deploy_net",
            target=threat.target,
            parameters={
                "type": "circuit_breaker",
                "failure_threshold": 50,
                "timeout_seconds": 60
            }
        ))

        self.stats["netosis_count"] += 1
        return actions

    async def _handle_malware_download(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """Handle malware download attempts"""
        self.state = NeutrophilState.PHAGOCYTOSING

        actions = []

        # Block source IP
        actions.append(await self._execute_action(
            action_type="block_ip",
            target=threat.source_ip,
            parameters={
                "duration_seconds": 86400,  # 24 hours
                "reason": "malware_download"
            }
        ))

        # Quarantine downloaded file (if known)
        if "file_path" in threat.evidence:
            actions.append(await self._execute_action(
                action_type="quarantine_file",
                target=threat.evidence["file_path"],
                parameters={
                    "quarantine_dir": "/var/quarantine",
                    "reason": "malware_detected"
                }
            ))

        self.stats["phagocytosis_count"] += 1
        return actions

    async def _handle_c2_communication(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """Handle C2 (Command & Control) communication"""
        self.state = NeutrophilState.PHAGOCYTOSING

        # Permanent block for C2 servers
        action = await self._execute_action(
            action_type="block_ip",
            target=threat.source_ip,
            parameters={
                "duration_seconds": None,  # Permanent
                "reason": "c2_communication",
                "add_to_blacklist": True
            }
        )

        self.stats["phagocytosis_count"] += 1
        return [action]

    async def _handle_data_exfiltration(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """Handle data exfiltration attempts"""
        self.state = NeutrophilState.PHAGOCYTOSING

        actions = []

        # Block outbound connection
        actions.append(await self._execute_action(
            action_type="block_ip",
            target=threat.source_ip,
            parameters={
                "direction": "outbound",
                "duration_seconds": 86400,
                "reason": "data_exfiltration"
            }
        ))

        # Isolate compromised host
        if "pod_name" in threat.evidence:
            actions.append(await self._execute_action(
                action_type="isolate_host",
                target=threat.evidence["pod_name"],
                parameters={
                    "namespace": threat.evidence.get("namespace", "default"),
                    "isolation_type": "full"
                }
            ))

        self.stats["phagocytosis_count"] += 1
        return actions

    async def _handle_lateral_movement(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """Handle lateral movement attempts"""
        self.state = NeutrophilState.PHAGOCYTOSING

        actions = []

        # Isolate source
        actions.append(await self._execute_action(
            action_type="isolate_host",
            target=threat.source_ip,
            parameters={
                "reason": "lateral_movement_source"
            }
        ))

        # Isolate target
        if "target_ip" in threat.evidence:
            actions.append(await self._execute_action(
                action_type="isolate_host",
                target=threat.evidence["target_ip"],
                parameters={
                    "reason": "lateral_movement_target"
                }
            ))

        self.stats["phagocytosis_count"] += 1
        return actions

    async def _execute_action(
        self,
        action_type: str,
        target: str,
        parameters: Dict
    ) -> NeutrophilAction:
        """
        Execute defensive action.

        For production: integrate with RTE playbooks or K8s API
        For now: simulated execution
        """
        start_time = time.time()

        # Simulate action execution
        await asyncio.sleep(0.01)  # 10ms latency

        success = True  # Would check real execution result

        execution_time_ms = (time.time() - start_time) * 1000

        action = NeutrophilAction(
            action_type=action_type,
            target=target,
            parameters=parameters,
            timestamp=time.time(),
            success=success,
            execution_time_ms=execution_time_ms
        )

        self.action_history.append(action)

        logger.debug(
            f"[{self.neutrophil_id}] Executed {action_type} on {target} "
            f"in {execution_time_ms:.2f}ms"
        )

        return action

    def should_apoptose(self) -> bool:
        """
        Check if neutrophil should undergo apoptosis (programmed death).

        Biological: Neutrophils live 24-48 hours
        Computational: TTL expiration
        """
        current_time = time.time()
        age = current_time - self.birth_time

        self.stats["age_seconds"] = age

        return current_time >= self.death_time

    async def apoptose(self):
        """
        Programmed cell death.

        Cleanup and graceful shutdown.
        """
        logger.info(
            f"[{self.neutrophil_id}] Undergoing apoptosis after "
            f"{self.stats['age_seconds']:.0f}s lifespan"
        )

        self.state = NeutrophilState.APOPTOSIS

        # Cleanup active threats
        self.active_threats.clear()

        # Final stats report
        logger.info(
            f"[{self.neutrophil_id}] Final stats: "
            f"threats_neutralized={self.stats['threats_neutralized']}, "
            f"actions_taken={self.stats['actions_taken']}, "
            f"avg_response_time={self.stats['avg_response_time_ms']:.2f}ms"
        )

    def get_stats(self) -> Dict:
        """Get neutrophil statistics"""
        return {
            **self.stats,
            "state": self.state.value,
            "active_threats": len(self.active_threats),
            "ttl_remaining_seconds": max(0, self.death_time - time.time())
        }


# Test
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("NEUTROPHIL SERVICE - FIRST RESPONDER")
    print("="*80 + "\n")

    async def test_neutrophil():
        # Initialize neutrophil
        neutrophil = NeutrophilCore(
            neutrophil_id="neut_001",
            ttl_seconds=3600  # 1 hour for testing
        )

        # Simulate threat events
        threats = [
            ThreatEvent(
                event_id="evt_001",
                timestamp=time.time(),
                threat_type=ThreatType.PORT_SCAN,
                source_ip="192.168.1.100",
                target="10.0.0.5",
                severity=0.6,
                evidence={"ports_scanned": [22, 23, 80, 443, 3306]}
            ),
            ThreatEvent(
                event_id="evt_002",
                timestamp=time.time(),
                threat_type=ThreatType.BRUTE_FORCE,
                source_ip="192.168.1.101",
                target="10.0.0.5:22",
                severity=0.8,
                evidence={"failed_attempts": 50, "username": "admin"}
            ),
            ThreatEvent(
                event_id="evt_003",
                timestamp=time.time(),
                threat_type=ThreatType.DDoS,
                source_ip="multiple",
                target="10.0.0.5:80",
                severity=0.9,
                evidence={"requests_per_second": 10000}
            ),
            ThreatEvent(
                event_id="evt_004",
                timestamp=time.time(),
                threat_type=ThreatType.C2_COMMUNICATION,
                source_ip="10.0.0.10",
                target="malicious.c2server.com",
                severity=1.0,
                evidence={"protocol": "HTTPS", "encrypted": True}
            )
        ]

        print(f"Neutrophil {neutrophil.neutrophil_id} circulating...\n")

        # Respond to threats
        for threat in threats:
            print(f"Threat detected: {threat.threat_type} from {threat.source_ip}")

            actions = await neutrophil.respond(threat)

            print(f"  Actions taken:")
            for action in actions:
                print(
                    f"    - {action.action_type} → {action.target} "
                    f"({action.execution_time_ms:.2f}ms)"
                )
            print()

        # Check apoptosis
        if neutrophil.should_apoptose():
            await neutrophil.apoptose()

        # Stats
        print("="*80)
        print("STATISTICS")
        print("="*80)
        stats = neutrophil.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n" + "="*80)
        print("NEUTROPHIL TEST COMPLETE!")
        print("="*80 + "\n")

    asyncio.run(test_neutrophil())
