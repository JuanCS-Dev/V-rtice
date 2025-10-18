"""
Kill Switch Implementation
Emergency shutdown and containment mechanisms
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

class ShutdownLevel(Enum):
    """Shutdown urgency levels"""
    GRACEFUL = "graceful"      # Controlled shutdown with cleanup
    IMMEDIATE = "immediate"     # Fast shutdown, minimal cleanup
    EMERGENCY = "emergency"     # Instant kill, no cleanup
    NUCLEAR = "nuclear"         # Destroy everything including data

class ComponentType(Enum):
    """Types of components that can be killed"""
    CONTAINER = "container"
    PROCESS = "process"
    NETWORK = "network"
    VM = "vm"
    SERVICE = "service"

@dataclass
class KillTarget:
    """Target for kill switch activation"""
    id: str
    name: str
    component_type: ComponentType
    layer: int  # 1, 2, or 3
    critical: bool = False
    kill_command: Optional[str] = None
    verify_command: Optional[str] = None

@dataclass
class KillEvent:
    """Record of kill switch activation"""
    timestamp: datetime
    level: ShutdownLevel
    reason: str
    targets_killed: List[str]
    initiated_by: str
    success: bool
    duration_seconds: float

class KillSwitch:
    """
    Emergency kill switch for Reactive Fabric
    Implements multiple levels of shutdown urgency
    """

    def __init__(self, require_confirmation: bool = True):
        """
        Initialize kill switch

        Args:
            require_confirmation: Require confirmation for non-emergency kills
        """
        self.require_confirmation = require_confirmation
        self._armed = False
        self._targets: Dict[str, KillTarget] = {}
        self._kill_history: List[KillEvent] = []
        self._callbacks: List[Callable] = []

        # Dead man's switch
        self._deadmans_active = False
        self._deadmans_task: Optional[asyncio.Task] = None
        self._last_heartbeat = time.time()

        # Audit log
        self._audit_file = Path("/var/log/reactive_fabric/kill_switch.log")

    def arm(self, authorization_code: str) -> bool:
        """
        Arm the kill switch

        Args:
            authorization_code: Security code to arm

        Returns:
            True if armed successfully
        """
        # Verify authorization
        expected_code = os.getenv("KILL_SWITCH_AUTH_CODE", "VERTICE-EMERGENCY-2025")

        if authorization_code != expected_code:
            logger.error("Invalid authorization code for kill switch")
            self._audit_event("ARM_FAILED", {"reason": "invalid_code"})
            return False

        self._armed = True
        logger.warning("KILL SWITCH ARMED - Emergency shutdown ready")
        self._audit_event("ARMED", {"timestamp": datetime.now().isoformat()})
        return True

    def disarm(self) -> bool:
        """Disarm the kill switch"""
        if not self._armed:
            return False

        self._armed = False
        logger.info("Kill switch disarmed")
        self._audit_event("DISARMED", {"timestamp": datetime.now().isoformat()})
        return True

    def register_target(self, target: KillTarget):
        """Register a component that can be killed"""
        self._targets[target.id] = target
        logger.debug(f"Registered kill target: {target.name} (layer {target.layer})")

    def activate(self, level: ShutdownLevel, reason: str,
                 initiated_by: str, layer: Optional[int] = None) -> KillEvent:
        """
        ACTIVATE THE KILL SWITCH

        Args:
            level: Shutdown urgency level
            reason: Reason for activation
            initiated_by: Who/what initiated the kill
            layer: Specific layer to kill (None = all)

        Returns:
            KillEvent record
        """
        if not self._armed and level != ShutdownLevel.NUCLEAR:
            logger.error("Kill switch not armed, activation blocked")
            return KillEvent(
                timestamp=datetime.now(),
                level=level,
                reason=reason,
                targets_killed=[],
                initiated_by=initiated_by,
                success=False,
                duration_seconds=0
            )

        start_time = time.time()
        killed_targets = []

        logger.critical(f"KILL SWITCH ACTIVATED - Level: {level.value}, Reason: {reason}")
        self._audit_event("ACTIVATED", {
            "level": level.value,
            "reason": reason,
            "initiated_by": initiated_by,
            "layer": layer
        })

        try:
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(level, reason)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            # Select targets
            targets = self._select_targets(layer)

            # Execute kill based on level
            if level == ShutdownLevel.GRACEFUL:
                killed_targets = self._graceful_shutdown(targets)
            elif level == ShutdownLevel.IMMEDIATE:
                killed_targets = self._immediate_shutdown(targets)
            elif level == ShutdownLevel.EMERGENCY:
                killed_targets = self._emergency_shutdown(targets)
            elif level == ShutdownLevel.NUCLEAR:
                killed_targets = self._nuclear_shutdown(targets)

            success = len(killed_targets) == len(targets)

        except Exception as e:
            logger.error(f"Kill switch activation error: {e}")
            success = False

        # Record event
        duration = time.time() - start_time
        event = KillEvent(
            timestamp=datetime.now(),
            level=level,
            reason=reason,
            targets_killed=killed_targets,
            initiated_by=initiated_by,
            success=success,
            duration_seconds=duration
        )

        self._kill_history.append(event)
        self._audit_event("COMPLETED", {
            "level": level.value,
            "targets_killed": len(killed_targets),
            "duration": duration,
            "success": success
        })

        return event

    def _select_targets(self, layer: Optional[int]) -> List[KillTarget]:
        """Select targets based on layer"""
        if layer is None:
            return list(self._targets.values())

        return [t for t in self._targets.values() if t.layer == layer]

    def _graceful_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """Graceful shutdown with cleanup"""
        killed = []

        for target in targets:
            try:
                if target.component_type == ComponentType.CONTAINER:
                    # Docker stop (graceful)
                    cmd = ["docker", "stop", "-t", "30", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=35)

                elif target.component_type == ComponentType.PROCESS:
                    # SIGTERM
                    os.kill(int(target.id), signal.SIGTERM)
                    time.sleep(2)  # Give time to cleanup

                elif target.component_type == ComponentType.SERVICE:
                    # Systemctl stop
                    cmd = ["systemctl", "stop", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=30)

                killed.append(target.id)
                logger.info(f"Gracefully stopped: {target.name}")

            except Exception as e:
                logger.error(f"Failed to gracefully stop {target.name}: {e}")

        return killed

    def _immediate_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """Immediate shutdown, minimal cleanup"""
        killed = []

        for target in targets:
            try:
                if target.component_type == ComponentType.CONTAINER:
                    # Docker kill
                    cmd = ["docker", "kill", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=5)

                elif target.component_type == ComponentType.PROCESS:
                    # SIGKILL
                    os.kill(int(target.id), signal.SIGKILL)

                elif target.component_type == ComponentType.NETWORK:
                    # Drop network
                    cmd = ["docker", "network", "disconnect", "-f", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=5)

                killed.append(target.id)
                logger.warning(f"Immediately killed: {target.name}")

            except Exception as e:
                logger.error(f"Failed to kill {target.name}: {e}")

        return killed

    def _emergency_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """Emergency shutdown - instant kill all"""
        killed = []

        # Kill all targets in parallel for speed
        kill_commands = []

        for target in targets:
            if target.kill_command:
                kill_commands.append(target.kill_command)
            elif target.component_type == ComponentType.CONTAINER:
                kill_commands.append(f"docker kill {target.id}")
            elif target.component_type == ComponentType.PROCESS:
                kill_commands.append(f"kill -9 {target.id}")

        # Execute all kills in parallel
        processes = []
        for cmd in kill_commands:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            processes.append(p)

        # Wait for completion (max 5 seconds)
        for p in processes:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()

        # Mark all as killed (optimistic)
        killed = [t.id for t in targets]

        logger.critical(f"EMERGENCY KILL completed: {len(killed)} targets")
        return killed

    def _nuclear_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """
        NUCLEAR OPTION - Destroy everything including data
        USE ONLY IN EXTREME CONTAINMENT BREACH
        """
        logger.critical("NUCLEAR SHUTDOWN INITIATED - DESTROYING ALL DATA")

        killed = []

        try:
            # 1. Kill all containers
            subprocess.run("docker kill $(docker ps -q)", shell=True,
                           capture_output=True, timeout=5)

            # 2. Remove all containers
            subprocess.run("docker rm -f $(docker ps -aq)", shell=True,
                           capture_output=True, timeout=5)

            # 3. Delete all networks
            subprocess.run("docker network prune -f", shell=True,
                           capture_output=True, timeout=5)

            # 4. Delete all volumes (DATA LOSS!)
            if os.getenv("ALLOW_NUCLEAR_DATA_LOSS", "false").lower() == "true":
                subprocess.run("docker volume prune -f", shell=True,
                               capture_output=True, timeout=5)

                # Delete honeypot data
                honeypot_dirs = [
                    "/var/lib/reactive_fabric/honeypots",
                    "/var/log/reactive_fabric",
                    "/tmp/reactive_fabric"
                ]

                for dir_path in honeypot_dirs:
                    try:
                        subprocess.run(f"rm -rf {dir_path}", shell=True,
                                       capture_output=True, timeout=5)
                    except Exception:
                        pass

            # 5. Kill all processes matching pattern
            subprocess.run("pkill -9 -f reactive_fabric", shell=True,
                           capture_output=True, timeout=5)

            killed = [t.id for t in targets]
            logger.critical("NUCLEAR SHUTDOWN COMPLETE - System destroyed")

        except Exception as e:
            logger.error(f"Nuclear shutdown error: {e}")

        return killed

    async def start_deadmans_switch(self, timeout_seconds: int = 300):
        """
        Start dead man's switch
        Auto-triggers if no heartbeat received

        Args:
            timeout_seconds: Time before auto-trigger
        """
        if self._deadmans_active:
            logger.warning("Dead man's switch already active")
            return

        self._deadmans_active = True
        self._last_heartbeat = time.time()

        async def monitor():
            while self._deadmans_active:
                elapsed = time.time() - self._last_heartbeat

                if elapsed > timeout_seconds:
                    logger.critical("DEAD MAN'S SWITCH TRIGGERED - No heartbeat")
                    self.activate(
                        level=ShutdownLevel.EMERGENCY,
                        reason="Dead man's switch timeout",
                        initiated_by="DEADMANS_SWITCH"
                    )
                    break

                await asyncio.sleep(10)  # Check every 10 seconds

        self._deadmans_task = asyncio.create_task(monitor())
        logger.info(f"Dead man's switch active (timeout: {timeout_seconds}s)")

    def heartbeat(self):
        """Reset dead man's switch timer"""
        self._last_heartbeat = time.time()

    async def stop_deadmans_switch(self):
        """Stop dead man's switch"""
        self._deadmans_active = False
        if self._deadmans_task:
            self._deadmans_task.cancel()
            try:
                await self._deadmans_task
            except asyncio.CancelledError:
                pass

    def register_callback(self, callback: Callable):
        """Register callback for kill switch activation"""
        self._callbacks.append(callback)

    def _audit_event(self, event_type: str, details: Dict):
        """Record audit event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "armed": self._armed,
            "details": details
        }

        try:
            self._audit_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._audit_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_status(self) -> Dict:
        """Get kill switch status"""
        return {
            "armed": self._armed,
            "targets_registered": len(self._targets),
            "deadmans_active": self._deadmans_active,
            "last_heartbeat": self._last_heartbeat if self._deadmans_active else None,
            "kill_history": len(self._kill_history),
            "last_activation": self._kill_history[-1].timestamp.isoformat()
                               if self._kill_history else None
        }

class EmergencyShutdown:
    """
    High-level emergency shutdown coordinator
    Orchestrates kill switches across all layers
    """

    def __init__(self):
        """Initialize emergency shutdown system"""
        self.kill_switches: Dict[int, KillSwitch] = {}

        # Create kill switch for each layer
        for layer in [1, 2, 3]:
            self.kill_switches[layer] = KillSwitch(
                require_confirmation=(layer == 1)  # L1 requires confirmation
            )

    def containment_breach(self, source_layer: int):
        """
        CONTAINMENT BREACH DETECTED
        Emergency response to prevent propagation

        Args:
            source_layer: Layer where breach detected
        """
        logger.critical(f"CONTAINMENT BREACH in Layer {source_layer}")

        # Immediate isolation
        if source_layer == 3:
            # L3 breach - kill L3, isolate L2
            self.kill_switches[3].activate(
                level=ShutdownLevel.IMMEDIATE,
                reason="L3 containment breach",
                initiated_by="BREACH_DETECTOR",
                layer=3
            )

        elif source_layer == 2:
            # L2 breach - kill L2 and L3, protect L1
            self.kill_switches[2].activate(
                level=ShutdownLevel.EMERGENCY,
                reason="L2 containment breach",
                initiated_by="BREACH_DETECTOR",
                layer=2
            )
            self.kill_switches[3].activate(
                level=ShutdownLevel.IMMEDIATE,
                reason="L2 breach cascade",
                initiated_by="BREACH_DETECTOR",
                layer=3
            )

        elif source_layer == 1:
            # L1 breach - CATASTROPHIC - nuclear option
            logger.critical("LAYER 1 BREACH - NUCLEAR SHUTDOWN")
            for layer in [3, 2, 1]:
                self.kill_switches[layer].activate(
                    level=ShutdownLevel.NUCLEAR,
                    reason="L1 CATASTROPHIC BREACH",
                    initiated_by="BREACH_DETECTOR",
                    layer=layer
                )

    def controlled_shutdown(self, reason: str = "Maintenance"):
        """Controlled shutdown of all layers"""
        for layer in [3, 2, 1]:  # Shutdown from least to most critical
            self.kill_switches[layer].activate(
                level=ShutdownLevel.GRACEFUL,
                reason=reason,
                initiated_by="ADMINISTRATOR",
                layer=layer
            )
            time.sleep(5)  # Stagger shutdowns