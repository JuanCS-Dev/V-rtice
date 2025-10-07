"""Salience Scorer - Calculates attention priority scores

Determines which events/anomalies warrant deep (foveal) analysis vs.
which can be handled by lightweight (peripheral) processing.
"""

from dataclasses import dataclass
from enum import Enum
import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SalienceLevel(Enum):
    """Salience levels for attention prioritization."""

    CRITICAL = 5  # Immediate foveal attention required
    HIGH = 4  # High priority for foveal analysis
    MEDIUM = 3  # Candidate for foveal analysis
    LOW = 2  # Peripheral monitoring sufficient
    MINIMAL = 1  # Background noise


@dataclass
class SalienceScore:
    """Salience score result."""

    score: float  # 0.0 - 1.0
    level: SalienceLevel
    factors: Dict[str, float]  # Individual factor contributions
    timestamp: float
    target_id: str
    requires_foveal: bool


class SalienceScorer:
    """Calculate salience scores for attention allocation.

    Salience is computed from multiple factors:
    - Novelty: How unusual is this event?
    - Magnitude: How large is the deviation?
    - Velocity: How quickly is it changing?
    - Threat: What's the potential impact?
    - Context: Historical importance
    """

    def __init__(self, foveal_threshold: float = 0.6, critical_threshold: float = 0.85):
        """Initialize salience scorer.

        Args:
            foveal_threshold: Minimum score to trigger foveal analysis (0.0-1.0)
            critical_threshold: Score for CRITICAL level (0.0-1.0)
        """
        self.foveal_threshold = foveal_threshold
        self.critical_threshold = critical_threshold
        self.baseline_stats = {}  # Baseline statistics for novelty detection
        self.score_history = []  # Recent scores for trending

    def calculate_salience(
        self, event: Dict[str, Any], context: Optional[Dict] = None
    ) -> SalienceScore:
        """Calculate salience score for an event.

        Args:
            event: Event data with metrics/features
            context: Optional historical context

        Returns:
            SalienceScore with overall score and factors
        """
        target_id = event.get("id", f"event_{time.time()}")

        # Calculate individual factors (0.0 - 1.0)
        factors = {}

        # 1. Novelty - Statistical surprise
        factors["novelty"] = self._calculate_novelty(event)

        # 2. Magnitude - Size of deviation
        factors["magnitude"] = self._calculate_magnitude(event)

        # 3. Velocity - Rate of change
        factors["velocity"] = self._calculate_velocity(event, context)

        # 4. Threat - Potential impact
        factors["threat"] = self._calculate_threat(event)

        # 5. Context - Historical importance
        factors["context"] = self._calculate_context(event, context)

        # Weighted aggregation
        weights = {
            "novelty": 0.25,
            "magnitude": 0.20,
            "velocity": 0.15,
            "threat": 0.30,  # Threat gets highest weight
            "context": 0.10,
        }

        overall_score = sum(factors[factor] * weights[factor] for factor in factors)

        # Clip to [0.0, 1.0]
        overall_score = np.clip(overall_score, 0.0, 1.0)

        # Determine salience level
        if overall_score >= self.critical_threshold:
            level = SalienceLevel.CRITICAL
        elif overall_score >= 0.75:
            level = SalienceLevel.HIGH
        elif overall_score >= 0.50:
            level = SalienceLevel.MEDIUM
        elif overall_score >= 0.25:
            level = SalienceLevel.LOW
        else:
            level = SalienceLevel.MINIMAL

        # Decide if foveal attention required
        requires_foveal = overall_score >= self.foveal_threshold

        score_result = SalienceScore(
            score=overall_score,
            level=level,
            factors=factors,
            timestamp=time.time(),
            target_id=target_id,
            requires_foveal=requires_foveal,
        )

        # Update history
        self.score_history.append(
            {"score": overall_score, "timestamp": time.time(), "target_id": target_id}
        )

        # Keep only last 1000 scores
        if len(self.score_history) > 1000:
            self.score_history = self.score_history[-1000:]

        logger.debug(
            f"Salience score: {overall_score:.3f} ({level.name}) "
            f"for {target_id} (foveal={requires_foveal})"
        )

        return score_result

    def _calculate_novelty(self, event: Dict) -> float:
        """Calculate novelty factor (0.0-1.0).

        Novelty = statistical surprise based on historical baselines.
        """
        try:
            # Extract metric value
            metric_name = event.get("metric", "unknown")
            value = event.get("value", 0)

            # Get or create baseline stats
            if metric_name not in self.baseline_stats:
                self.baseline_stats[metric_name] = {
                    "mean": value,
                    "std": 0.0,
                    "count": 1,
                    "values": [value],
                }
                return 0.5  # Moderate novelty for first observation

            baseline = self.baseline_stats[metric_name]

            # Calculate z-score (standardized deviation)
            if baseline["std"] > 0:
                z_score = abs((value - baseline["mean"]) / baseline["std"])
            else:
                z_score = 0.0

            # Convert z-score to novelty (0.0-1.0)
            # z=0 -> novelty=0, z=3 -> novelty=0.95, z>=6 -> novelty=1.0
            novelty = 1.0 - np.exp(-z_score / 3.0)

            # Update baseline (exponential moving average)
            alpha = 0.1  # Smoothing factor
            baseline["mean"] = alpha * value + (1 - alpha) * baseline["mean"]
            baseline["values"].append(value)

            # Keep only last 100 values for std calculation
            if len(baseline["values"]) > 100:
                baseline["values"] = baseline["values"][-100:]

            baseline["std"] = np.std(baseline["values"])
            baseline["count"] += 1

            return float(np.clip(novelty, 0.0, 1.0))

        except Exception as e:
            logger.warning(f"Novelty calculation error: {e}")
            return 0.5

    def _calculate_magnitude(self, event: Dict) -> float:
        """Calculate magnitude factor (0.0-1.0).

        Magnitude = normalized size of deviation from normal range.
        """
        try:
            # Get metric bounds
            value = event.get("value", 0)
            normal_min = event.get("normal_min", 0)
            normal_max = event.get("normal_max", 100)
            critical_min = event.get("critical_min", -50)
            critical_max = event.get("critical_max", 150)

            # If within normal range, magnitude is low
            if normal_min <= value <= normal_max:
                return 0.1

            # Calculate deviation from normal range
            if value < normal_min:
                # Below normal
                deviation = (
                    (normal_min - value) / (normal_min - critical_min)
                    if critical_min < normal_min
                    else 1.0
                )
            else:
                # Above normal
                deviation = (
                    (value - normal_max) / (critical_max - normal_max)
                    if critical_max > normal_max
                    else 1.0
                )

            magnitude = np.clip(deviation, 0.0, 1.0)

            return float(magnitude)

        except Exception as e:
            logger.warning(f"Magnitude calculation error: {e}")
            return 0.5

    def _calculate_velocity(self, event: Dict, context: Optional[Dict]) -> float:
        """Calculate velocity factor (0.0-1.0).

        Velocity = rate of change over time.
        """
        try:
            if not context or "previous_value" not in context:
                return 0.0  # No change data available

            current_value = event.get("value", 0)
            previous_value = context["previous_value"]
            time_delta = context.get("time_delta", 1.0)  # seconds

            # Calculate rate of change
            if time_delta > 0:
                rate = abs(current_value - previous_value) / time_delta
            else:
                rate = 0.0

            # Normalize rate (assuming max rate of 10 units/sec = velocity 1.0)
            max_rate = 10.0
            velocity = rate / max_rate

            return float(np.clip(velocity, 0.0, 1.0))

        except Exception as e:
            logger.warning(f"Velocity calculation error: {e}")
            return 0.0

    def _calculate_threat(self, event: Dict) -> float:
        """Calculate threat factor (0.0-1.0).

        Threat = potential impact on system health/security.
        """
        try:
            # Threat indicators
            indicators = {
                "error_rate": event.get("error_rate", 0) / 100.0,  # 0-100% -> 0-1
                "security_alert": 1.0 if event.get("security_alert", False) else 0.0,
                "anomaly_score": event.get("anomaly_score", 0),  # Already 0-1
                "failure_prediction": event.get("failure_probability", 0),  # 0-1
                "critical_service": (
                    1.0 if event.get("critical_service", False) else 0.5
                ),
            }

            # Weighted threat score
            threat_weights = {
                "error_rate": 0.20,
                "security_alert": 0.30,  # Security gets high weight
                "anomaly_score": 0.20,
                "failure_prediction": 0.20,
                "critical_service": 0.10,
            }

            threat = sum(indicators[key] * threat_weights[key] for key in indicators)

            return float(np.clip(threat, 0.0, 1.0))

        except Exception as e:
            logger.warning(f"Threat calculation error: {e}")
            return 0.5

    def _calculate_context(self, event: Dict, context: Optional[Dict]) -> float:
        """Calculate context factor (0.0-1.0).

        Context = historical importance based on past events.
        """
        try:
            if not context:
                return 0.5  # Neutral importance without context

            # Context indicators
            recent_alerts = context.get("recent_alerts_count", 0)
            similar_past_incidents = context.get("similar_incidents", 0)
            time_since_last_alert = context.get(
                "time_since_last_alert", 3600
            )  # seconds

            # Recency boost (more recent = higher context)
            recency = 1.0 - min(time_since_last_alert / 3600.0, 1.0)  # 1h = 0

            # Alert frequency penalty (too many alerts = lower importance)
            frequency_penalty = 1.0 - min(recent_alerts / 10.0, 1.0)

            # Historical pattern boost
            pattern_boost = min(similar_past_incidents / 5.0, 1.0)

            context_score = (
                recency * 0.4 + frequency_penalty * 0.3 + pattern_boost * 0.3
            )

            return float(np.clip(context_score, 0.0, 1.0))

        except Exception as e:
            logger.warning(f"Context calculation error: {e}")
            return 0.5

    def get_top_salient_targets(self, n: int = 10) -> List[Dict]:
        """Get top N most salient recent targets.

        Args:
            n: Number of top targets to return

        Returns:
            List of top N targets sorted by score (descending)
        """
        if not self.score_history:
            return []

        # Sort by score descending
        sorted_history = sorted(
            self.score_history, key=lambda x: x["score"], reverse=True
        )

        return sorted_history[:n]

    def reset_baselines(self):
        """Reset baseline statistics (useful for testing)."""
        self.baseline_stats = {}
        self.score_history = []
        logger.info("Salience scorer baselines reset")
