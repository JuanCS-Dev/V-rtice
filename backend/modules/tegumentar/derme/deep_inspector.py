"""Deep packet inspection combining signatures and anomaly detection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..config import TegumentarSettings, get_settings
from .ml.anomaly_detector import AnomalyDetector
from .ml.feature_extractor import FeatureExtractor
from .signature_engine import Signature, SignatureEngine
from .stateful_inspector import FlowObservation, InspectorAction

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InspectionResult:
    action: InspectorAction
    confidence: float
    reason: str
    signature: Optional[Signature] = None
    anomaly_score: Optional[float] = None


class DeepPacketInspector:
    """Performs DPI using signatures + ML anomaly detection."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._signature_engine = SignatureEngine(self._settings)
        self._feature_extractor = FeatureExtractor()
        self._anomaly_detector = AnomalyDetector(self._settings)
        self._signature_engine.load()
        self._anomaly_detector.load()

    def inspect(self, observation: FlowObservation, payload: bytes) -> InspectionResult:
        signature = self._signature_engine.match(payload)
        if signature:
            action = InspectorAction.DROP if signature.action == "block" else InspectorAction.INSPECT_DEEP
            logger.info("Signature %s matched for %s:%d", signature.name, observation.src_ip, observation.src_port)
            return InspectionResult(
                action=action,
                confidence=0.99,
                reason=f"Signature match: {signature.name}",
                signature=signature,
            )

        features = self._feature_extractor.transform(observation, payload)
        score = self._anomaly_detector.score(features)
        if score > 0.7:
            logger.warning(
                "Anomalous flow detected score=%.3f src=%s dst=%s",
                score,
                observation.src_ip,
                observation.dst_ip,
            )
            return InspectionResult(
                action=InspectorAction.INSPECT_DEEP,
                confidence=min(score, 0.99),
                reason="Anomaly detector high score",
                anomaly_score=score,
            )

        return InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="No signature match and anomaly score below threshold",
            anomaly_score=score,
        )


__all__ = ["DeepPacketInspector", "InspectionResult"]
