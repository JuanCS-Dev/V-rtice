"""
Contradiction Detector - Belief Update Validation
==================================================

Detects contradictory belief updates in ToM inferences.
Implements GAP 2 from ToM Engine refinement directive (FASE 2).

A contradiction occurs when belief value changes by > threshold in single update.
This helps identify unreliable or inconsistent mental state inferences.

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

from datetime import datetime
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """Detects contradictory belief updates in ToM inferences.

    Tracks belief updates and flags contradictions when value changes
    exceed a specified threshold in a single update.

    Attributes:
        threshold: Minimum delta to consider a contradiction (default: 0.5)
    """

    def __init__(self, threshold: float = 0.5):
        """Initialize ContradictionDetector.

        Args:
            threshold: Minimum absolute delta to flag as contradiction [0.0, 1.0]
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be in [0, 1], got {threshold}")

        self.threshold = threshold

        # Storage: agent_id → list of update records
        self._history: Dict[str, List[Dict]] = {}

        # Counters for statistics
        self._total_updates: Dict[str, int] = {}
        self._contradiction_count: Dict[str, int] = {}

        logger.info(f"ContradictionDetector initialized: threshold={threshold}")

    async def record_update(
        self,
        agent_id: str,
        belief_key: str,
        old_value: float,
        new_value: float
    ) -> bool:
        """Record a belief update and check for contradiction.

        Args:
            agent_id: Unique identifier for agent
            belief_key: Belief identifier (e.g., "confusion_history")
            old_value: Previous belief value [0.0, 1.0]
            new_value: Updated belief value [0.0, 1.0]

        Returns:
            True if contradiction detected, False otherwise
        """
        if agent_id not in self._history:
            self._history[agent_id] = []
            self._total_updates[agent_id] = 0
            self._contradiction_count[agent_id] = 0

        # Calculate delta (absolute change)
        delta = abs(new_value - old_value)

        # Check if contradiction
        is_contradiction = delta >= self.threshold

        # Record update
        update_record = {
            "belief_key": belief_key,
            "old_value": old_value,
            "new_value": new_value,
            "delta": delta,
            "timestamp": datetime.utcnow(),
            "is_contradiction": is_contradiction,
        }

        self._history[agent_id].append(update_record)
        self._total_updates[agent_id] += 1

        if is_contradiction:
            self._contradiction_count[agent_id] += 1
            logger.warning(
                f"Contradiction detected: agent={agent_id}, key={belief_key}, "
                f"old={old_value:.2f}, new={new_value:.2f}, delta={delta:.2f}"
            )
        else:
            logger.debug(
                f"Update recorded: agent={agent_id}, key={belief_key}, delta={delta:.2f}"
            )

        return is_contradiction

    def get_contradictions(self, agent_id: str) -> List[Dict]:
        """Get all contradictions for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of contradiction records (may be empty)
        """
        if agent_id not in self._history:
            return []

        # Filter for contradictions only
        contradictions = [
            record for record in self._history[agent_id]
            if record["is_contradiction"]
        ]

        return contradictions

    def clear_contradictions(self, agent_id: str) -> None:
        """Clear all contradiction history for an agent.

        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._history:
            self._history[agent_id] = []
            self._total_updates[agent_id] = 0
            self._contradiction_count[agent_id] = 0

        logger.info(f"Cleared contradictions for agent={agent_id}")

    def get_contradiction_rate(self, agent_id: str) -> float:
        """Calculate contradiction rate for an agent.

        Rate = contradictions / total_updates

        Args:
            agent_id: Agent identifier

        Returns:
            Contradiction rate [0.0, 1.0], or 0.0 if no updates
        """
        if agent_id not in self._total_updates or self._total_updates[agent_id] == 0:
            return 0.0

        total = self._total_updates[agent_id]
        contradictions = self._contradiction_count[agent_id]

        return contradictions / total

    def get_all_agents(self) -> List[str]:
        """Get list of all tracked agent IDs.

        Returns:
            List of agent IDs
        """
        return list(self._history.keys())

    def get_stats(self) -> Dict:
        """Get comprehensive statistics.

        Returns:
            Dictionary with global statistics
        """
        total_agents = len(self._history)
        total_updates = sum(self._total_updates.values())
        total_contradictions = sum(self._contradiction_count.values())

        global_rate = (
            total_contradictions / total_updates if total_updates > 0 else 0.0
        )

        return {
            "total_agents": total_agents,
            "total_updates": total_updates,
            "total_contradictions": total_contradictions,
            "global_contradiction_rate": global_rate,
            "threshold": self.threshold,
        }

    def __repr__(self) -> str:
        total_agents = len(self._history)
        total_contradictions = sum(self._contradiction_count.values())

        return (
            f"ContradictionDetector(threshold={self.threshold}, "
            f"agents={total_agents}, "
            f"contradictions={total_contradictions})"
        )
