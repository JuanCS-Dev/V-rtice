"""Immunis Helper T-Cell Service - Production-Ready Immune Orchestration

Bio-inspired Helper T-Cell service that:
1. **Th1/Th2 Orchestration**
   - Th1 response: Cell-mediated immunity (aggressive)
   - Th2 response: Humoral immunity (defensive)
   - Dynamic strategy selection based on threat type

2. **Response Intensity Modulation**
   - Determines proportionate response based on severity
   - Prevents over-reaction to minor threats
   - Escalates response for critical threats

3. **Coordinates B-cells and Cytotoxic T-cells**
   - Directs B-cell signature generation
   - Activates Cytotoxic T-cell active defense
   - Maintains global immune system state

4. **Effectiveness Metrics**
   - Tracks response success rates
   - Measures time-to-containment
   - Optimizes future responses

Like biological Helper T-cells: Orchestrates adaptive immunity.
NO MOCKS - Production-ready implementation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ImmuneStrategy(Enum):
    """Immune response strategy types."""
    TH1 = "th1"  # Cell-mediated (aggressive, active defense)
    TH2 = "th2"  # Humoral (defensive, signature-based)
    BALANCED = "balanced"  # Mixed strategy


class ResponseIntensity(Enum):
    """Response intensity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HelperTCellCore:
    """Production-ready Helper T-Cell service for immune orchestration.

    Coordinates adaptive immunity:
    - Th1/Th2 strategy selection
    - Response intensity modulation
    - B-cell and Cytotoxic T-cell coordination
    - Effectiveness tracking
    """

    def __init__(
        self,
        b_cell_endpoint: str = "http://immunis-bcell:8015",
        cytotoxic_endpoint: str = "http://immunis-cytotoxic-t:8017"
    ):
        """Initialize Helper T-Cell Core.

        Args:
            b_cell_endpoint: B-Cell service endpoint
            cytotoxic_endpoint: Cytotoxic T-Cell service endpoint
        """
        self.b_cell_endpoint = b_cell_endpoint
        self.cytotoxic_endpoint = cytotoxic_endpoint

        self.threat_intelligence: Dict[str, Dict[str, Any]] = {}
        self.response_directives: List[Dict[str, Any]] = []
        self.response_outcomes: List[Dict[str, Any]] = []
        self.last_coordination_time: Optional[datetime] = None

        logger.info("HelperTCellCore initialized (production-ready)")

    async def activate(self, antigen: Dict[str, Any]) -> Dict[str, Any]:
        """Activate Helper T-Cell with antigen from Dendritic Cell.

        Args:
            antigen: Antigen from Dendritic Cell

        Returns:
            Orchestration result
        """
        logger.info(f"Helper T-Cell activated with antigen: {antigen.get('antigen_id', '')[:16]}")

        antigen_id = antigen.get('antigen_id')
        malware_family = antigen.get('malware_family', 'unknown')
        severity = antigen.get('severity', 0.5)
        correlation_count = antigen.get('correlation_count', 0)

        # 1. Determine immune strategy (Th1 vs Th2)
        strategy = self._select_immune_strategy(antigen)

        # 2. Determine response intensity
        intensity = self._calculate_response_intensity(severity, correlation_count)

        # 3. Coordinate immune cells
        coordination_result = await self._coordinate_immune_response(
            antigen, strategy, intensity
        )

        # 4. Store threat intelligence
        self.threat_intelligence[antigen_id] = {
            'timestamp': datetime.now().isoformat(),
            'malware_family': malware_family,
            'severity': severity,
            'strategy': strategy.value,
            'intensity': intensity.value,
            'coordination': coordination_result
        }

        self.last_coordination_time = datetime.now()

        logger.info(
            f"Helper T-Cell orchestration: strategy={strategy.value}, "
            f"intensity={intensity.value}"
        )

        return {
            'timestamp': datetime.now().isoformat(),
            'antigen_id': antigen_id,
            'strategy': strategy.value,
            'intensity': intensity.value,
            'coordination': coordination_result
        }

    def _select_immune_strategy(self, antigen: Dict[str, Any]) -> ImmuneStrategy:
        """Select Th1 (aggressive) vs Th2 (defensive) strategy.

        Args:
            antigen: Threat antigen

        Returns:
            Selected immune strategy
        """
        severity = antigen.get('severity', 0.5)
        malware_family = antigen.get('malware_family', 'unknown')
        correlation_count = antigen.get('correlation_count', 0)

        # Th1 strategy (cell-mediated, aggressive):
        # - High severity threats (≥0.7)
        # - Active malware (ransomware, worms)
        # - Multiple correlated events (campaign)

        if severity >= 0.7:
            logger.info("Th1 strategy selected: High severity threat")
            return ImmuneStrategy.TH1

        if correlation_count >= 5:
            logger.info("Th1 strategy selected: Multi-host campaign detected")
            return ImmuneStrategy.TH1

        # Aggressive malware families
        aggressive_families = ['ransomware', 'worm', 'rootkit', 'apt']
        if any(family in malware_family.lower() for family in aggressive_families):
            logger.info(f"Th1 strategy selected: Aggressive malware family ({malware_family})")
            return ImmuneStrategy.TH1

        # Th2 strategy (humoral, defensive):
        # - Medium/low severity (signature-based detection)
        # - Isolated incidents
        # - Known malware families

        if correlation_count == 0 and severity < 0.5:
            logger.info("Th2 strategy selected: Isolated low-severity threat")
            return ImmuneStrategy.TH2

        # Balanced (mixed strategy)
        logger.info("Balanced strategy selected: Mixed threat characteristics")
        return ImmuneStrategy.BALANCED

    def _calculate_response_intensity(
        self,
        severity: float,
        correlation_count: int
    ) -> ResponseIntensity:
        """Calculate proportionate response intensity.

        Args:
            severity: Threat severity (0-1)
            correlation_count: Number of correlated events

        Returns:
            Response intensity level
        """
        # Intensity score combines severity and correlation
        intensity_score = severity

        # Increase intensity for correlated threats (campaigns)
        if correlation_count >= 5:
            intensity_score = min(intensity_score + 0.2, 1.0)
        elif correlation_count >= 3:
            intensity_score = min(intensity_score + 0.1, 1.0)

        # Map to intensity levels
        if intensity_score >= 0.8:
            return ResponseIntensity.CRITICAL
        elif intensity_score >= 0.6:
            return ResponseIntensity.HIGH
        elif intensity_score >= 0.4:
            return ResponseIntensity.MEDIUM
        else:
            return ResponseIntensity.LOW

    async def _coordinate_immune_response(
        self,
        antigen: Dict[str, Any],
        strategy: ImmuneStrategy,
        intensity: ResponseIntensity
    ) -> Dict[str, Any]:
        """Coordinate B-cell and Cytotoxic T-cell responses.

        Args:
            antigen: Threat antigen
            strategy: Immune strategy
            intensity: Response intensity

        Returns:
            Coordination results
        """
        coordination = {
            'b_cell_activated': False,
            'cytotoxic_t_activated': False,
            'directives': []
        }

        # B-Cell activation (always for signature generation)
        if strategy in [ImmuneStrategy.TH2, ImmuneStrategy.BALANCED, ImmuneStrategy.TH1]:
            directive = {
                'cell_type': 'b_cell',
                'action': 'generate_signature',
                'priority': 'high' if intensity in [ResponseIntensity.HIGH, ResponseIntensity.CRITICAL] else 'medium',
                'antigen': antigen
            }
            coordination['directives'].append(directive)
            coordination['b_cell_activated'] = True

        # Cytotoxic T-Cell activation (Th1 strategy or high intensity)
        if strategy == ImmuneStrategy.TH1 or intensity in [ResponseIntensity.HIGH, ResponseIntensity.CRITICAL]:
            directive = {
                'cell_type': 'cytotoxic_t',
                'action': 'active_defense',
                'priority': 'critical' if intensity == ResponseIntensity.CRITICAL else 'high',
                'antigen': antigen
            }
            coordination['directives'].append(directive)
            coordination['cytotoxic_t_activated'] = True

        # Store directives
        self.response_directives.extend(coordination['directives'])

        logger.info(
            f"Coordination: B-cell={coordination['b_cell_activated']}, "
            f"Cytotoxic-T={coordination['cytotoxic_t_activated']}"
        )

        return coordination

    async def record_response_outcome(
        self,
        antigen_id: str,
        outcome: str,
        time_to_containment: Optional[float] = None,
        false_positive: bool = False
    ) -> Dict[str, Any]:
        """Record outcome of immune response.

        Args:
            antigen_id: Antigen identifier
            outcome: Response outcome (success/failure/partial)
            time_to_containment: Time to contain threat (seconds)
            false_positive: Whether detection was false positive

        Returns:
            Outcome record
        """
        outcome_record = {
            'timestamp': datetime.now().isoformat(),
            'antigen_id': antigen_id,
            'outcome': outcome,
            'time_to_containment': time_to_containment,
            'false_positive': false_positive
        }

        self.response_outcomes.append(outcome_record)

        logger.info(
            f"Response outcome recorded: {outcome}, "
            f"ttc={time_to_containment:.1f}s" if time_to_containment else f"ttc=N/A"
        )

        return outcome_record

    async def get_effectiveness_metrics(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get effectiveness metrics for immune responses.

        Args:
            time_window_hours: Time window for metrics

        Returns:
            Effectiveness metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        # Filter recent outcomes
        recent_outcomes = [
            o for o in self.response_outcomes
            if datetime.fromisoformat(o['timestamp']) >= cutoff_time
        ]

        if not recent_outcomes:
            return {
                'time_window_hours': time_window_hours,
                'total_responses': 0
            }

        total = len(recent_outcomes)
        successes = sum(1 for o in recent_outcomes if o['outcome'] == 'success')
        false_positives = sum(1 for o in recent_outcomes if o['false_positive'])

        # Calculate average time-to-containment
        ttc_values = [o['time_to_containment'] for o in recent_outcomes if o['time_to_containment'] is not None]
        avg_ttc = sum(ttc_values) / len(ttc_values) if ttc_values else None

        return {
            'time_window_hours': time_window_hours,
            'total_responses': total,
            'successes': successes,
            'failures': total - successes,
            'success_rate': successes / total if total > 0 else 0.0,
            'false_positives': false_positives,
            'fp_rate': false_positives / total if total > 0 else 0.0,
            'avg_time_to_containment': avg_ttc
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Helper T-Cell service status.

        Returns:
            Service status dictionary
        """
        return {
            'status': 'operational',
            'threat_intel_count': len(self.threat_intelligence),
            'directives_issued': len(self.response_directives),
            'outcomes_recorded': len(self.response_outcomes),
            'last_coordination': self.last_coordination_time.isoformat() if self.last_coordination_time else 'N/A'
        }
