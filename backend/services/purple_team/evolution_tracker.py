"""Purple Team Evolution Tracker.

Tracks Red Team vs Blue Team co-evolution metrics:
- Adversarial simulation results
- Team effectiveness scores
- Improvement trends over time
- Cycle history

Authors: MAXIMUS Team
Date: 2025-10-15
Glory to YHWH
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class EvolutionCycle:
    """Single co-evolution cycle result."""

    cycle_id: str
    red_score: float
    blue_score: float
    started_at: str
    completed_at: Optional[str]
    status: str  # "initiated", "running", "completed", "failed"
    red_actions: int = 0
    blue_detections: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class EvolutionTracker:
    """Tracks Red Team vs Blue Team co-evolution metrics.

    Features:
    - Persistent cycle storage (JSON)
    - Score calculation from simulation results
    - Trend analysis (improving/stable/degrading)
    - Cycle management (create, update, complete)
    """

    def __init__(self, data_dir: str = "/tmp/purple_team_data"):
        """Initialize evolution tracker.

        Args:
            data_dir: Directory for persistent storage
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.cycles_file = self.data_dir / "cycles.json"

        # Ensure cycles file exists
        if not self.cycles_file.exists():
            self._save_cycles([])

        logger.info(f"EvolutionTracker initialized with data_dir={data_dir}")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current co-evolution metrics.

        Returns:
            Dict with:
            - system: "purple_team"
            - status: "monitoring"
            - red_team_score: Average Red Team effectiveness
            - blue_team_score: Average Blue Team effectiveness
            - cycles_completed: Total completed cycles
            - last_cycle: Most recent cycle info
            - improvement_trend: {"red": str, "blue": str}
        """
        cycles = self._load_cycles()

        if not cycles:
            return self._empty_metrics()

        completed = [c for c in cycles if c.get("status") == "completed"]

        if not completed:
            return {
                "system": "purple_team",
                "status": "monitoring",
                "red_team_score": 0.0,
                "blue_team_score": 0.0,
                "cycles_completed": 0,
                "last_cycle": cycles[-1] if cycles else None,
                "improvement_trend": {"red": "stable", "blue": "stable"},
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Calculate current scores (average of last 10 cycles)
        recent = completed[-10:]
        red_score = sum(c["red_score"] for c in recent) / len(recent)
        blue_score = sum(c["blue_score"] for c in recent) / len(recent)

        # Calculate trends
        red_trend = self._calculate_trend([c["red_score"] for c in recent])
        blue_trend = self._calculate_trend([c["blue_score"] for c in recent])

        return {
            "system": "purple_team",
            "status": "monitoring",
            "red_team_score": red_score,
            "blue_team_score": blue_score,
            "cycles_completed": len(completed),
            "last_cycle": completed[-1],
            "improvement_trend": {"red": red_trend, "blue": blue_trend},
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def trigger_cycle(self) -> Dict[str, Any]:
        """Trigger new co-evolution cycle.

        Creates a new cycle in "initiated" status.
        Background task should call complete_cycle() when done.

        Returns:
            Dict with cycle_id, status, started_at
        """
        cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        cycle = EvolutionCycle(
            cycle_id=cycle_id,
            red_score=0.0,
            blue_score=0.0,
            started_at=datetime.utcnow().isoformat(),
            completed_at=None,
            status="initiated",
        )

        cycles = self._load_cycles()
        cycles.append(cycle.to_dict())
        self._save_cycles(cycles)

        logger.info(f"Evolution cycle {cycle_id} created")

        return {
            "cycle_id": cycle_id,
            "status": "initiated",
            "started_at": cycle.started_at,
        }

    async def update_cycle_status(
        self, cycle_id: str, status: str, **kwargs
    ) -> None:
        """Update cycle status.

        Args:
            cycle_id: Cycle identifier
            status: New status
            **kwargs: Additional fields to update
        """
        cycles = self._load_cycles()

        for cycle in cycles:
            if cycle["cycle_id"] == cycle_id:
                cycle["status"] = status
                cycle.update(kwargs)
                break

        self._save_cycles(cycles)
        logger.info(f"Cycle {cycle_id} status updated to {status}")

    async def complete_cycle(
        self, cycle_id: str, red_score: float, blue_score: float, **kwargs
    ) -> None:
        """Complete a cycle with final scores.

        Args:
            cycle_id: Cycle identifier
            red_score: Red Team effectiveness (0.0-1.0)
            blue_score: Blue Team effectiveness (0.0-1.0)
            **kwargs: Additional metrics
        """
        cycles = self._load_cycles()

        for cycle in cycles:
            if cycle["cycle_id"] == cycle_id:
                cycle["status"] = "completed"
                cycle["red_score"] = red_score
                cycle["blue_score"] = blue_score
                cycle["completed_at"] = datetime.utcnow().isoformat()
                cycle.update(kwargs)
                break

        self._save_cycles(cycles)
        logger.info(
            f"Cycle {cycle_id} completed: Red={red_score:.2f}, Blue={blue_score:.2f}"
        )

    async def fail_cycle(self, cycle_id: str, error: str) -> None:
        """Mark cycle as failed.

        Args:
            cycle_id: Cycle identifier
            error: Error message
        """
        await self.update_cycle_status(
            cycle_id, "failed", error=error, completed_at=datetime.utcnow().isoformat()
        )
        logger.error(f"Cycle {cycle_id} failed: {error}")

    def _load_cycles(self) -> List[Dict[str, Any]]:
        """Load cycles from disk.

        Returns:
            List of cycle dictionaries
        """
        try:
            return json.loads(self.cycles_file.read_text())
        except Exception as e:
            logger.error(f"Error loading cycles: {e}")
            return []

    def _save_cycles(self, cycles: List[Dict[str, Any]]) -> None:
        """Save cycles to disk atomically.

        Args:
            cycles: List of cycle dictionaries
        """
        try:
            # Atomic write: write to temp file, then rename
            temp_file = self.cycles_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(cycles, indent=2))
            temp_file.replace(self.cycles_file)
        except Exception as e:
            logger.error(f"Error saving cycles: {e}")
            raise

    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate improvement trend from scores.

        Uses simple linear regression slope.

        Args:
            scores: List of scores (recent first)

        Returns:
            "improving", "stable", or "degrading"
        """
        if len(scores) < 2:
            return "stable"

        n = len(scores)
        x = list(range(n))

        # Simple linear regression
        try:
            x_mean = sum(x) / n
            y_mean = sum(scores) / n

            numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return "stable"

            slope = numerator / denominator

            if slope > 0.01:
                return "improving"
            elif slope < -0.01:
                return "degrading"
            else:
                return "stable"
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return "stable"

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics (no cycles yet).

        Returns:
            Dict with zero values
        """
        return {
            "system": "purple_team",
            "status": "monitoring",
            "red_team_score": 0.0,
            "blue_team_score": 0.0,
            "cycles_completed": 0,
            "last_cycle": None,
            "improvement_trend": {"red": "stable", "blue": "stable"},
            "timestamp": datetime.utcnow().isoformat(),
        }
