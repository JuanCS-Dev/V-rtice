"""
RTE - Fusion Engine
====================
Combines Hyperscan pattern matching + Fast ML models.

Decision logic: BLOCK / INVESTIGATE / ALLOW
Target latency: <50ms end-to-end
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from hyperscan_matcher import HyperscanMatcher, Match
from fast_ml import FastMLEngine, ThreatScore

logger = logging.getLogger(__name__)


class ThreatAction(str, Enum):
    """Decision actions"""
    BLOCK = "BLOCK"  # Immediate blocking
    INVESTIGATE = "INVESTIGATE"  # Flag for analysis
    ALLOW = "ALLOW"  # Pass through
    QUARANTINE = "QUARANTINE"  # Isolate for analysis


@dataclass
class FusionResult:
    """Combined result from all detection engines"""
    action: ThreatAction
    confidence: float  # 0-1
    threat_level: str  # critical, high, medium, low
    hyperscan_matches: List[Match]
    ml_score: Optional[ThreatScore]
    reasoning: str
    latency_ms: float
    metadata: Dict


class FusionEngine:
    """
    Fusion engine combining pattern matching + ML.

    Decision tree:
    1. Hyperscan match with severity=critical → BLOCK (no ML needed)
    2. Hyperscan match + ML anomaly → BLOCK
    3. ML anomaly only (high confidence) → INVESTIGATE
    4. Hyperscan match (low severity) → INVESTIGATE
    5. No detections → ALLOW
    """

    def __init__(
        self,
        hyperscan_matcher: HyperscanMatcher,
        ml_engine: FastMLEngine
    ):
        self.hyperscan = hyperscan_matcher
        self.ml = ml_engine

        # Decision thresholds
        self.thresholds = {
            "ml_high_confidence": 0.8,
            "ml_medium_confidence": 0.5,
            "combined_block": 0.7
        }

        logger.info("Fusion engine initialized")

    def analyze(
        self,
        data: bytes,
        event_metadata: Optional[Dict] = None
    ) -> FusionResult:
        """
        Analyze data with all detection engines.

        Args:
            data: Raw data to analyze
            event_metadata: Additional event context (for ML features)

        Returns:
            FusionResult with action and confidence
        """
        start_time = time.time()

        # Step 1: Hyperscan pattern matching
        hyperscan_matches = self.hyperscan.scan(data)

        # Quick exit: Critical pattern match
        if hyperscan_matches:
            highest_severity = self.hyperscan.get_highest_severity(hyperscan_matches)

            if highest_severity == "critical":
                latency_ms = (time.time() - start_time) * 1000

                return FusionResult(
                    action=ThreatAction.BLOCK,
                    confidence=1.0,
                    threat_level="critical",
                    hyperscan_matches=hyperscan_matches,
                    ml_score=None,
                    reasoning=f"Critical pattern match: {hyperscan_matches[0].metadata.get('description', 'Unknown')}",
                    latency_ms=latency_ms,
                    metadata={"fast_path": True, "detection_method": "hyperscan"}
                )

        # Step 2: ML analysis (if no critical match OR to confirm)
        ml_score = None
        if event_metadata:
            ml_score = self.ml.predict(event_metadata)

        # Step 3: Decision fusion
        action, confidence, threat_level, reasoning = self._make_decision(
            hyperscan_matches,
            ml_score
        )

        latency_ms = (time.time() - start_time) * 1000

        return FusionResult(
            action=action,
            confidence=confidence,
            threat_level=threat_level,
            hyperscan_matches=hyperscan_matches,
            ml_score=ml_score,
            reasoning=reasoning,
            latency_ms=latency_ms,
            metadata={
                "fast_path": False,
                "hyperscan_matches": len(hyperscan_matches),
                "ml_anomaly": ml_score.is_anomaly if ml_score else False
            }
        )

    def _make_decision(
        self,
        hyperscan_matches: List[Match],
        ml_score: Optional[ThreatScore]
    ) -> Tuple[ThreatAction, float, str, str]:
        """
        Make final decision based on all signals.

        Returns:
            (action, confidence, threat_level, reasoning)
        """
        # Case 1: Hyperscan + ML both detect
        if hyperscan_matches and ml_score and ml_score.is_anomaly:
            highest_severity = self.hyperscan.get_highest_severity(hyperscan_matches)

            # Both agree on high threat
            combined_confidence = min(1.0, ml_score.anomaly_score + 0.3)

            if combined_confidence >= self.thresholds["combined_block"]:
                return (
                    ThreatAction.BLOCK,
                    combined_confidence,
                    highest_severity,
                    f"Pattern match ({highest_severity}) + ML anomaly (score={ml_score.anomaly_score:.2f})"
                )
            else:
                return (
                    ThreatAction.INVESTIGATE,
                    combined_confidence,
                    highest_severity,
                    f"Pattern match + ML anomaly, confidence below block threshold"
                )

        # Case 2: Only Hyperscan detects
        if hyperscan_matches:
            highest_severity = self.hyperscan.get_highest_severity(hyperscan_matches)
            severity_confidence = {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.5,
                "low": 0.3
            }.get(highest_severity, 0.3)

            if highest_severity in ["critical", "high"]:
                return (
                    ThreatAction.BLOCK,
                    severity_confidence,
                    highest_severity,
                    f"Pattern match detected: {hyperscan_matches[0].metadata.get('description', 'Unknown')}"
                )
            else:
                return (
                    ThreatAction.INVESTIGATE,
                    severity_confidence,
                    highest_severity,
                    f"Low/medium severity pattern match"
                )

        # Case 3: Only ML detects
        if ml_score and ml_score.is_anomaly:
            if ml_score.anomaly_score >= self.thresholds["ml_high_confidence"]:
                return (
                    ThreatAction.INVESTIGATE,  # ML alone doesn't block
                    ml_score.anomaly_score,
                    "medium",
                    f"ML anomaly detection (score={ml_score.anomaly_score:.2f})"
                )
            else:
                return (
                    ThreatAction.INVESTIGATE,
                    ml_score.anomaly_score,
                    "low",
                    f"ML weak anomaly (score={ml_score.anomaly_score:.2f})"
                )

        # Case 4: Nothing detected
        return (
            ThreatAction.ALLOW,
            0.95,  # High confidence in clean traffic
            "benign",
            "No threats detected"
        )

    def update_thresholds(self, thresholds: Dict[str, float]):
        """Update decision thresholds (for tuning)"""
        self.thresholds.update(thresholds)
        logger.info(f"Thresholds updated: {self.thresholds}")

    def get_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            "hyperscan": self.hyperscan.get_stats(),
            "thresholds": self.thresholds
        }


# Test
if __name__ == "__main__":
    import json
    import tempfile
    from pathlib import Path
    import numpy as np

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("FUSION ENGINE TEST")
    print("="*80 + "\n")

    # Setup Hyperscan
    test_patterns = [
        {
            "id": 1,
            "pattern": "malware.*\\.exe",
            "flags": ["CASELESS"],
            "metadata": {"severity": "critical", "category": "malware"}
        },
        {
            "id": 2,
            "pattern": "SELECT.*FROM",
            "flags": ["CASELESS"],
            "metadata": {"severity": "high", "category": "sqli"}
        }
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_patterns, f)
        patterns_file = Path(f.name)

    hyperscan = HyperscanMatcher(patterns_file)

    # Setup ML
    np.random.seed(42)
    normal_events = []
    for i in range(500):
        event = {
            "packet_size": np.random.normal(500, 100),
            "packet_count": np.random.randint(10, 100),
            "bytes_sent": np.random.normal(5000, 1000),
            "protocol": "TCP",
            "payload_entropy": np.random.uniform(3, 5),
        }
        normal_events.append(event)

    ml_engine = FastMLEngine()
    ml_engine.train(normal_events)

    # Create fusion engine
    fusion = FusionEngine(hyperscan, ml_engine)

    # Test scenarios
    test_cases = [
        {
            "name": "Critical malware pattern",
            "data": b"Download malware.exe now!",
            "event": normal_events[0]
        },
        {
            "name": "SQL injection attempt",
            "data": b"SELECT * FROM users WHERE 1=1",
            "event": normal_events[0]
        },
        {
            "name": "ML anomaly (no pattern)",
            "data": b"Normal looking data",
            "event": {
                "packet_size": 50000,  # Anomalous
                "packet_count": 10000,
                "bytes_sent": 1000000,
                "protocol": "ICMP",
                "payload_entropy": 7.9,
            }
        },
        {
            "name": "Clean traffic",
            "data": b"Normal HTTPS request",
            "event": normal_events[1]
        }
    ]

    print("Testing fusion logic:\n")

    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"  Data: {test['data'].decode('utf-8', errors='ignore')}")

        result = fusion.analyze(test["data"], test["event"])

        print(f"  → ACTION: {result.action}")
        print(f"  → Confidence: {result.confidence:.2f}")
        print(f"  → Threat level: {result.threat_level}")
        print(f"  → Reasoning: {result.reasoning}")
        print(f"  → Latency: {result.latency_ms:.2f}ms")
        print()

    # Performance stats
    print("="*80)
    print("PERFORMANCE")
    print("="*80)
    stats = fusion.get_stats()
    print(f"Hyperscan avg scan time: {stats['hyperscan']['avg_scan_time_ms']:.2f}ms")
    print(f"Thresholds: {stats['thresholds']}")

    # Cleanup
    patterns_file.unlink()

    print("\n" + "="*80)
    print("FUSION ENGINE TEST COMPLETE!")
    print("="*80 + "\n")
