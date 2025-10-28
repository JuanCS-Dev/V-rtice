"""Cliente assíncrono para o Linfonodo Digital (Immunis API)."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Dict, Optional
import uuid

import httpx

from ..config import get_settings, TegumentarSettings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ThreatValidation:
    """Resultado da validação do Linfonodo."""

    confirmed: bool
    threat_id: Optional[str] = None
    severity: Optional[str] = None
    confidence: float = 0.0
    extra: Optional[Dict[str, Any]] = None


class LymphnodeAPI:
    """Cliente HTTP para interação com o Linfonodo/Immunis."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._timeout = httpx.Timeout(10.0, connect=5.0)

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self._settings.lymphnode_api_key:
            headers["Authorization"] = f"Bearer {self._settings.lymphnode_api_key}"
        return headers

    async def submit_threat(self, threat_report: Dict[str, Any]) -> ThreatValidation:
        """Submete ameaça para validação e orquestração imune."""

        threat_id = (
            threat_report.get("threat_id") or f"teg-threat-{uuid.uuid4().hex[:12]}"
        )
        severity = threat_report.get("severity") or self._classify_severity(
            threat_report.get("anomaly_score", 0.0)
        )
        payload = {
            "threat_id": threat_id,
            "threat_type": threat_report.get("threat_type", "anomaly"),
            "severity": severity,
            "details": threat_report,
            "source": threat_report.get("source", "tegumentar"),
        }

        start = time.perf_counter()
        async with httpx.AsyncClient(
            base_url=str(self._settings.lymphnode_endpoint), timeout=self._timeout
        ) as client:
            response = await client.post(
                "/threat_alert",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            body = response.json()
            latency = time.perf_counter() - start
            confidence = float(threat_report.get("anomaly_score", 0.9))
            confidence = max(0.0, min(1.0, confidence))
            immunis_response = body.get("immunis_response")
            logger.info(
                "Linfonodo confirmou ameaça %s (severity=%s, confidence=%.2f)",
                threat_id,
                severity,
                confidence,
            )
            return ThreatValidation(
                confirmed=True,
                threat_id=threat_id,
                severity=severity,
                confidence=confidence,
                extra={
                    "immunis_response": immunis_response,
                    "raw": body,
                    "latency": latency,
                },
            )

    async def broadcast_vaccination(self, rule: Dict[str, Any]) -> bool:
        """Dispara resposta imune para disseminar nova assinatura."""

        payload = {
            "response_type": "b_cell_vaccination",
            "target_id": rule.get("id", f"rule-{uuid.uuid4().hex[:10]}"),
            "parameters": {"rule": rule},
        }

        async with httpx.AsyncClient(
            base_url=str(self._settings.lymphnode_endpoint), timeout=self._timeout
        ) as client:
            response = await client.post(
                "/trigger_immune_response",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            logger.info("Vacinação enviada para Linfonodo: %s", payload["target_id"])
            return True

    @staticmethod
    def _classify_severity(score: float) -> str:
        if score >= 0.98:
            return "critical"
        if score >= 0.9:
            return "high"
        if score >= 0.75:
            return "medium"
        return "low"


__all__ = ["LymphnodeAPI", "ThreatValidation"]
