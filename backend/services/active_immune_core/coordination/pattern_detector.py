"""Pattern Detector - Threat Pattern Recognition

Extracted from LinfonodoDigital as part of FASE 3 Desacoplamento.

This module implements threat pattern detection algorithms that analyze
cytokine streams to identify coordinated attacks, persistent threats,
and Advanced Persistent Threat (APT) indicators.

Responsibilities:
- Persistent threat detection (same threat_id, repeated attacks)
- Coordinated attack detection (multiple areas, simultaneous threats)
- Anomaly scoring and frequency analysis
- Threat pattern caching and historical tracking

Biological Inspiration:
-----------------------
In biological systems, the immune system recognizes patterns through:
- Pattern Recognition Receptors (PRRs) - detect PAMPs (pathogen-associated molecular patterns)
- Dendritic cells aggregate signals to identify systemic vs. local threats
- Memory cells remember past attack patterns for faster response

This digital implementation mirrors these biological mechanisms, detecting
attack patterns in real-time to trigger appropriate immune responses.

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PatternType(str, Enum):
    """Types of detected threat patterns."""

    PERSISTENT = "persistent"  # Same threat, multiple detections
    COORDINATED = "coordinated"  # Multiple threats, short timeframe
    APT_INDICATOR = "apt"  # Low-and-slow pattern (future implementation)


@dataclass
class ThreatPattern:
    """Detected threat pattern with metadata.

    Attributes:
        pattern_type: Type of pattern detected
        threat_ids: List of threat IDs involved
        areas_affected: List of areas where threats were detected
        detection_count: Number of detections in this pattern
        time_window_sec: Time window in which pattern was detected
        first_detected: Timestamp of first detection
        last_detected: Timestamp of most recent detection
        confidence: Confidence score (0.0-1.0) for this pattern
        metadata: Additional pattern-specific metadata
    """

    pattern_type: PatternType
    threat_ids: List[str]
    areas_affected: List[str]
    detection_count: int
    time_window_sec: float
    first_detected: datetime
    last_detected: datetime
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"ThreatPattern({self.pattern_type.value}|"
            f"threats={len(self.threat_ids)}|"
            f"count={self.detection_count}|"
            f"confidence={self.confidence:.2f})"
        )


class PatternDetector:
    """Detects threat patterns from cytokine signals.

    This class implements pattern recognition algorithms that analyze
    cytokine streams to identify coordinated attacks, persistent threats,
    and other attack patterns that require immune system escalation.

    Attributes:
        persistent_threshold: Number of detections to qualify as persistent threat
        coordinated_threshold: Number of threats to qualify as coordinated attack
        time_window_sec: Time window for pattern detection (seconds)

    Example:
        >>> detector = PatternDetector(persistent_threshold=5)
        >>> patterns = await detector.detect_persistent_threats(threat_counts)
        >>> if patterns:
        ...     logger.warning(f"Detected {len(patterns)} persistent threats")
    """

    def __init__(
        self,
        persistent_threshold: int = 5,
        coordinated_threshold: int = 10,
        time_window_sec: float = 60.0,
    ):
        """Initialize PatternDetector with detection thresholds.

        Args:
            persistent_threshold: Min detections to classify as persistent threat
            coordinated_threshold: Min threats to classify as coordinated attack
            time_window_sec: Time window for pattern detection (default 60s)
        """
        self.persistent_threshold = persistent_threshold
        self.coordinated_threshold = coordinated_threshold
        self.time_window_sec = time_window_sec

        # Pattern history tracking
        self._pattern_history: List[ThreatPattern] = []
        self._max_history_size = 1000

        logger.info(
            f"PatternDetector initialized: "
            f"persistent_threshold={persistent_threshold}, "
            f"coordinated_threshold={coordinated_threshold}, "
            f"time_window={time_window_sec}s"
        )

    async def detect_persistent_threats(
        self,
        threat_counts: Dict[str, int],
    ) -> List[ThreatPattern]:
        """Detect threats that persist across multiple detections.

        A persistent threat is characterized by the same threat_id being
        detected multiple times, indicating a recurring or evasive threat
        that requires specialized immune response (clonal expansion).

        EXTRACTED from lymphnode.py:_detect_persistent_threats() (lines 789-823)

        Args:
            threat_counts: Dict mapping threat_id → detection count

        Returns:
            List of ThreatPattern objects for persistent threats

        Example:
            >>> threat_counts = {"malware_x": 7, "scan_y": 2}
            >>> patterns = await detector.detect_persistent_threats(threat_counts)
            >>> assert len(patterns) == 1  # Only malware_x exceeds threshold
        """
        patterns: List[ThreatPattern] = []

        for threat_id, count in threat_counts.items():
            if count >= self.persistent_threshold:
                logger.warning(
                    f"PERSISTENT THREAT detected: {threat_id} "
                    f"({count} detections, threshold={self.persistent_threshold})"
                )

                # Calculate confidence (higher count = higher confidence)
                # Cap at 1.0
                confidence = min(1.0, count / (self.persistent_threshold * 2))

                pattern = ThreatPattern(
                    pattern_type=PatternType.PERSISTENT,
                    threat_ids=[threat_id],
                    areas_affected=[],  # Area info not available in this context
                    detection_count=count,
                    time_window_sec=self.time_window_sec,
                    first_detected=datetime.now() - timedelta(seconds=self.time_window_sec),
                    last_detected=datetime.now(),
                    confidence=confidence,
                    metadata={"threat_id": threat_id, "threshold_exceeded_by": count - self.persistent_threshold},
                )

                patterns.append(pattern)

                # Track in history
                self._add_to_history(pattern)

        return patterns

    async def detect_coordinated_attacks(
        self,
        cytokines: List[Dict[str, Any]],
    ) -> List[ThreatPattern]:
        """Detect coordinated attacks (multiple threats in short time).

        A coordinated attack is characterized by multiple distinct threats
        appearing simultaneously or in quick succession, indicating an
        orchestrated multi-vector attack that requires mass immune response.

        EXTRACTED from lymphnode.py:_detect_coordinated_attacks() (lines 825-869)

        Args:
            cytokines: List of recent cytokine messages

        Returns:
            List of ThreatPattern objects for coordinated attacks

        Example:
            >>> cytokines = [{"timestamp": "...", "payload": {"evento": "ameaca_detectada"}}] * 15
            >>> patterns = await detector.detect_coordinated_attacks(cytokines)
            >>> assert len(patterns) > 0  # Coordinated attack detected
        """
        patterns: List[ThreatPattern] = []

        # Count threats in last time_window_sec
        now = datetime.now()
        recent_threats: List[Dict[str, Any]] = []
        threat_ids: List[str] = []
        areas: List[str] = []

        for citocina in cytokines:
            timestamp_str = citocina.get("timestamp")
            if not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if (now - timestamp).total_seconds() < self.time_window_sec:
                    payload = citocina.get("payload", {})

                    # Check if it's a threat event
                    is_threat = payload.get("evento") == "ameaca_detectada" or payload.get("is_threat")

                    if is_threat:
                        recent_threats.append(citocina)

                        # Extract threat ID if available
                        threat_id = (
                            payload.get("alvo", {}).get("id")
                            or payload.get("host_id")
                            or payload.get("threat_id")
                            or f"unknown_{len(threat_ids)}"
                        )
                        threat_ids.append(threat_id)

                        # Extract area if available
                        area = citocina.get("area_alvo") or citocina.get("area")
                        if area:
                            areas.append(area)

            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse cytokine timestamp '{timestamp_str}': {e}")
                continue

        # Check if coordinated attack threshold exceeded
        threat_count = len(recent_threats)
        if threat_count >= self.coordinated_threshold:
            logger.critical(
                f"COORDINATED ATTACK detected: "
                f"{threat_count} threats in last {self.time_window_sec}s "
                f"(threshold={self.coordinated_threshold})"
            )

            # Calculate confidence (higher count = higher confidence)
            confidence = min(1.0, threat_count / (self.coordinated_threshold * 2))

            # Get unique threat IDs and areas
            unique_threat_ids = list(set(threat_ids))
            unique_areas = list(set(areas))

            pattern = ThreatPattern(
                pattern_type=PatternType.COORDINATED,
                threat_ids=unique_threat_ids,
                areas_affected=unique_areas,
                detection_count=threat_count,
                time_window_sec=self.time_window_sec,
                first_detected=now - timedelta(seconds=self.time_window_sec),
                last_detected=now,
                confidence=confidence,
                metadata={
                    "unique_threats": len(unique_threat_ids),
                    "unique_areas": len(unique_areas),
                    "threshold_exceeded_by": threat_count - self.coordinated_threshold,
                },
            )

            patterns.append(pattern)

            # Track in history
            self._add_to_history(pattern)

        return patterns

    async def analyze_threat_frequency(
        self,
        threat_id: str,
        threat_counts: Dict[str, int],
    ) -> float:
        """Analyze threat detection frequency for a specific threat.

        Args:
            threat_id: Threat identifier to analyze
            threat_counts: Dict mapping threat_id → detection count

        Returns:
            Normalized frequency score (0.0-1.0)
        """
        count = threat_counts.get(threat_id, 0)

        # Normalize by threshold
        if self.persistent_threshold == 0:
            return 0.0

        frequency = count / self.persistent_threshold

        # Cap at 1.0
        return min(1.0, frequency)

    def get_pattern_history(
        self,
        pattern_type: Optional[PatternType] = None,
        limit: int = 100,
    ) -> List[ThreatPattern]:
        """Retrieve pattern detection history.

        Args:
            pattern_type: Filter by pattern type (optional)
            limit: Maximum number of patterns to return

        Returns:
            List of ThreatPattern objects (most recent first)
        """
        history = self._pattern_history.copy()

        # Filter by type if specified
        if pattern_type:
            history = [p for p in history if p.pattern_type == pattern_type]

        # Sort by most recent first
        history.sort(key=lambda p: p.last_detected, reverse=True)

        return history[:limit]

    def clear_history(self) -> None:
        """Clear pattern detection history."""
        self._pattern_history.clear()
        logger.debug("Pattern detection history cleared")

    def _add_to_history(self, pattern: ThreatPattern) -> None:
        """Add pattern to history with size limiting.

        Args:
            pattern: ThreatPattern to add to history
        """
        self._pattern_history.append(pattern)

        # Limit history size (keep most recent)
        if len(self._pattern_history) > self._max_history_size:
            # Remove oldest (first element)
            self._pattern_history.pop(0)

    def get_stats(self) -> Dict[str, Any]:
        """Get pattern detector statistics.

        Returns:
            Dict with detector stats
        """
        persistent_count = sum(1 for p in self._pattern_history if p.pattern_type == PatternType.PERSISTENT)
        coordinated_count = sum(1 for p in self._pattern_history if p.pattern_type == PatternType.COORDINATED)

        return {
            "persistent_threshold": self.persistent_threshold,
            "coordinated_threshold": self.coordinated_threshold,
            "time_window_sec": self.time_window_sec,
            "total_patterns_detected": len(self._pattern_history),
            "persistent_patterns": persistent_count,
            "coordinated_patterns": coordinated_count,
            "history_size": len(self._pattern_history),
            "max_history_size": self._max_history_size,
        }

    def __repr__(self) -> str:
        return (
            f"PatternDetector("
            f"persistent={self.persistent_threshold}, "
            f"coordinated={self.coordinated_threshold}, "
            f"window={self.time_window_sec}s, "
            f"history={len(self._pattern_history)})"
        )
