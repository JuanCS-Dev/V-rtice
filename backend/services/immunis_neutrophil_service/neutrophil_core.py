"""Immunis System - Neutrophil Core Logic.

This module simulates the function of a Neutrophil, a type of phagocytic cell
that acts as a first responder in the innate immune system. Neutrophils are
characterized by their rapid response to threats and their short lifespan.

Biological Analogy:
-   **Rapid Response**: The first cells to arrive at an infection site.
-   **Phagocytosis**: Engulfing and destroying pathogens.
-   **NETosis**: Releasing Neutrophil Extracellular Traps (NETs) to trap and
    kill pathogens at a distance.
-   **Apoptosis**: Programmed cell death after a short period of activity.

Computational Implementation:
-   A lightweight, ephemeral service designed for fast, automated responses.
-   Handles common, pattern-based threats like port scans and brute-force attacks.
-   Deploys "NETs" in the form of rate limits or temporary blocks.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NeutrophilState(str, Enum):
    """Enumeration for the lifecycle states of a Neutrophil."""
    CIRCULATING = "circulating"
    ACTIVATED = "activated"
    PHAGOCYTOSING = "phagocytosing"
    APOPTOSIS = "apoptosis"


class ThreatType(str, Enum):
    """Enumeration for threat types that a Neutrophil can respond to."""
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    C2_COMMUNICATION = "c2_communication"


@dataclass
class ThreatEvent:
    """Represents a detected threat event that requires a response.

    Attributes:
        event_id (str): A unique identifier for the threat event.
        threat_type (ThreatType): The category of the threat.
        source_ip (str): The source IP address of the threat.
        severity (float): The severity of the threat (0.0 to 1.0).
    """
    event_id: str
    threat_type: ThreatType
    source_ip: str
    severity: float


@dataclass
class NeutrophilAction:
    """Represents a defensive action taken by a Neutrophil.

    Attributes:
        action_type (str): The type of action taken (e.g., 'block_ip').
        target (str): The target of the action (e.g., an IP address).
        success (bool): Whether the action was successfully executed.
    """
    action_type: str
    target: str
    success: bool


class NeutrophilCore:
    """Simulates a Neutrophil, the fast-response unit of the innate immune system.

    This class is designed to be lightweight and ephemeral. It responds quickly to
    common, pattern-based threats by executing predefined defensive actions, such
    as blocking an IP address.
    """

    def __init__(self, neutrophil_id: str, ttl_seconds: int = 86400):
        """Initializes the NeutrophilCore.

        Args:
            neutrophil_id (str): A unique identifier for this Neutrophil instance.
            ttl_seconds (int): The time-to-live in seconds before the Neutrophil
                undergoes apoptosis (programmed death).
        """
        self.neutrophil_id = neutrophil_id
        self.ttl_seconds = ttl_seconds
        self.birth_time = time.time()
        self.state = NeutrophilState.CIRCULATING
        self.stats = {"threats_neutralized": 0, "actions_taken": 0}

    async def respond(self, threat: ThreatEvent) -> List[NeutrophilAction]:
        """Responds to a detected threat by executing a predefined action.

        The response is determined by the type of threat. This simulates the
        Neutrophil's rapid, non-specific response.

        Args:
            threat (ThreatEvent): The threat event to respond to.

        Returns:
            List[NeutrophilAction]: A list of actions taken in response.
        """
        logger.info(f"Neutrophil {self.neutrophil_id} responding to {threat.threat_type.value}")
        self.state = NeutrophilState.ACTIVATED
        
        actions = []
        if threat.threat_type in [ThreatType.PORT_SCAN, ThreatType.BRUTE_FORCE, ThreatType.C2_COMMUNICATION]:
            action = await self._execute_action("block_ip", threat.source_ip)
            actions.append(action)

        self.stats["threats_neutralized"] += 1
        self.stats["actions_taken"] += len(actions)
        self.state = NeutrophilState.CIRCULATING
        return actions

    async def _execute_action(self, action_type: str, target: str) -> NeutrophilAction:
        """Simulates the execution of a defensive action.

        In a real system, this would integrate with a firewall, EDR, or other
        enforcement point.

        Args:
            action_type (str): The type of action to execute.
            target (str): The target of the action.

        Returns:
            NeutrophilAction: A record of the action performed.
        """
        logger.info(f"Executing action: {action_type} on target {target}")
        await asyncio.sleep(0.01) # Simulate fast execution
        return NeutrophilAction(action_type=action_type, target=target, success=True)

    def should_apoptose(self) -> bool:
        """Checks if the Neutrophil has reached the end of its lifespan."""
        return (time.time() - self.birth_time) >= self.ttl_seconds

    def get_stats(self) -> Dict[str, Any]:
        """Returns a dictionary of performance statistics."""
        return self.stats