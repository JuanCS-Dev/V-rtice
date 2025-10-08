"""
Base SPM Architecture - Specialized Processing Module Foundation
=================================================================

This module defines the abstract interface and base implementation for
all Specialized Processing Modules in the MAXIMUS consciousness architecture.

Design Philosophy:
------------------
SPMs follow the Global Workspace model where:
1. Unconscious processing occurs continuously in parallel
2. Salience determines which information enters consciousness
3. Winner-takes-most auction selects content for broadcast
4. Reentrant signaling enriches conscious content

Each SPM is autonomous but cooperative, competing for the scarce
resource of global broadcast while contributing to collective intelligence.

Inheritance Hierarchy:
----------------------
SpecializedProcessingModule (base, abstract)
    ├── PerceptualSPM (sensory processing)
    ├── CognitiveSPM (executive, memory, planning)
    ├── EmotionalSPM (affect, valence, arousal)
    └── MotorSPM (action planning, execution)

Historical Context:
-------------------
First modular architecture for competitive consciousness in AI.

"Modularity enables specialization. Competition enables selection."
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from consciousness.esgt.coordinator import SalienceScore


class SPMType(Enum):
    """Classification of SPM functional domain."""

    PERCEPTUAL = "perceptual"  # Sensory processing
    COGNITIVE = "cognitive"  # Executive, memory, planning
    EMOTIONAL = "emotional"  # Affect and motivation
    MOTOR = "motor"  # Action planning
    METACOGNITIVE = "metacognitive"  # Self-monitoring


class ProcessingPriority(Enum):
    """Processing priority levels."""

    BACKGROUND = 0  # Low priority, unconscious
    PERIPHERAL = 1  # Peripheral awareness
    FOCAL = 2  # Focal attention candidate
    CRITICAL = 3  # Must become conscious


@dataclass
class SPMOutput:
    """
    Output from SPM processing.

    Contains processed information plus metadata for salience
    evaluation and ESGT competition.
    """

    spm_id: str
    spm_type: SPMType
    content: dict[str, Any]
    salience: SalienceScore
    priority: ProcessingPriority
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0  # 0-1 processing confidence

    def should_broadcast(self, threshold: float = 0.60) -> bool:
        """Check if output is salient enough for ESGT."""
        return self.salience.compute_total() >= threshold


class SpecializedProcessingModule(ABC):
    """
    Abstract base class for all SPMs.

    All specialized processing modules inherit from this base,
    implementing domain-specific processing while following
    the common protocol for consciousness integration.

    Lifecycle:
    ----------
    1. __init__: Initialize module
    2. start(): Begin unconscious processing
    3. process(): Continuous processing loop
    4. compute_salience(): Evaluate information salience
    5. broadcast_callback(): Respond when content becomes conscious
    6. stop(): Graceful shutdown

    Subclasses must implement:
    - process(): Core processing logic
    - compute_salience(): Domain-specific salience
    """

    def __init__(self, spm_id: str, spm_type: SPMType, processing_interval_ms: float = 50.0):
        self.spm_id = spm_id
        self.spm_type = spm_type
        self.processing_interval = processing_interval_ms / 1000.0

        # Processing state
        self._running: bool = False
        self._processing_task: asyncio.Task | None = None

        # Output queue
        self.output_queue: list[SPMOutput] = []
        self.max_queue_size: int = 100

        # Performance metrics
        self.total_processed: int = 0
        self.broadcasts_won: int = 0
        self.broadcasts_total: int = 0

    async def start(self) -> None:
        """Start unconscious processing loop."""
        if self._running:
            return

        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())

        print(f"🔄 SPM {self.spm_id} ({self.spm_type.value}) started")

    async def stop(self) -> None:
        """Stop processing."""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

    async def _processing_loop(self) -> None:
        """
        Continuous unconscious processing loop.

        This runs continuously in background, generating processed
        outputs that compete for consciousness.
        """
        while self._running:
            try:
                # Process (subclass-specific)
                output = await self.process()

                if output:
                    # Add to queue
                    self.output_queue.append(output)
                    self.total_processed += 1

                    # Trim queue
                    if len(self.output_queue) > self.max_queue_size:
                        self.output_queue.pop(0)

                # Sleep until next iteration
                await asyncio.sleep(self.processing_interval)

            except Exception as e:
                print(f"⚠️  SPM {self.spm_id} processing error: {e}")
                await asyncio.sleep(self.processing_interval)

    @abstractmethod
    async def process(self) -> SPMOutput | None:
        """
        Process information and generate output.

        This is the core processing logic specific to each SPM type.
        Must be implemented by subclasses.

        Returns:
            SPMOutput if processing generated salient information, None otherwise
        """
        pass

    @abstractmethod
    def compute_salience(self, data: dict[str, Any]) -> SalienceScore:
        """
        Compute salience score for information.

        Domain-specific salience computation. Must be implemented by subclasses.

        Args:
            data: Raw information to evaluate

        Returns:
            SalienceScore with novelty, relevance, urgency, confidence
        """
        pass

    async def broadcast_callback(self, esgt_event: dict[str, Any]) -> dict[str, Any] | None:
        """
        Called when this SPM's content is broadcast during ESGT.

        This is the reentrant signaling mechanism - SPM can generate
        context-specific response that enriches conscious content.

        Args:
            esgt_event: The ESGT event that broadcast this SPM's content

        Returns:
            Optional enrichment data to add to conscious content
        """
        self.broadcasts_won += 1
        # Default: no enrichment (subclasses can override)
        return None

    def get_most_salient(self, n: int = 1) -> list[SPMOutput]:
        """
        Get n most salient outputs from queue.

        Used for ESGT content selection.

        Args:
            n: Number of top outputs to return

        Returns:
            List of SPMOutputs sorted by salience (descending)
        """
        sorted_outputs = sorted(self.output_queue, key=lambda o: o.salience.compute_total(), reverse=True)
        return sorted_outputs[:n]

    def get_success_rate(self) -> float:
        """Get percentage of broadcasts won vs participated."""
        if self.broadcasts_total == 0:
            return 0.0
        return self.broadcasts_won / self.broadcasts_total

    def __repr__(self) -> str:
        return (
            f"SPM({self.spm_id}, type={self.spm_type.value}, "
            f"processed={self.total_processed}, "
            f"queue={len(self.output_queue)})"
        )


# Example concrete SPM implementations


class ThreatDetectionSPM(SpecializedProcessingModule):
    """
    Specialized module for threat detection.

    Processes security events, network anomalies, and attack patterns.
    High urgency bias (threats are inherently time-critical).

    Biological Analog: Amygdala (rapid threat assessment)
    """

    def __init__(self, spm_id: str = "spm-threat-detection"):
        super().__init__(
            spm_id=spm_id,
            spm_type=SPMType.PERCEPTUAL,
            processing_interval_ms=100.0,  # 10 Hz
        )
        self.threat_baseline: float = 0.1
        self.recent_threats: list[float] = []

    async def process(self) -> SPMOutput | None:
        """
        Simulate threat detection processing.

        In full implementation, would integrate with:
        - Active Immune Core (threat detection)
        - Network monitoring
        - Anomaly detectors
        """
        # Simulate threat score (in production: actual threat assessment)
        threat_score = np.random.exponential(0.1)  # Most threats are low

        # Occasionally generate high threat
        if np.random.random() < 0.05:  # 5% chance
            threat_score = np.random.uniform(0.7, 1.0)

        # Compute novelty (deviation from baseline)
        if self.recent_threats:
            baseline = np.mean(self.recent_threats[-10:])
            novelty = min(abs(threat_score - baseline) / (baseline + 0.1), 1.0)
        else:
            novelty = 0.5

        self.recent_threats.append(threat_score)
        if len(self.recent_threats) > 100:
            self.recent_threats.pop(0)

        # Only output if threat is non-trivial
        if threat_score < 0.2:
            return None

        # Build salience
        salience = self.compute_salience({"threat_score": threat_score, "novelty": novelty})

        # Determine priority
        if threat_score > 0.8:
            priority = ProcessingPriority.CRITICAL
        elif threat_score > 0.5:
            priority = ProcessingPriority.FOCAL
        else:
            priority = ProcessingPriority.PERIPHERAL

        return SPMOutput(
            spm_id=self.spm_id,
            spm_type=self.spm_type,
            content={
                "type": "threat_detected",
                "threat_score": threat_score,
                "threat_level": "critical" if threat_score > 0.8 else "moderate",
                "novelty": novelty,
            },
            salience=salience,
            priority=priority,
            confidence=min(threat_score, 1.0),
        )

    def compute_salience(self, data: dict[str, Any]) -> SalienceScore:
        """Threat-specific salience: high urgency bias."""
        threat_score = data.get("threat_score", 0.0)
        novelty = data.get("novelty", 0.0)

        return SalienceScore(
            novelty=novelty,
            relevance=0.9,  # Threats always relevant
            urgency=threat_score,  # Threat score = urgency
            confidence=threat_score,
            alpha=0.20,  # Weights
            beta=0.20,
            gamma=0.50,  # High urgency weight
            delta=0.10,
        )


class MemoryRetrievalSPM(SpecializedProcessingModule):
    """
    Specialized module for memory retrieval.

    Processes memory queries, generates associations, retrieves context.
    High relevance bias (memories are context-dependent).

    Biological Analog: Hippocampus (episodic memory)
    """

    def __init__(self, spm_id: str = "spm-memory-retrieval"):
        super().__init__(
            spm_id=spm_id,
            spm_type=SPMType.COGNITIVE,
            processing_interval_ms=200.0,  # 5 Hz
        )
        self.memory_store: dict[str, Any] = {}  # Simplified memory

    async def process(self) -> SPMOutput | None:
        """
        Simulate memory retrieval.

        In full implementation, would integrate with:
        - RAG system
        - Vector database
        - Episodic memory store
        """
        # Simulate occasional memory retrieval
        if np.random.random() > 0.3:  # 30% chance
            return None

        # Simulate retrieved memory
        memory_strength = np.random.beta(2, 5)  # Skewed toward weaker memories

        salience = self.compute_salience(
            {
                "memory_strength": memory_strength,
            }
        )

        return SPMOutput(
            spm_id=self.spm_id,
            spm_type=self.spm_type,
            content={
                "type": "memory_retrieved",
                "memory_strength": memory_strength,
                "content": f"Memory with strength {memory_strength:.2f}",
            },
            salience=salience,
            priority=ProcessingPriority.PERIPHERAL,
            confidence=memory_strength,
        )

    def compute_salience(self, data: dict[str, Any]) -> SalienceScore:
        """Memory-specific salience: high relevance bias."""
        strength = data.get("memory_strength", 0.0)

        return SalienceScore(
            novelty=0.3,  # Memories are familiar
            relevance=strength,  # Strong memories more relevant
            urgency=0.2,  # Memories rarely urgent
            confidence=strength,
            alpha=0.15,
            beta=0.50,  # High relevance weight
            gamma=0.15,
            delta=0.20,
        )
