"""Cytokine Aggregator - Regional Cytokine Processing

Extracted from LinfonodoDigital as part of FASE 3 Desacoplamento.

This module implements cytokine aggregation, filtering, and temperature impact
calculation. It processes cytokine signals from agents and translates them into
homeostatic responses (temperature adjustments, threat tracking, escalation).

Responsibilities:
- Cytokine validation via Pydantic
- Area-based filtering (regional vs global)
- Temperature impact calculation (pro-inflammatory vs anti-inflammatory)
- Threat detection tracking
- Critical cytokine escalation (to global lymphnode/MAXIMUS)

Biological Inspiration:
-----------------------
In biological systems, cytokines act as immune system messengers:
- Pro-inflammatory cytokines (IL-1, IL-6, TNF-α) → increase temperature (fever)
- Anti-inflammatory cytokines (IL-10, TGF-β) → reduce temperature
- Regional lymph nodes aggregate signals from local tissue
- Critical threats trigger systemic responses (cortisol release)

This digital implementation mirrors these biological mechanisms, processing
cytokine streams to regulate immune system homeostasis.

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import ValidationError

from active_immune_core.coordination.validators import validate_cytokine

logger = logging.getLogger(__name__)


class CytokineType(str, Enum):
    """Cytokine types recognized by the system."""

    IL1 = "IL1"  # Pro-inflammatory
    IL6 = "IL6"  # Pro-inflammatory
    IL8 = "IL8"  # Pro-inflammatory (chemokine)
    IL10 = "IL10"  # Anti-inflammatory
    IL12 = "IL12"  # Pro-inflammatory (Th1 response)
    TNF = "TNF"  # Pro-inflammatory (Tumor Necrosis Factor)
    IFNgamma = "IFNgamma"  # Pro-inflammatory (antiviral)
    TGFbeta = "TGFbeta"  # Anti-inflammatory (regulatory)


class EventType(str, Enum):
    """Event types extracted from cytokine payload."""

    THREAT_DETECTED = "ameaca_detectada"
    NEUTRALIZATION_SUCCESS = "neutralizacao_sucesso"
    NK_CYTOTOXICITY = "nk_cytotoxicity"
    NEUTROPHIL_NET = "neutrophil_net_formation"


@dataclass
class ProcessingResult:
    """Result of cytokine processing.

    Attributes:
        temperature_delta: Temperature adjustment (positive = increase, negative = decrease)
        threat_detected: Whether this cytokine represents a threat
        threat_id: Threat identifier (if threat detected)
        neutralization: Whether this cytokine represents a neutralization
        should_escalate: Whether this cytokine should be escalated to global
        metadata: Additional processing metadata
    """

    temperature_delta: float = 0.0
    threat_detected: bool = False
    threat_id: Optional[str] = None
    neutralization: bool = False
    should_escalate: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class CytokineAggregator:
    """Processes cytokine signals and calculates immune responses.

    This class implements cytokine aggregation logic extracted from
    LinfonodoDigital, including validation, filtering, temperature impact
    calculation, and escalation logic.

    Attributes:
        area: Network area this aggregator is responsible for
        nivel: Hierarchy level (local, regional, global)
        escalation_priority_threshold: Min priority to escalate to global (default 9)

    Example:
        >>> aggregator = CytokineAggregator(area="network-zone-1", nivel="regional")
        >>> result = await aggregator.process_cytokine(cytokine_data)
        >>> if result.threat_detected:
        ...     logger.warning(f"Threat detected: {result.threat_id}")
    """

    # Pro-inflammatory cytokines (increase temperature)
    PRO_INFLAMMATORY = {CytokineType.IL1, CytokineType.IL6, CytokineType.TNF, CytokineType.IL8}

    # Anti-inflammatory cytokines (decrease temperature)
    ANTI_INFLAMMATORY = {CytokineType.IL10, CytokineType.TGFbeta}

    # Temperature deltas per cytokine type
    TEMPERATURE_INCREASE = 0.2  # °C for pro-inflammatory
    TEMPERATURE_DECREASE = -0.1  # °C for anti-inflammatory

    def __init__(
        self,
        area: str = "default",
        nivel: str = "local",
        escalation_priority_threshold: int = 9,
    ):
        """Initialize CytokineAggregator.

        Args:
            area: Network area (subnet, zone, datacenter)
            nivel: Hierarchy level (local, regional, global)
            escalation_priority_threshold: Min priority for escalation (0-10)
        """
        self.area = area
        self.nivel = nivel
        self.escalation_priority_threshold = escalation_priority_threshold

        # Statistics
        self._total_processed = 0
        self._total_threats = 0
        self._total_neutralizations = 0
        self._total_escalated = 0
        self._total_validation_errors = 0

        logger.info(
            f"CytokineAggregator initialized: "
            f"area={area}, nivel={nivel}, "
            f"escalation_threshold={escalation_priority_threshold}"
        )

    async def validate_and_parse(
        self,
        cytokine_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Validate cytokine via Pydantic and return parsed dict.

        EXTRACTED from lymphnode.py:_aggregate_cytokines() (lines 644-649)

        Args:
            cytokine_data: Raw cytokine data from Kafka

        Returns:
            Validated cytokine dict, or None if validation fails
        """
        try:
            validated = validate_cytokine(cytokine_data)
            return validated.model_dump()

        except ValidationError as e:
            logger.warning(f"Invalid cytokine received, skipping: {e}")
            self._total_validation_errors += 1
            return None

    async def should_process_for_area(
        self,
        cytokine: Dict[str, Any],
    ) -> bool:
        """Determine if cytokine should be processed based on area.

        EXTRACTED from lymphnode.py:_aggregate_cytokines() (line 652)

        Args:
            cytokine: Validated cytokine dict

        Returns:
            True if should process, False otherwise
        """
        # Global level processes all cytokines
        if self.nivel == "global":
            return True

        # Local/regional only process cytokines from their area
        area_alvo = cytokine.get("area_alvo")
        return area_alvo == self.area

    async def process_cytokine(
        self,
        cytokine: Dict[str, Any],
    ) -> ProcessingResult:
        """Process cytokine and calculate immune response.

        EXTRACTED from lymphnode.py:_processar_citocina_regional() (lines 670-719)

        Args:
            cytokine: Validated cytokine dict

        Returns:
            ProcessingResult with temperature delta, threat info, escalation
        """
        self._total_processed += 1

        tipo_str = cytokine.get("tipo")
        payload = cytokine.get("payload", {})
        prioridade = cytokine.get("prioridade", 0)

        result = ProcessingResult()

        # Calculate temperature impact
        result.temperature_delta = await self._calculate_temperature_impact(tipo_str)

        # Extract threat information
        evento = payload.get("evento")

        if evento == EventType.THREAT_DETECTED.value or payload.get("is_threat"):
            result.threat_detected = True
            self._total_threats += 1

            # Extract threat ID from various possible locations
            threat_id = payload.get("alvo", {}).get("id") or payload.get("host_id") or payload.get("threat_id")
            result.threat_id = threat_id

        # Check for neutralization events
        elif evento in [
            EventType.NEUTRALIZATION_SUCCESS.value,
            EventType.NK_CYTOTOXICITY.value,
            EventType.NEUTROPHIL_NET.value,
        ]:
            result.neutralization = True
            self._total_neutralizations += 1

        # Determine if should escalate to global
        result.should_escalate = await self._should_escalate_to_global(cytokine, prioridade)

        if result.should_escalate:
            self._total_escalated += 1

        # Add metadata
        result.metadata = {
            "tipo": tipo_str,
            "prioridade": prioridade,
            "evento": evento,
            "emissor_id": cytokine.get("emissor_id"),
            "timestamp": cytokine.get("timestamp"),
        }

        return result

    async def _calculate_temperature_impact(
        self,
        cytokine_type: str,
    ) -> float:
        """Calculate temperature delta for cytokine type.

        EXTRACTED from lymphnode.py:_processar_citocina_regional() (lines 686-693)

        Args:
            cytokine_type: Cytokine type string (IL1, IL6, etc.)

        Returns:
            Temperature delta in °C
        """
        try:
            tipo_enum = CytokineType(cytokine_type)

            if tipo_enum in self.PRO_INFLAMMATORY:
                return self.TEMPERATURE_INCREASE

            elif tipo_enum in self.ANTI_INFLAMMATORY:
                return self.TEMPERATURE_DECREASE

        except (ValueError, KeyError):
            logger.debug(f"Unknown cytokine type: {cytokine_type}")

        return 0.0  # Neutral cytokines don't affect temperature

    async def _should_escalate_to_global(
        self,
        cytokine: Dict[str, Any],
        prioridade: int,
    ) -> bool:
        """Determine if cytokine should be escalated to global lymphnode.

        EXTRACTED from lymphnode.py:_processar_citocina_regional() (line 712)

        Args:
            cytokine: Cytokine dict
            prioridade: Priority level (0-10)

        Returns:
            True if should escalate, False otherwise
        """
        # Don't escalate if already at global level
        if self.nivel == "global":
            return False

        # Escalate if priority exceeds threshold
        return prioridade >= self.escalation_priority_threshold

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics.

        Returns:
            Dict with processing stats
        """
        return {
            "area": self.area,
            "nivel": self.nivel,
            "escalation_threshold": self.escalation_priority_threshold,
            "total_processed": self._total_processed,
            "total_threats": self._total_threats,
            "total_neutralizations": self._total_neutralizations,
            "total_escalated": self._total_escalated,
            "total_validation_errors": self._total_validation_errors,
            "threat_rate": (self._total_threats / self._total_processed if self._total_processed > 0 else 0.0),
            "escalation_rate": (self._total_escalated / self._total_processed if self._total_processed > 0 else 0.0),
        }

    def reset_stats(self) -> None:
        """Reset all statistics counters."""
        self._total_processed = 0
        self._total_threats = 0
        self._total_neutralizations = 0
        self._total_escalated = 0
        self._total_validation_errors = 0
        logger.debug("Cytokine aggregator stats reset")

    def __repr__(self) -> str:
        return (
            f"CytokineAggregator("
            f"area={self.area}, "
            f"nivel={self.nivel}, "
            f"processed={self._total_processed}, "
            f"threats={self._total_threats})"
        )
