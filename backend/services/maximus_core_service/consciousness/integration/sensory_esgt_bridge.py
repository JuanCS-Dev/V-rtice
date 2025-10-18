"""
Sensory-Consciousness Bridge
============================

Integrates Predictive Coding layers with ESGT consciousness system.

Purpose
-------
Transforms sensory prediction errors into conscious-level salience signals,
enabling sensory-driven ignition of global workspace dynamics.

Theoretical Foundation
----------------------
Predictive Processing (Clark, 2013) + Global Workspace Theory (Dehaene, 2021):
- High prediction error = surprising/novel stimulus
- Surprise → salience amplification
- High salience → conscious ignition trigger
- Result: Unexpected events become conscious

Architecture
------------
Predictive Coding Layer → Bridge → ESGT Coordinator → Conscious Access

Flow:
1. Sensory input processed through predictive coding
2. Prediction errors computed (actual vs predicted)
3. Bridge converts errors to salience (novelty, relevance, urgency)
4. If salience exceeds threshold → ESGT ignition
5. Content enters global workspace → becomes conscious

Biological Correspondence
-------------------------
Bridge Component        | Neural Correlate
------------------------|------------------
Prediction error        | Mismatch negativity (MMN)
Salience computation    | Anterior cingulate cortex (ACC)
Threshold check         | Thalamic gating
ESGT trigger            | Cortical ignition

NO MOCK, NO PLACEHOLDER, NO TODO.

Authors: Claude Code + Juan Carlos
Version: 1.0.0
Date: 2025-10-12
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from consciousness.esgt.coordinator import SalienceScore, ESGTCoordinator


@dataclass
class PredictionError:
    """
    Prediction error from predictive coding layer.
    
    Attributes:
        layer_id: Layer that generated the error
        magnitude: Error magnitude [0, max_error]
        max_error: Maximum possible error (for normalization)
        bounded: Whether error was clipped to max
    """
    layer_id: int
    magnitude: float
    max_error: float
    bounded: bool = True


@dataclass
class SensoryContext:
    """
    Contextual information about sensory input.
    
    Attributes:
        modality: Sensory modality (e.g., "event", "network", "system")
        timestamp: Event timestamp
        source: Source identifier
        metadata: Additional context
    """
    modality: str
    timestamp: float
    source: str
    metadata: Dict[str, any]


@dataclass
class SalienceFactors:
    """
    Decomposed salience factors from prediction errors.
    
    Attributes:
        novelty: How unexpected (0-1, from prediction error)
        relevance: Task relevance (0-1, from context)
        urgency: Time-criticality (0-1, from context)
        intensity: Signal strength (0-1, from magnitude)
    """
    novelty: float
    relevance: float
    urgency: float
    intensity: float
    
    def compute_total_salience(self) -> float:
        """
        Compute weighted total salience.
        
        Weights based on empirical consciousness research:
        - Novelty: 0.4 (strongest predictor of conscious access)
        - Relevance: 0.3 (task-dependent modulation)
        - Urgency: 0.2 (temporal pressure)
        - Intensity: 0.1 (magnitude matters less than unexpectedness)
        
        Returns:
            Total salience score [0, 1]
        """
        return (
            0.4 * self.novelty +
            0.3 * self.relevance +
            0.2 * self.urgency +
            0.1 * self.intensity
        )


class SensoryESGTBridge:
    """
    Bridge between Predictive Coding and ESGT.
    
    Converts prediction errors into salience signals suitable for
    triggering global workspace ignition.
    
    Usage:
        bridge = SensoryESGTBridge(
            esgt_coordinator=esgt,
            salience_threshold=0.7,
            novelty_amplification=1.5
        )
        
        # From prediction error to consciousness
        prediction_error = layer.compute_error(prediction, actual)
        context = SensoryContext(modality="event", ...)
        
        ignited = await bridge.process_sensory_input(
            prediction_error=prediction_error,
            context=context
        )
        
        if ignited:
            print("Sensory event entered consciousness!")
    """
    
    def __init__(
        self,
        esgt_coordinator: ESGTCoordinator,
        salience_threshold: float = 0.7,
        novelty_amplification: float = 1.2,
        min_error_for_salience: float = 0.3,
    ):
        """
        Initialize Sensory-ESGT Bridge.
        
        Args:
            esgt_coordinator: ESGT coordinator instance
            salience_threshold: Minimum salience to trigger ignition (0-1)
            novelty_amplification: Amplification factor for novel stimuli (>1.0)
            min_error_for_salience: Minimum prediction error to consider (0-1)
        """
        self.esgt = esgt_coordinator
        self.salience_threshold = salience_threshold
        self.novelty_amplification = novelty_amplification
        self.min_error_threshold = min_error_for_salience
        
        # Statistics
        self.total_inputs = 0
        self.salient_inputs = 0
        self.ignitions_triggered = 0
    
    def compute_salience_from_error(
        self,
        prediction_error: PredictionError,
        context: SensoryContext,
    ) -> SalienceFactors:
        """
        Convert prediction error to salience factors.
        
        Args:
            prediction_error: Prediction error from predictive coding layer
            context: Contextual information about the input
            
        Returns:
            Decomposed salience factors
        """
        # Novelty from prediction error (normalized)
        # High error = unexpected = novel
        raw_novelty = min(1.0, prediction_error.magnitude / prediction_error.max_error)
        
        # Amplify novelty (surprising events get extra boost)
        novelty = min(1.0, raw_novelty * self.novelty_amplification)
        
        # Relevance from context
        # Check metadata for relevance markers
        relevance = self._compute_relevance(context)
        
        # Urgency from context
        # Security events, errors, anomalies are urgent
        urgency = self._compute_urgency(context)
        
        # Intensity from error magnitude
        intensity = min(1.0, prediction_error.magnitude)
        
        return SalienceFactors(
            novelty=novelty,
            relevance=relevance,
            urgency=urgency,
            intensity=intensity
        )
    
    def _compute_relevance(self, context: SensoryContext) -> float:
        """
        Compute task relevance from context.
        
        Heuristics:
        - Security events: HIGH (0.9)
        - System anomalies: HIGH (0.8)
        - Network events: MEDIUM (0.6)
        - Normal operations: LOW (0.3)
        
        Args:
            context: Sensory context
            
        Returns:
            Relevance score [0, 1]
        """
        metadata = context.metadata
        
        # Check for high-relevance markers
        if metadata.get("security_event", False):
            return 0.9
        
        if metadata.get("anomaly", False):
            return 0.8
        
        if context.modality in ["network", "intrusion"]:
            return 0.6
        
        # Default moderate relevance
        return 0.5
    
    def _compute_urgency(self, context: SensoryContext) -> float:
        """
        Compute temporal urgency from context.
        
        Heuristics:
        - Active attacks: CRITICAL (1.0)
        - Errors/failures: HIGH (0.8)
        - Warnings: MEDIUM (0.6)
        - Info: LOW (0.3)
        
        Args:
            context: Sensory context
            
        Returns:
            Urgency score [0, 1]
        """
        metadata = context.metadata
        
        # Check severity markers
        severity = metadata.get("severity", "info").lower()
        
        if severity in ["critical", "emergency"]:
            return 1.0
        
        if severity in ["error", "alert"]:
            return 0.8
        
        if severity in ["warning", "notice"]:
            return 0.6
        
        # Default low urgency
        return 0.3
    
    def should_trigger_ignition(self, salience_factors: SalienceFactors) -> bool:
        """
        Decide if salience warrants conscious ignition.
        
        Args:
            salience_factors: Computed salience factors
            
        Returns:
            True if should trigger ESGT ignition
        """
        total_salience = salience_factors.compute_total_salience()
        
        # Threshold check
        return total_salience >= self.salience_threshold
    
    def build_conscious_content(
        self,
        prediction_error: PredictionError,
        context: SensoryContext,
        salience_factors: SalienceFactors,
    ) -> Dict[str, any]:
        """
        Build content dictionary for global broadcast.
        
        Args:
            prediction_error: Original prediction error
            context: Sensory context
            salience_factors: Computed salience
            
        Returns:
            Content dictionary for ESGT
        """
        return {
            "source": "sensory_bridge",
            "modality": context.modality,
            "timestamp": context.timestamp,
            "prediction_error": {
                "magnitude": prediction_error.magnitude,
                "layer_id": prediction_error.layer_id,
                "bounded": True,
            },
            "salience": {
                "novelty": salience_factors.novelty,
                "relevance": salience_factors.relevance,
                "urgency": salience_factors.urgency,
                "intensity": salience_factors.intensity,
                "total": salience_factors.compute_total_salience(),
            },
            "context": context.metadata,
            "interpretation": f"Unexpected {context.modality} event (error: {prediction_error.magnitude:.2f})",
        }
    
    async def process_sensory_input(
        self,
        prediction_error: PredictionError,
        context: SensoryContext,
        force_ignition: bool = False,
    ) -> bool:
        """
        Process sensory input and potentially trigger consciousness.
        
        Complete flow:
        1. Check if error exceeds minimum threshold
        2. Compute salience factors from error + context
        3. Decide if salience warrants ignition
        4. If yes, trigger ESGT with conscious content
        5. Return whether ignition occurred
        
        Args:
            prediction_error: Prediction error from layer
            context: Contextual information
            force_ignition: Skip threshold check (for testing)
            
        Returns:
            True if ESGT ignition was triggered
        """
        self.total_inputs += 1
        
        # Filter out small errors (not salient)
        if prediction_error.magnitude < self.min_error_threshold and not force_ignition:
            return False
        
        # Compute salience
        salience_factors = self.compute_salience_from_error(
            prediction_error, context
        )
        
        # Check if salient enough
        is_salient = self.should_trigger_ignition(salience_factors)
        
        if is_salient:
            self.salient_inputs += 1
        
        # Decide ignition
        if not (is_salient or force_ignition):
            return False
        
        # Build salience score for ESGT
        total_salience = salience_factors.compute_total_salience()
        
        salience_score = SalienceScore(
            novelty=salience_factors.novelty,
            relevance=salience_factors.relevance,
            urgency=salience_factors.urgency,
        )
        
        # Build conscious content
        content = self.build_conscious_content(
            prediction_error, context, salience_factors
        )
        
        # Trigger ESGT ignition
        event = await self.esgt.initiate_esgt(
            salience=salience_score,
            content=content,
            content_source=f"sensory_bridge_{context.modality}",
        )
        
        if event.success:
            self.ignitions_triggered += 1
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get bridge statistics.
        
        Returns:
            Statistics dictionary
        """
        salient_rate = (
            self.salient_inputs / self.total_inputs
            if self.total_inputs > 0
            else 0.0
        )
        
        ignition_rate = (
            self.ignitions_triggered / self.salient_inputs
            if self.salient_inputs > 0
            else 0.0
        )
        
        return {
            "total_inputs": self.total_inputs,
            "salient_inputs": self.salient_inputs,
            "ignitions_triggered": self.ignitions_triggered,
            "salient_rate": salient_rate,
            "ignition_success_rate": ignition_rate,
            "threshold": self.salience_threshold,
        }
