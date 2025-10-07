"""
SimpleSPM - Configurable Test SPM for ESGT Validation
======================================================

This module implements a minimal, configurable Specialized Processing Module
for testing ESGT ignition protocol without requiring complex domain-specific
processing logic.

Design Philosophy:
------------------
SimpleSPM serves as:
1. A test harness for ESGT coordinator
2. A reference implementation for new SPMs
3. A debugging tool for consciousness pipeline

It generates synthetic content with controllable salience, allowing systematic
testing of ESGT trigger conditions, node recruitment, and coherence validation.

Historical Context:
-------------------
First concrete SPM implementation in MAXIMUS consciousness architecture.
While not domain-specialized, it validates that the SPM protocol and ESGT
ignition mechanism work correctly before investing in perceptual/cognitive SPMs.

"Simplicity validates complexity."
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from consciousness.esgt.spm.base import (
    SpecializedProcessingModule,
    SPMType,
    SPMOutput,
    ProcessingPriority,
)
from consciousness.esgt.coordinator import SalienceScore


@dataclass
class SimpleSPMConfig:
    """Configuration for SimpleSPM."""

    # Processing
    processing_interval_ms: float = 100.0  # How often to generate output
    burst_mode: bool = False  # Generate multiple outputs per cycle
    burst_count: int = 3  # Outputs per burst

    # Salience configuration
    base_novelty: float = 0.3
    base_relevance: float = 0.5
    base_urgency: float = 0.2
    salience_noise: float = 0.1  # Random variation

    # Content generation
    content_size_bytes: int = 1024  # Size of generated content
    include_timestamp: bool = True
    include_counter: bool = True

    # Priority
    default_priority: ProcessingPriority = ProcessingPriority.PERIPHERAL

    # Lifecycle
    auto_start: bool = True
    max_outputs: int = 0  # 0 = unlimited


class SimpleSPM(SpecializedProcessingModule):
    """
    A simple, configurable SPM for testing and validation.

    SimpleSPM generates synthetic content with controllable salience,
    allowing systematic testing of ESGT trigger conditions and
    ignition protocol.

    Unlike domain-specific SPMs (perceptual, cognitive), SimpleSPM
    has no semantic processing - it's purely for protocol validation.

    Example Usage:
    --------------
    ```python
    # Create SPM with high salience
    config = SimpleSPMConfig(
        base_novelty=0.8,
        base_relevance=0.9,
        base_urgency=0.7,
    )
    spm = SimpleSPM("test-spm", config)

    # Register callback
    spm.register_output_callback(my_handler)

    # Start processing
    await spm.start()

    # SPM will continuously generate high-salience outputs
    # triggering ESGT ignition when combined with other SPMs
    ```
    """

    def __init__(
        self,
        spm_id: str,
        config: Optional[SimpleSPMConfig] = None,
        spm_type: SPMType = SPMType.COGNITIVE,
    ):
        """
        Initialize SimpleSPM.

        Args:
            spm_id: Unique identifier
            config: Configuration (uses defaults if None)
            spm_type: SPM type classification
        """
        super().__init__(spm_id, spm_type)

        self.config = config or SimpleSPMConfig()

        # State
        self._running: bool = False
        self._processing_task: Optional[asyncio.Task] = None
        self._output_counter: int = 0
        self._total_outputs_generated: int = 0

        # Callbacks
        self._output_callbacks: List[Callable[[SPMOutput], None]] = []

        # Metrics
        self._generation_latencies_ms: List[float] = []
        self._last_generation_time: float = 0.0

    async def start(self) -> None:
        """Start continuous processing."""
        if self._running:
            return

        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())

    async def stop(self) -> None:
        """Stop processing gracefully."""
        self._running = False

        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        self._processing_task = None

    async def _processing_loop(self) -> None:
        """
        Main processing loop.

        Generates outputs at configured interval until stopped
        or max_outputs reached.
        """
        interval_s = self.config.processing_interval_ms / 1000.0

        while self._running:
            try:
                # Check if we've hit max outputs
                if self.config.max_outputs > 0:
                    if self._total_outputs_generated >= self.config.max_outputs:
                        break

                # Generate output(s)
                if self.config.burst_mode:
                    outputs = self._generate_burst()
                else:
                    outputs = [self._generate_single_output()]

                # Dispatch outputs
                for output in outputs:
                    self._dispatch_output(output)

                # Wait for next cycle
                await asyncio.sleep(interval_s)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Graceful degradation - log and continue
                print(f"[SimpleSPM {self.spm_id}] Error in processing: {e}")
                await asyncio.sleep(interval_s)

    def _generate_single_output(self) -> SPMOutput:
        """Generate a single SPM output."""
        start = time.time()

        # Compute salience (base + noise)
        import random

        novelty = max(0.0, min(1.0,
            self.config.base_novelty + random.uniform(
                -self.config.salience_noise,
                self.config.salience_noise
            )
        ))

        relevance = max(0.0, min(1.0,
            self.config.base_relevance + random.uniform(
                -self.config.salience_noise,
                self.config.salience_noise
            )
        ))

        urgency = max(0.0, min(1.0,
            self.config.base_urgency + random.uniform(
                -self.config.salience_noise,
                self.config.salience_noise
            )
        ))

        salience = SalienceScore(
            novelty=novelty,
            relevance=relevance,
            urgency=urgency,
        )

        # Generate content
        content = self._generate_content()

        # Create output
        output = SPMOutput(
            spm_id=self.spm_id,
            spm_type=self.spm_type,
            content=content,
            salience=salience,
            priority=self.config.default_priority,
            timestamp=time.time(),
            confidence=1.0,
        )

        # Track metrics
        latency_ms = (time.time() - start) * 1000
        self._generation_latencies_ms.append(latency_ms)
        self._last_generation_time = time.time()
        self._output_counter += 1
        self._total_outputs_generated += 1

        # Keep only recent latencies
        if len(self._generation_latencies_ms) > 100:
            self._generation_latencies_ms.pop(0)

        return output

    def _generate_burst(self) -> List[SPMOutput]:
        """Generate multiple outputs in burst mode."""
        outputs = []
        for _ in range(self.config.burst_count):
            outputs.append(self._generate_single_output())
        return outputs

    def _generate_content(self) -> Dict[str, Any]:
        """Generate synthetic content."""
        content: Dict[str, Any] = {
            "type": "simple_spm_output",
            "source": self.spm_id,
        }

        if self.config.include_timestamp:
            content["timestamp"] = time.time()

        if self.config.include_counter:
            content["counter"] = self._output_counter

        # Add synthetic data to reach target size
        if self.config.content_size_bytes > 0:
            # Rough estimate: each char = 1 byte
            existing_size = len(str(content))
            remaining = self.config.content_size_bytes - existing_size

            if remaining > 0:
                content["synthetic_data"] = "x" * remaining

        return content

    def _dispatch_output(self, output: SPMOutput) -> None:
        """Dispatch output to registered callbacks."""
        for callback in self._output_callbacks:
            try:
                callback(output)
            except Exception as e:
                # Don't let callback errors stop processing
                print(f"[SimpleSPM {self.spm_id}] Callback error: {e}")

    # =========================================================================
    # Abstract Method Implementations
    # =========================================================================

    async def process(self) -> Optional[SPMOutput]:
        """
        Process and generate output (required by base class).

        SimpleSPM uses _processing_loop() instead, but this method
        satisfies the abstract requirement.
        """
        return self._generate_single_output()

    def compute_salience(self, data: Dict[str, Any]) -> SalienceScore:
        """
        Compute salience for given data (required by base class).

        SimpleSPM uses configured base salience, but this method
        provides on-demand computation.
        """
        import random

        novelty = max(0.0, min(1.0,
            self.config.base_novelty + random.uniform(
                -self.config.salience_noise,
                self.config.salience_noise
            )
        ))

        relevance = max(0.0, min(1.0,
            self.config.base_relevance + random.uniform(
                -self.config.salience_noise,
                self.config.salience_noise
            )
        ))

        urgency = max(0.0, min(1.0,
            self.config.base_urgency + random.uniform(
                -self.config.salience_noise,
                self.config.salience_noise
            )
        ))

        return SalienceScore(
            novelty=novelty,
            relevance=relevance,
            urgency=urgency,
        )

    # =========================================================================
    # SimpleSPM-Specific Methods
    # =========================================================================

    def register_output_callback(
        self,
        callback: Callable[[SPMOutput], None]
    ) -> None:
        """Register callback for output events."""
        if callback not in self._output_callbacks:
            self._output_callbacks.append(callback)

    def unregister_output_callback(
        self,
        callback: Callable[[SPMOutput], None]
    ) -> None:
        """Unregister callback."""
        if callback in self._output_callbacks:
            self._output_callbacks.remove(callback)

    def configure_salience(
        self,
        novelty: Optional[float] = None,
        relevance: Optional[float] = None,
        urgency: Optional[float] = None,
    ) -> None:
        """
        Dynamically adjust base salience values.

        Allows tests to control whether outputs should trigger ESGT.
        """
        if novelty is not None:
            self.config.base_novelty = max(0.0, min(1.0, novelty))

        if relevance is not None:
            self.config.base_relevance = max(0.0, min(1.0, relevance))

        if urgency is not None:
            self.config.base_urgency = max(0.0, min(1.0, urgency))

    def get_metrics(self) -> Dict[str, Any]:
        """Get SPM performance metrics."""
        if not self._generation_latencies_ms:
            avg_latency = 0.0
        else:
            avg_latency = sum(self._generation_latencies_ms) / len(self._generation_latencies_ms)

        return {
            "spm_id": self.spm_id,
            "spm_type": self.spm_type.value,
            "running": self._running,
            "total_outputs": self._total_outputs_generated,
            "avg_generation_latency_ms": avg_latency,
            "last_generation_time": self._last_generation_time,
        }

    def is_running(self) -> bool:
        """Check if SPM is running."""
        return self._running

    def __repr__(self) -> str:
        return (f"SimpleSPM(id={self.spm_id}, "
                f"type={self.spm_type.value}, "
                f"outputs={self._total_outputs_generated}, "
                f"running={self._running})")
