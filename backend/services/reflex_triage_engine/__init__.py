"""Reflex Triage Engine (RTE) - Ultra-fast threat detection <50ms

Bio-inspired reflex system for immediate threat response.
Combines signature matching, anomaly detection, and predictive coding.

Components:
- HyperscanEngine: Pattern matching with Intel Hyperscan (10-50ms)
- FastAnomalyDetector: Isolation Forest ML detection (<10ms)
- ReflexFusionEngine: Combines detections for decision making
- AutonomousResponseEngine: Executes response playbooks

Performance: p99 latency <50ms for 50k+ signatures
"""

from .hyperscan_engine import HyperscanEngine, SignatureMatch
from .fast_anomaly_detector import FastAnomalyDetector, AnomalyResult
from .reflex_fusion import ReflexFusionEngine, ThreatDecision, ReflexResult
from .autonomous_response import AutonomousResponseEngine, PlaybookAction, ActionResult

__all__ = [
    # Signature matching
    'HyperscanEngine',
    'SignatureMatch',

    # Anomaly detection
    'FastAnomalyDetector',
    'AnomalyResult',

    # Fusion
    'ReflexFusionEngine',
    'ThreatDecision',
    'ReflexResult',

    # Autonomous response
    'AutonomousResponseEngine',
    'PlaybookAction',
    'ActionResult',
]
