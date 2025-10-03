"""
Immunis - Cytotoxic T Cell Service
==================================
Active defense and threat elimination.

Biological inspiration: Cytotoxic T Lymphocytes (CD8+, CTLs)
- Kill infected/compromised cells
- Recognize antigen on MHC-I (self markers)
- Granzyme/perforin mediated apoptosis
- Serial killing (one CTL kills multiple targets)
- Memory CTLs (rapid recall)

Computational implementation:
- Process termination (kill compromised processes)
- Host isolation (network quarantine)
- Container/pod destruction
- Rollback automation (restore clean state)
- Coordinated strikes (serial killing)
- Audit logging (kill tracking)
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class KillMechanism(str, Enum):
    """CTL killing mechanisms"""
    GRANZYME = "granzyme"  # Process termination
    PERFORIN = "perforin"  # Memory corruption (force crash)
    FAS = "fas"  # Graceful shutdown (SIGTERM)
    APOPTOSIS = "apoptosis"  # Clean removal


class TargetType(str, Enum):
    """Target types for elimination"""
    PROCESS = "process"
    CONTAINER = "container"
    POD = "pod"
    VM = "vm"
    HOST = "host"


@dataclass
class Target:
    """Compromised target to eliminate"""
    target_id: str
    target_type: TargetType
    location: str  # Host, node, cluster
    threat_info: Dict  # Malware family, severity, etc.
    confidence: float  # Kill confidence (0-1)
    priority: int  # 1-10 (10 = highest)


@dataclass
class KillAction:
    """CTL kill action"""
    action_id: str
    ctl_id: str
    target: Target
    mechanism: KillMechanism

    # Execution
    executed_at: float
    execution_time_ms: float
    success: bool

    # Rollback info (for restoration if false positive)
    rollback_data: Optional[Dict] = None
    rollback_possible: bool = False

    # Audit
    evidence: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SerialKilling:
    """Serial killing session (one CTL, multiple targets)"""
    session_id: str
    ctl_id: str
    targets: List[Target]
    kills_completed: int = 0
    kills_failed: int = 0
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class CytotoxicTCore:
    """
    Cytotoxic T Cell - Active defense and elimination.

    Activation requirements:
    1. Antigen presentation from DC
    2. Co-stimulation from Helper T
    3. IL-2 signal (proliferation)
    4. Target recognition (MHC-I check)

    Killing process:
    1. Recognize target (antigen match)
    2. Form immunological synapse
    3. Deliver lethal hit (granzyme/perforin)
    4. Detach and kill next target (serial killing)
    5. Log kill for audit

    Safety mechanisms:
    - MHC-I check (don't kill healthy cells)
    - Confidence threshold (avoid false positives)
    - Rollback capability
    - Kill quota (prevent runaway)
    """

    def __init__(
        self,
        ctl_id: str,
        kill_threshold: float = 0.8,  # Min confidence to kill
        max_kills_per_session: int = 100,
        enable_rollback: bool = True
    ):
        self.ctl_id = ctl_id
        self.kill_threshold = kill_threshold
        self.max_kills_per_session = max_kills_per_session
        self.enable_rollback = enable_rollback

        # Kill history
        self.kill_history: List[KillAction] = []

        # Active serial killing sessions
        self.active_sessions: Dict[str, SerialKilling] = {}

        # Statistics
        self.stats = {
            "activations": 0,
            "total_kills": 0,
            "successful_kills": 0,
            "failed_kills": 0,
            "rollbacks_performed": 0,
            "serial_sessions": 0,
            "avg_kill_time_ms": 0.0
        }

        logger.info(
            f"Cytotoxic T Cell {ctl_id} initialized "
            f"(kill_threshold={kill_threshold}, max_kills={max_kills_per_session})"
        )

    async def activate(
        self,
        antigen: Dict,
        helper_signal: Dict,
        dc_signal: Dict
    ):
        """
        Activate CTL for killing.

        Biological: TCR + MHC-I + co-stimulation → activation
        Computational: Verify signals before granting kill permission

        Args:
            antigen: Antigen from DC
            helper_signal: IL-2, IFN-γ from Helper T
            dc_signal: IL-12 from DC
        """
        logger.info(
            f"[{self.ctl_id}] Activation signal received for {antigen.get('malware_family')}"
        )

        # Check activation requirements
        has_helper_signal = helper_signal.get('cytokine_type') in ['il2', 'ifn_gamma']
        has_dc_signal = dc_signal.get('cytokine_type') in ['il12', 'ifn_alpha']

        if not (has_helper_signal and has_dc_signal):
            logger.warning(
                f"[{self.ctl_id}] Activation failed: missing signals"
            )
            return

        self.stats["activations"] += 1

        logger.info(
            f"[{self.ctl_id}] Successfully activated! Ready to kill."
        )

    async def serial_kill(
        self,
        targets: List[Target],
        mechanism: KillMechanism = KillMechanism.GRANZYME
    ) -> SerialKilling:
        """
        Serial killing - eliminate multiple targets sequentially.

        Biological: One CTL can kill 10-20 infected cells serially
        Computational: Process multiple compromised targets efficiently

        Args:
            targets: List of targets to eliminate
            mechanism: Killing mechanism to use

        Returns:
            SerialKilling session record
        """
        session_id = f"serial_{int(time.time())}_{hash(self.ctl_id) % 10000}"

        # Sort targets by priority
        sorted_targets = sorted(targets, key=lambda t: t.priority, reverse=True)

        # Limit to max kills
        limited_targets = sorted_targets[:self.max_kills_per_session]

        logger.info(
            f"[{self.ctl_id}] Starting serial killing session: "
            f"{len(limited_targets)} targets"
        )

        session = SerialKilling(
            session_id=session_id,
            ctl_id=self.ctl_id,
            targets=limited_targets
        )

        self.active_sessions[session_id] = session
        self.stats["serial_sessions"] += 1

        # Kill each target
        for target in limited_targets:
            # Check MHC-I (self marker)
            if not await self._check_mhc_i(target):
                logger.warning(
                    f"[{self.ctl_id}] Target {target.target_id} has valid MHC-I, skipping"
                )
                session.kills_failed += 1
                continue

            # Execute kill
            kill_action = await self._execute_kill(target, mechanism)

            if kill_action.success:
                session.kills_completed += 1
                self.stats["successful_kills"] += 1
            else:
                session.kills_failed += 1
                self.stats["failed_kills"] += 1

            self.kill_history.append(kill_action)
            self.stats["total_kills"] += 1

            # Small delay between kills
            await asyncio.sleep(0.01)

        session.completed_at = time.time()

        logger.info(
            f"[{self.ctl_id}] Serial session complete: "
            f"{session.kills_completed} successful, {session.kills_failed} failed"
        )

        return session

    async def _check_mhc_i(self, target: Target) -> bool:
        """
        Check if target lacks MHC-I (self marker).

        Biological: Healthy cells present MHC-I, infected cells often don't
        Computational: Check if target has valid signatures/certificates

        Returns:
            True if target should be killed (missing self marker)
        """
        # Check confidence threshold
        if target.confidence < self.kill_threshold:
            logger.debug(
                f"[{self.ctl_id}] Target {target.target_id} below kill threshold "
                f"(confidence={target.confidence:.2f})"
            )
            return False

        # In production: check actual signatures, whitelists, etc.
        # For now: assume missing if confidence high

        return True

    async def _execute_kill(
        self,
        target: Target,
        mechanism: KillMechanism
    ) -> KillAction:
        """
        Execute kill on target.

        Mechanism:
        - GRANZYME: SIGKILL (immediate termination)
        - PERFORIN: Crash (memory corruption simulation)
        - FAS: SIGTERM (graceful shutdown)
        - APOPTOSIS: Clean removal with rollback data
        """
        start_time = time.time()

        logger.info(
            f"[{self.ctl_id}] Killing {target.target_type.value} {target.target_id} "
            f"using {mechanism.value}"
        )

        action_id = f"kill_{int(time.time())}_{hash(target.target_id) % 10000}"
        success = False
        rollback_data = None
        rollback_possible = False
        evidence = []

        try:
            if target.target_type == TargetType.PROCESS:
                success = await self._kill_process(target, mechanism)
                evidence.append(f"Process {target.target_id} terminated")

            elif target.target_type == TargetType.CONTAINER:
                success = await self._kill_container(target, mechanism)
                evidence.append(f"Container {target.target_id} stopped")

            elif target.target_type == TargetType.POD:
                success, rollback_data = await self._kill_pod(target, mechanism)
                rollback_possible = rollback_data is not None
                evidence.append(f"Pod {target.target_id} deleted")

            elif target.target_type == TargetType.VM:
                success = await self._kill_vm(target, mechanism)
                evidence.append(f"VM {target.target_id} terminated")

            elif target.target_type == TargetType.HOST:
                success = await self._isolate_host(target)
                evidence.append(f"Host {target.target_id} isolated")

        except Exception as e:
            logger.error(f"[{self.ctl_id}] Kill failed: {e}")
            success = False
            evidence.append(f"Error: {str(e)}")

        execution_time_ms = (time.time() - start_time) * 1000

        # Update average kill time
        n = self.stats["total_kills"] + 1
        old_avg = self.stats["avg_kill_time_ms"]
        self.stats["avg_kill_time_ms"] = (old_avg * (n - 1) + execution_time_ms) / n

        return KillAction(
            action_id=action_id,
            ctl_id=self.ctl_id,
            target=target,
            mechanism=mechanism,
            executed_at=start_time,
            execution_time_ms=execution_time_ms,
            success=success,
            rollback_data=rollback_data,
            rollback_possible=rollback_possible,
            evidence=evidence,
            metadata={
                "threat_family": target.threat_info.get("malware_family"),
                "severity": target.threat_info.get("severity")
            }
        )

    async def _kill_process(self, target: Target, mechanism: KillMechanism) -> bool:
        """Kill process"""
        # In production: subprocess.run(['kill', '-9', pid])
        # For now: simulate
        await asyncio.sleep(0.01)
        return True

    async def _kill_container(self, target: Target, mechanism: KillMechanism) -> bool:
        """Kill Docker container"""
        # In production: docker stop / docker kill
        await asyncio.sleep(0.02)
        return True

    async def _kill_pod(
        self,
        target: Target,
        mechanism: KillMechanism
    ) -> tuple[bool, Optional[Dict]]:
        """
        Kill Kubernetes pod.

        Returns:
            (success, rollback_data)
        """
        # Save pod spec for rollback
        rollback_data = {
            "pod_name": target.target_id,
            "namespace": target.location,
            "pod_spec": {"kind": "Pod"}  # In production: actual spec
        }

        # In production: kubectl delete pod
        await asyncio.sleep(0.03)

        return True, rollback_data if self.enable_rollback else None

    async def _kill_vm(self, target: Target, mechanism: KillMechanism) -> bool:
        """Kill virtual machine"""
        # In production: cloud provider API
        await asyncio.sleep(0.05)
        return True

    async def _isolate_host(self, target: Target) -> bool:
        """Isolate host (network quarantine)"""
        # In production: NetworkPolicy or firewall rules
        await asyncio.sleep(0.02)
        return True

    async def rollback(self, kill_action: KillAction) -> bool:
        """
        Rollback kill action (restore if false positive).

        Biological: No rollback in biology (cell death is permanent)
        Computational: We can restore from rollback data

        Args:
            kill_action: Kill action to rollback

        Returns:
            True if rollback successful
        """
        if not kill_action.rollback_possible:
            logger.warning(
                f"[{self.ctl_id}] Rollback not possible for {kill_action.action_id}"
            )
            return False

        logger.info(
            f"[{self.ctl_id}] Rolling back kill {kill_action.action_id}"
        )

        try:
            if kill_action.target.target_type == TargetType.POD:
                # In production: kubectl apply -f rollback_data
                await asyncio.sleep(0.05)

            self.stats["rollbacks_performed"] += 1

            logger.info(
                f"[{self.ctl_id}] Rollback successful for {kill_action.target.target_id}"
            )

            return True

        except Exception as e:
            logger.error(f"[{self.ctl_id}] Rollback failed: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get CTL statistics"""
        success_rate = (
            self.stats["successful_kills"] / self.stats["total_kills"]
            if self.stats["total_kills"] > 0 else 0.0
        )

        return {
            **self.stats,
            "success_rate": success_rate,
            "active_sessions": len(self.active_sessions)
        }


# Test
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("CYTOTOXIC T CELL SERVICE - ACTIVE DEFENSE")
    print("="*80 + "\n")

    async def test_cytotoxic_t():
        # Initialize CTL
        ctl = CytotoxicTCore(
            ctl_id="ctl_001",
            kill_threshold=0.7,
            enable_rollback=True
        )

        # Activation signals
        antigen = {"malware_family": "ransomware", "severity": "critical"}
        helper_signal = {"cytokine_type": "il2", "concentration": 0.8}
        dc_signal = {"cytokine_type": "il12", "concentration": 0.9}

        print("Activating CTL...")
        await ctl.activate(antigen, helper_signal, dc_signal)
        print()

        # Create targets
        targets = [
            Target(
                target_id="proc_12345",
                target_type=TargetType.PROCESS,
                location="host_1",
                threat_info={"malware_family": "ransomware", "severity": "critical"},
                confidence=0.95,
                priority=10
            ),
            Target(
                target_id="pod_evil_abc",
                target_type=TargetType.POD,
                location="default",
                threat_info={"malware_family": "ransomware", "severity": "high"},
                confidence=0.85,
                priority=8
            ),
            Target(
                target_id="container_sus",
                target_type=TargetType.CONTAINER,
                location="docker_host",
                threat_info={"malware_family": "trojan", "severity": "medium"},
                confidence=0.75,
                priority=5
            )
        ]

        print(f"Targets identified: {len(targets)}\n")

        # Serial killing
        print("Initiating serial killing session...\n")
        session = await ctl.serial_kill(targets, KillMechanism.GRANZYME)

        print(f"Serial session: {session.session_id}")
        print(f"  Kills completed: {session.kills_completed}")
        print(f"  Kills failed: {session.kills_failed}")
        print(f"  Duration: {session.completed_at - session.started_at:.2f}s")
        print()

        # Show kill history
        print("Kill history:")
        for kill in ctl.kill_history:
            print(f"  {kill.action_id}:")
            print(f"    Target: {kill.target.target_id} ({kill.target.target_type.value})")
            print(f"    Mechanism: {kill.mechanism.value}")
            print(f"    Success: {kill.success}")
            print(f"    Time: {kill.execution_time_ms:.2f}ms")
            print(f"    Rollback possible: {kill.rollback_possible}")
        print()

        # Test rollback
        if ctl.kill_history and ctl.kill_history[0].rollback_possible:
            print("Testing rollback on first kill...")
            rollback_success = await ctl.rollback(ctl.kill_history[0])
            print(f"  Rollback: {'successful' if rollback_success else 'failed'}")
            print()

        # Stats
        print("="*80)
        print("STATISTICS")
        print("="*80)
        stats = ctl.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n" + "="*80)
        print("CYTOTOXIC T CELL TEST COMPLETE!")
        print("="*80 + "\n")

    asyncio.run(test_cytotoxic_t())
