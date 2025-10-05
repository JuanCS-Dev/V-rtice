"""Reflex Fusion Engine - Combines Hyperscan + IF + VAE for decision making

Hybrid detection combining:
1. Hyperscan signature matching (known threats)
2. Isolation Forest anomaly detection (behavioral anomalies)
3. VAE reconstruction error (L1 predictive coding - if available)

Decision tree: BLOCK / INVESTIGATE / ALLOW
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .hyperscan_engine import HyperscanEngine, SignatureMatch
from .fast_anomaly_detector import FastAnomalyDetector, AnomalyResult

logger = logging.getLogger(__name__)


class ThreatDecision(Enum):
    """Threat triage decision."""
    BLOCK = "BLOCK"  # Immediate block
    INVESTIGATE = "INVESTIGATE"  # Send to deep analysis
    ALLOW = "ALLOW"  # Allow through


@dataclass
class ReflexResult:
    """Result from reflex triage."""
    decision: ThreatDecision
    confidence: float  # 0.0-1.0
    threat_score: float  # 0.0-1.0 (higher = more threatening)
    detections: Dict[str, any]  # Individual detector results
    reasoning: List[str]  # Human-readable reasoning
    latency_ms: float


class ReflexFusionEngine:
    """Fuses multiple detection methods for ultra-fast triage.

    Decision logic:
    - Any CRITICAL signature match → BLOCK
    - High anomaly score + signature match → BLOCK
    - Moderate anomaly → INVESTIGATE
    - Everything else → ALLOW
    """

    def __init__(
        self,
        hyperscan_engine: HyperscanEngine,
        anomaly_detector: FastAnomalyDetector,
        vae_layer: Optional[any] = None  # L1 from predictive coding
    ):
        """Initialize reflex fusion engine.

        Args:
            hyperscan_engine: Signature matching engine
            anomaly_detector: Fast anomaly detector
            vae_layer: Optional VAE from Layer 1 (predictive coding)
        """
        self.hyperscan = hyperscan_engine
        self.anomaly = anomaly_detector
        self.vae = vae_layer

        # Decision thresholds
        self.thresholds = {
            'critical_signature': 1.0,  # Any critical signature = BLOCK
            'block_score': 0.85,  # Combined score for BLOCK
            'investigate_score': 0.60,  # Combined score for INVESTIGATE
            'anomaly_high': 0.80,
            'anomaly_medium': 0.50
        }

        logger.info("ReflexFusionEngine initialized")

    def triage(
        self,
        event_data: bytes,
        event_metadata: Dict
    ) -> ReflexResult:
        """Perform reflex triage on event.

        Args:
            event_data: Raw event data (for signature matching)
            event_metadata: Event metadata dict (for anomaly detection)

        Returns:
            ReflexResult with decision and reasoning
        """
        triage_start = time.time()

        detections = {}
        reasoning = []
        threat_score = 0.0

        # 1. Hyperscan signature matching
        sig_start = time.time()
        signature_matches = self.hyperscan.scan(event_data, max_matches=10)
        sig_time = (time.time() - sig_start) * 1000

        detections['signatures'] = {
            'matches': [
                {
                    'name': m.signature_name,
                    'severity': m.severity,
                    'category': m.category
                }
                for m in signature_matches
            ],
            'count': len(signature_matches),
            'latency_ms': sig_time
        }

        # Check for critical signatures
        critical_sigs = [m for m in signature_matches if m.severity == 'CRITICAL']
        if critical_sigs:
            decision = ThreatDecision.BLOCK
            confidence = 0.99
            threat_score = 1.0
            reasoning.append(f"CRITICAL signature detected: {critical_sigs[0].signature_name}")

            latency = (time.time() - triage_start) * 1000

            return ReflexResult(
                decision=decision,
                confidence=confidence,
                threat_score=threat_score,
                detections=detections,
                reasoning=reasoning,
                latency_ms=latency
            )

        # 2. Anomaly detection
        anom_start = time.time()
        anomaly_result = self.anomaly.detect(event_metadata)
        anom_time = (time.time() - anom_start) * 1000

        detections['anomaly'] = {
            'is_anomaly': anomaly_result.is_anomaly,
            'score': anomaly_result.anomaly_score,
            'top_features': anomaly_result.feature_contributions,
            'latency_ms': anom_time
        }

        # 3. VAE prediction error (if available)
        vae_score = 0.0
        if self.vae:
            try:
                vae_start = time.time()
                # Assuming VAE expects feature vector
                vae_input = self.anomaly.extract_features(event_metadata)
                vae_result = self.vae.predict(vae_input)
                vae_time = (time.time() - vae_start) * 1000

                vae_score = vae_result.get('anomaly_score', 0.0)

                detections['vae'] = {
                    'is_anomalous': vae_result.get('is_anomalous', False),
                    'score': vae_score,
                    'latency_ms': vae_time
                }

                if vae_result.get('is_anomalous'):
                    reasoning.append(f"VAE prediction error high ({vae_score:.2f})")

            except Exception as e:
                logger.warning(f"VAE detection failed: {e}")
                detections['vae'] = {'error': str(e)}

        # 4. Compute combined threat score
        weights = {
            'signatures': 0.50,
            'anomaly': 0.35,
            'vae': 0.15
        }

        # Signature score (weighted by severity)
        sig_score = 0.0
        if signature_matches:
            severity_weights = {'CRITICAL': 1.0, 'HIGH': 0.75, 'MEDIUM': 0.5, 'LOW': 0.25}
            sig_score = max(
                severity_weights.get(m.severity, 0.25) for m in signature_matches
            )
            reasoning.append(f"{len(signature_matches)} signature(s) matched")

        # Combined score
        threat_score = (
            weights['signatures'] * sig_score +
            weights['anomaly'] * anomaly_result.anomaly_score +
            weights['vae'] * vae_score
        )

        # 5. Make decision
        decision, confidence = self._make_decision(
            threat_score,
            signature_matches,
            anomaly_result,
            reasoning
        )

        latency = (time.time() - triage_start) * 1000

        # Performance warning
        if latency > 50:
            logger.warning(f"Reflex triage exceeded 50ms: {latency:.1f}ms")

        logger.debug(f"Triage: {decision.value} (score={threat_score:.2f}, latency={latency:.1f}ms)")

        return ReflexResult(
            decision=decision,
            confidence=confidence,
            threat_score=threat_score,
            detections=detections,
            reasoning=reasoning,
            latency_ms=latency
        )

    def _make_decision(
        self,
        threat_score: float,
        signatures: List[SignatureMatch],
        anomaly: AnomalyResult,
        reasoning: List[str]
    ) -> Tuple[ThreatDecision, float]:
        """Make triage decision based on combined evidence.

        Args:
            threat_score: Combined threat score (0-1)
            signatures: Signature matches
            anomaly: Anomaly detection result
            reasoning: Reasoning list to append to

        Returns:
            (decision, confidence)
        """
        # Rule 1: High threat score → BLOCK
        if threat_score >= self.thresholds['block_score']:
            reasoning.append(f"High threat score ({threat_score:.2f})")
            return ThreatDecision.BLOCK, 0.90

        # Rule 2: HIGH severity signature + anomaly → BLOCK
        high_sigs = [s for s in signatures if s.severity == 'HIGH']
        if high_sigs and anomaly.anomaly_score > self.thresholds['anomaly_high']:
            reasoning.append("HIGH signature + anomaly detected")
            return ThreatDecision.BLOCK, 0.85

        # Rule 3: Moderate threat score → INVESTIGATE
        if threat_score >= self.thresholds['investigate_score']:
            reasoning.append(f"Moderate threat score ({threat_score:.2f})")
            return ThreatDecision.INVESTIGATE, 0.70

        # Rule 4: Anomaly alone (medium) → INVESTIGATE
        if anomaly.is_anomaly and anomaly.anomaly_score > self.thresholds['anomaly_medium']:
            reasoning.append(f"Anomaly detected ({anomaly.anomaly_score:.2f})")
            return ThreatDecision.INVESTIGATE, 0.65

        # Rule 5: Signature alone (MEDIUM/LOW) → INVESTIGATE
        if signatures:
            reasoning.append(f"Signature match (low severity)")
            return ThreatDecision.INVESTIGATE, 0.60

        # Default: ALLOW
        reasoning.append("No significant threat detected")
        return ThreatDecision.ALLOW, 0.50

    def adjust_thresholds(self, thresholds: Dict[str, float]):
        """Adjust decision thresholds dynamically.

        Args:
            thresholds: Dictionary of threshold values to update
        """
        self.thresholds.update(thresholds)
        logger.info(f"Thresholds updated: {thresholds}")

    def get_statistics(self) -> Dict:
        """Get fusion engine statistics."""
        return {
            'thresholds': self.thresholds,
            'hyperscan_stats': self.hyperscan.get_statistics(),
            'anomaly_stats': self.anomaly.get_statistics(),
            'vae_available': self.vae is not None
        }
