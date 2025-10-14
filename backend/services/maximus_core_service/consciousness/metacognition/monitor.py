"""
Metacognitive Monitor - Confidence Tracking and Reasoning Quality
==================================================================

Implements basic metacognition for social cognition pipeline:
- Tracks prediction errors over time
- Calculates confidence based on recent performance
- Provides self-monitoring for reasoning quality

This is a simplified metacognition implementation focused on confidence
tracking. Future enhancements will add bias detection and strategy shifting.

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Article IV (Operational Excellence)
"""

from collections import deque
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MetacognitiveMonitor:
    """
    Tracks reasoning quality and calculates confidence.

    Implements simple error-based confidence calculation:
    - Records prediction errors (0-1, where 1 = complete error)
    - Maintains sliding window of recent errors
    - Confidence = 1 - average_error

    Usage:
        monitor = MetacognitiveMonitor(window_size=100)

        # Record error after prediction validated
        monitor.record_error(error=0.2)  # 20% error

        # Get current confidence
        confidence = monitor.calculate_confidence()
        print(f"Current confidence: {confidence:.2f}")  # 0.80

    Future Enhancements (Phase 2):
    - Cognitive bias detection (confirmation, anchoring, availability)
    - Strategy shift recommendations
    - Logical consistency checking
    """

    def __init__(self, window_size: int = 100):
        """Initialize Metacognitive Monitor.

        Args:
            window_size: Number of recent errors to track
        """
        self.errors: deque = deque(maxlen=window_size)
        self.window_size = window_size

        # Statistics
        self.total_recordings = 0

        logger.info(f"MetacognitiveMonitor initialized: window_size={window_size}")

    def record_error(self, error: float) -> None:
        """Record a prediction error.

        Args:
            error: Error magnitude (0-1)
                0.0 = perfect prediction
                1.0 = complete error
        """
        if not 0.0 <= error <= 1.0:
            logger.warning(f"Error value {error} outside [0,1] range, clamping")
            error = max(0.0, min(1.0, error))

        self.errors.append(error)
        self.total_recordings += 1

        logger.debug(f"Metacog: Recorded error={error:.3f}, total_recordings={self.total_recordings}")

    def calculate_confidence(self) -> float:
        """Calculate current confidence based on recent errors.

        Returns:
            Confidence score (0-1)
                1.0 = no errors (perfect confidence)
                0.0 = all errors (no confidence)
                0.5 = neutral (no data yet)
        """
        if not self.errors:
            # No data yet - return neutral confidence
            return 0.5

        # Calculate average error
        avg_error = sum(self.errors) / len(self.errors)

        # Confidence is inverse of error
        confidence = 1.0 - avg_error

        return confidence

    def get_recent_errors(self, n: int = 10) -> List[float]:
        """Get N most recent errors.

        Args:
            n: Number of recent errors to retrieve

        Returns:
            List of recent errors (most recent last)
        """
        return list(self.errors)[-n:]

    def get_error_trend(self, window: int = 10) -> str:
        """Analyze error trend over recent window.

        Args:
            window: Number of recent errors to analyze

        Returns:
            Trend string: "improving", "stable", "degrading", "insufficient_data"
        """
        if len(self.errors) < window:
            return "insufficient_data"

        recent = list(self.errors)[-window:]

        # Split into first half and second half
        mid = window // 2
        first_half_avg = sum(recent[:mid]) / mid
        second_half_avg = sum(recent[mid:]) / (window - mid)

        # Compare averages
        if second_half_avg < first_half_avg - 0.1:  # 10% improvement
            return "improving"
        elif second_half_avg > first_half_avg + 0.1:  # 10% degradation
            return "degrading"
        else:
            return "stable"

    def reset(self) -> None:
        """Reset error history.

        Useful when switching to new task domain or after significant
        system changes.
        """
        old_count = len(self.errors)
        self.errors.clear()
        logger.info(f"Metacog: Reset error history ({old_count} errors cleared)")

    def get_stats(self) -> Dict[str, Any]:
        """Get metacognition statistics.

        Returns:
            Statistics dictionary
        """
        confidence = self.calculate_confidence()
        trend = self.get_error_trend()

        return {
            "total_recordings": self.total_recordings,
            "window_size": self.window_size,
            "current_error_count": len(self.errors),
            "current_confidence": confidence,
            "error_trend": trend,
            "avg_error": (1.0 - confidence) if self.errors else 0.0,
        }

    def __repr__(self) -> str:
        confidence = self.calculate_confidence()
        return (
            f"MetacognitiveMonitor("
            f"errors={len(self.errors)}/{self.window_size}, "
            f"confidence={confidence:.3f})"
        )
