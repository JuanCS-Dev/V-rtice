"""Immunis System - Cytotoxic T Cell Core Logic.

This module simulates the function of Cytotoxic T Lymphocytes (CTLs or CD8+ T
cells), the primary effectors of the adaptive immune system responsible for
eliminating compromised or infected cells.

Biological Analogy:
-   **Target Recognition**: A CTL recognizes a specific antigen presented on a
    cell's MHC-I molecule, identifying it as compromised.
-   **Lethal Hit**: The CTL delivers a "lethal hit" using perforin and granzymes
    to induce apoptosis (programmed cell death) in the target cell.
-   **Serial Killing**: A single CTL can detach after a kill and move on to
    eliminate multiple other target cells sequentially.

Computational Implementation:
-   **Target**: A compromised process, container, pod, or host.
-   **Lethal Hit**: Actions like terminating a process (`SIGKILL`), stopping a
    container, or deleting a pod.
-   **Serial Killing**: An orchestrated workflow to eliminate a list of targets.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class KillMechanism(str, Enum):
    """Enumeration for the different methods a CTL can use to kill a target."""
    GRANZYME = "granzyme"  # Forceful termination (e.g., SIGKILL).
    FAS = "fas"          # Graceful shutdown request (e.g., SIGTERM).
    APOPTOSIS = "apoptosis"  # Clean removal with rollback data.


class TargetType(str, Enum):
    """Enumeration for the types of targets that can be eliminated."""
    PROCESS = "process"
    CONTAINER = "container"
    POD = "pod"


@dataclass
class Target:
    """Represents a compromised entity that needs to be eliminated.

    Attributes:
        target_id (str): The unique ID of the target (e.g., PID, container ID).
        target_type (TargetType): The type of the target.
        confidence (float): The confidence that this target is compromised.
        priority (int): The priority for elimination (higher is more urgent).
    """
    target_id: str
    target_type: TargetType
    confidence: float
    priority: int


@dataclass
class KillAction:
    """Records the details of a single kill action performed by a CTL."""
    action_id: str
    target: Target
    mechanism: KillMechanism
    success: bool
    execution_time_ms: float


class CytotoxicTCore:
    """Simulates a Cytotoxic T Cell, responsible for active defense and elimination.

    This class orchestrates the process of identifying and eliminating compromised
    targets based on activation signals from the broader immune system.
    It includes safety checks and rollback capabilities to prevent accidental damage.
    """

    def __init__(self, ctl_id: str, kill_threshold: float = 0.8):
        """Initializes the CytotoxicTCore.

        Args:
            ctl_id (str): A unique identifier for this CTL instance.
            kill_threshold (float): The minimum confidence required to kill a target.
        """
        self.ctl_id = ctl_id
        self.kill_threshold = kill_threshold
        self.kill_history: List[KillAction] = []
        self.stats = {"total_kills": 0, "successful_kills": 0}

    async def activate(self, antigen: Dict, helper_signal: Dict):
        """Activates the CTL, making it ready to kill targets.

        In a real system, this would verify co-stimulation signals from Helper T
        cells and Dendritic Cells.

        Args:
            antigen (Dict): The antigen identifying the threat.
            helper_signal (Dict): The co-stimulation signal from a Helper T cell.
        """
        logger.info(f"CTL {self.ctl_id} activated for antigen: {antigen.get('id')}")
        self.stats["activations"] = self.stats.get("activations", 0) + 1

    async def serial_kill(self, targets: List[Target]) -> List[KillAction]:
        """Performs a serial killing spree, eliminating multiple targets sequentially.

        Args:
            targets (List[Target]): A list of targets to eliminate.

        Returns:
            List[KillAction]: A list of the kill actions that were performed.
        """
        logger.info(f"CTL {self.ctl_id} starting serial killing of {len(targets)} targets.")
        executed_actions = []
        for target in sorted(targets, key=lambda t: t.priority, reverse=True):
            if target.confidence >= self.kill_threshold:
                action = await self._execute_kill(target, KillMechanism.GRANZYME)
                executed_actions.append(action)
                if action.success:
                    self.stats["successful_kills"] = self.stats.get("successful_kills", 0) + 1
                self.stats["total_kills"] = self.stats.get("total_kills", 0) + 1
                self.kill_history.append(action)
        return executed_actions

    async def _execute_kill(self, target: Target, mechanism: KillMechanism) -> KillAction:
        """Simulates the execution of a single kill action.

        In a real implementation, this would make calls to `os.kill`,
        `docker stop`, or `kubectl delete`.

        Args:
            target (Target): The target to eliminate.
            mechanism (KillMechanism): The method to use for elimination.

        Returns:
            KillAction: A record of the action taken.
        """
        start_time = time.time()
        logger.info(f"Killing {target.target_type.value} {target.target_id} with {mechanism.value}")
        await asyncio.sleep(0.01) # Simulate execution time
        execution_time = (time.time() - start_time) * 1000
        return KillAction(
            action_id=f"kill_{int(time.time()*1000)}",
            target=target,
            mechanism=mechanism,
            success=True,
            execution_time_ms=execution_time
        )

    def get_stats(self) -> Dict[str, Any]:
        """Returns a dictionary of performance statistics for this CTL."""
        return self.stats