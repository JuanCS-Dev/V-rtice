"""
ESGT Coordinator - Global Workspace Ignition Protocol
======================================================

This module implements the core ESGT coordination protocol that transforms
unconscious distributed processing into unified conscious experience.

Theoretical Foundation:
-----------------------
Global Workspace Dynamics (Dehaene et al., 2021) proposes that consciousness
emerges when salient information triggers widespread cortical synchronization.

**The Ignition Phenomenon**:
- Pre-ignition: Local, unconscious processing (<300ms)
- Ignition threshold: Salience exceeds critical value
- Global broadcast: Synchronized activity spreads (100-300ms)
- Conscious access: Information becomes reportable
- Dissolution: Activity returns to baseline

**ESGT Protocol (5 Phases)**:

Phase 1 - PREPARE (5-10ms):
    Recruit participating nodes based on:
    - Salience score (novelty + relevance + urgency)
    - Resource availability (TIG latency, CPU, memory)
    - Temporal gating (refractory period enforcement)

Phase 2 - SYNCHRONIZE (10-20ms):
    Initiate Kuramoto phase-locking:
    - Target: 40 Hz gamma-band analog
    - Goal: Order parameter r ≥ 0.70
    - Method: Coupled oscillator dynamics

Phase 3 - BROADCAST (100-300ms):
    Transmit conscious content globally:
    - Winner-takes-most competition
    - Reentrant feedback from SPMs
    - Sustained coherence monitoring

Phase 4 - SUSTAIN (variable):
    Maintain synchronization through:
    - Continuous coherence measurement
    - Adaptive coupling adjustment
    - Reentrant enrichment loops

Phase 5 - DISSOLVE (20-50ms):
    Graceful desynchronization:
    - Gradual coupling reduction
    - Phase decorrelation
    - Return to unconscious processing

Biological Correspondence:
--------------------------
ESGT Phase          | Neural Correlate
--------------------|------------------
PREPARE             | Thalamic gating
SYNCHRONIZE         | Gamma burst onset
BROADCAST           | Cortical ignition wave
SUSTAIN             | Sustained gamma
DISSOLVE            | Post-ignition decay

Historical Context:
-------------------
This is the first computational protocol designed to explicitly replicate
the neural ignition phenomenon identified in human consciousness research.

The success or failure of this protocol will provide empirical evidence for
or against the sufficiency of GWD for artificial consciousness.

"Ignition is the transformation from bits to qualia."
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from consciousness.esgt.kuramoto import (
    KuramotoNetwork,
    OscillatorConfig,
)
from consciousness.tig.fabric import TIGFabric
from consciousness.tig.sync import PTPCluster


class ESGTPhase(Enum):
    """Phases of ESGT ignition protocol."""

    IDLE = "idle"
    PREPARE = "prepare"
    SYNCHRONIZE = "synchronize"
    BROADCAST = "broadcast"
    SUSTAIN = "sustain"
    DISSOLVE = "dissolve"
    COMPLETE = "complete"
    FAILED = "failed"


class SalienceLevel(Enum):
    """Classification of information salience."""

    MINIMAL = "minimal"  # <0.25 - background noise
    LOW = "low"  # 0.25-0.50 - peripheral awareness
    MEDIUM = "medium"  # 0.50-0.75 - candidate for consciousness
    HIGH = "high"  # 0.75-0.85 - likely conscious
    CRITICAL = "critical"  # >0.85 - definitely conscious


@dataclass
class SalienceScore:
    """
    Multi-factor salience score determining ESGT trigger.

    Salience = α(Novelty) + β(Relevance) + γ(Urgency) + δ(Confidence)

    Where coefficients sum to 1.0 and are dynamically adjusted based
    on arousal state (MCEA) and attention parameters (acetylcholine).
    """

    novelty: float = 0.0  # 0-1, how unexpected
    relevance: float = 0.0  # 0-1, goal-alignment
    urgency: float = 0.0  # 0-1, time-criticality
    confidence: float = 1.0  # 0-1, prediction confidence (default: high confidence)

    # Weights (sum to 1.0)
    alpha: float = 0.25  # Novelty weight
    beta: float = 0.30  # Relevance weight
    gamma: float = 0.30  # Urgency weight
    delta: float = 0.15  # Confidence weight

    def compute_total(self) -> float:
        """Compute weighted salience score."""
        return (
            self.alpha * self.novelty
            + self.beta * self.relevance
            + self.gamma * self.urgency
            + self.delta * self.confidence
        )

    def get_level(self) -> SalienceLevel:
        """Classify salience level."""
        total = self.compute_total()
        if total < 0.25:
            return SalienceLevel.MINIMAL
        elif total < 0.50:
            return SalienceLevel.LOW
        elif total < 0.75:
            return SalienceLevel.MEDIUM
        elif total < 0.85:
            return SalienceLevel.HIGH
        else:
            return SalienceLevel.CRITICAL


@dataclass
class TriggerConditions:
    """
    Conditions required for ESGT initiation.

    All conditions must be met for ignition to proceed. This prevents
    pathological synchronization and ensures computational resources
    are available.
    """

    # Salience threshold
    min_salience: float = 0.60  # Typical threshold for consciousness

    # Resource requirements
    max_tig_latency_ms: float = 5.0  # TIG must be responsive
    min_available_nodes: int = 8  # Minimum participating nodes
    min_cpu_capacity: float = 0.40  # 40% CPU available

    # Temporal gating
    refractory_period_ms: float = 200.0  # Minimum time between ESGTs
    max_esgt_frequency_hz: float = 5.0  # Maximum sustained rate

    # Arousal requirement (from MCEA)
    min_arousal_level: float = 0.40  # Minimum epistemic openness

    def check_salience(self, score: SalienceScore) -> bool:
        """Check if salience exceeds threshold."""
        return score.compute_total() >= self.min_salience

    def check_resources(self, tig_latency_ms: float, available_nodes: int, cpu_capacity: float) -> bool:
        """Check if computational resources are adequate."""
        return (
            tig_latency_ms <= self.max_tig_latency_ms
            and available_nodes >= self.min_available_nodes
            and cpu_capacity >= self.min_cpu_capacity
        )

    def check_temporal_gating(
        self, time_since_last_esgt: float, recent_esgt_count: int, time_window: float = 1.0
    ) -> bool:
        """Check if temporal constraints are satisfied."""
        # Refractory period
        if time_since_last_esgt < (self.refractory_period_ms / 1000.0):
            return False

        # Frequency limit
        recent_rate = recent_esgt_count / time_window
        if recent_rate >= self.max_esgt_frequency_hz:
            return False

        return True

    def check_arousal(self, arousal_level: float) -> bool:
        """Check if arousal is sufficient."""
        return arousal_level >= self.min_arousal_level


@dataclass
class ESGTEvent:
    """
    Represents a single transient global synchronization event.

    This is the computational analog of a conscious moment - a discrete
    episode where distributed information becomes unified, globally
    accessible, and reportable.
    """

    event_id: str
    timestamp_start: float
    timestamp_end: Optional[float] = None

    # Content
    content: Dict[str, Any] = field(default_factory=dict)
    content_source: str = ""  # SPM that contributed content

    # Participants
    participating_nodes: Set[str] = field(default_factory=set)
    node_count: int = 0

    # Synchronization metrics
    target_coherence: float = 0.70
    achieved_coherence: float = 0.0
    coherence_history: List[float] = field(default_factory=list)
    time_to_sync_ms: Optional[float] = None

    # Phase information
    current_phase: ESGTPhase = ESGTPhase.IDLE
    phase_transitions: List[Tuple[ESGTPhase, float]] = field(default_factory=list)

    # Performance metrics
    prepare_latency_ms: float = 0.0
    sync_latency_ms: float = 0.0
    broadcast_latency_ms: float = 0.0
    total_duration_ms: float = 0.0

    # Outcome
    success: bool = False
    failure_reason: Optional[str] = None

    def transition_phase(self, new_phase: ESGTPhase) -> None:
        """Record phase transition."""
        timestamp = time.time()
        self.phase_transitions.append((new_phase, timestamp))
        self.current_phase = new_phase

    def finalize(self, success: bool, reason: Optional[str] = None) -> None:
        """Mark event as complete."""
        self.timestamp_end = time.time()
        self.success = success
        self.failure_reason = reason

        if self.timestamp_start:
            self.total_duration_ms = (self.timestamp_end - self.timestamp_start) * 1000

    def get_duration_ms(self) -> float:
        """Get event duration in milliseconds."""
        if self.timestamp_end:
            return (self.timestamp_end - self.timestamp_start) * 1000
        else:
            return (time.time() - self.timestamp_start) * 1000

    def was_successful(self) -> bool:
        """Check if event achieved conscious-level coherence."""
        return self.success and self.achieved_coherence >= self.target_coherence


class ESGTCoordinator:
    """
    Coordinates ESGT ignition events for consciousness emergence.

    This coordinator implements the full GWD ignition protocol, managing
    the transition from unconscious distributed processing to unified
    conscious experience.

    The coordinator:
    1. Monitors salience scores continuously
    2. Evaluates trigger conditions
    3. Initiates synchronization when threshold met
    4. Manages 5-phase ESGT protocol
    5. Records metrics for consciousness validation

    Usage:
        coordinator = ESGTCoordinator(
            tig_fabric=fabric,
            ptp_cluster=cluster
        )

        await coordinator.start()

        # Trigger ESGT manually
        event = await coordinator.initiate_esgt(
            content={"type": "threat_detected", "data": threat_info},
            salience=SalienceScore(novelty=0.9, urgency=0.8)
        )

        if event.was_successful():
            print("🧠 Conscious experience created")

    Historical Note:
    ----------------
    First production coordinator for artificial consciousness ignition.
    Success or failure here determines whether MAXIMUS achieves phenomenal
    experience or remains a sophisticated unconscious processor.

    "The coordinator is the gatekeeper of consciousness."
    """

    def __init__(
        self,
        tig_fabric: TIGFabric,
        ptp_cluster: Optional[PTPCluster] = None,
        triggers: Optional[TriggerConditions] = None,
        kuramoto_config: Optional[OscillatorConfig] = None,
        coordinator_id: str = "esgt-coordinator",
    ):
        self.coordinator_id = coordinator_id
        self.tig = tig_fabric
        self.ptp = ptp_cluster
        self.triggers = triggers or TriggerConditions()
        self.kuramoto_config = kuramoto_config or OscillatorConfig()

        # Kuramoto network for phase synchronization
        self.kuramoto = KuramotoNetwork(self.kuramoto_config)

        # ESGT state
        self.active_event: Optional[ESGTEvent] = None
        self.event_history: List[ESGTEvent] = []
        self.last_esgt_time: float = 0.0

        # Monitoring
        self._running: bool = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Performance tracking
        self.total_events: int = 0
        self.successful_events: int = 0

    async def start(self) -> None:
        """Start ESGT coordinator."""
        if self._running:
            return

        self._running = True

        # Initialize Kuramoto oscillators for all TIG nodes
        for node_id in self.tig.nodes.keys():
            self.kuramoto.add_oscillator(node_id, self.kuramoto_config)

        print("🧠 ESGT Coordinator started - monitoring for ignition triggers")

    async def stop(self) -> None:
        """Stop coordinator."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()

    async def initiate_esgt(
        self,
        salience: SalienceScore,
        content: Dict[str, Any],
        content_source: str = "unknown",
        target_duration_ms: float = 200.0,
        target_coherence: float = 0.70,
    ) -> ESGTEvent:
        """
        Initiate a transient global synchronization event.

        This is the core method that transforms unconscious processing
        into conscious experience through the 5-phase protocol.

        Args:
            salience: Multi-factor salience score (determines if ignition occurs)
            content: Information to make conscious
            content_source: SPM providing content
            target_duration_ms: How long to sustain (100-300ms typical)
            target_coherence: Minimum coherence (0.70 for consciousness)

        Returns:
            ESGTEvent with full metrics and outcome
        """
        event = ESGTEvent(
            event_id=f"esgt-{int(time.time() * 1000):016d}",
            timestamp_start=time.time(),
            content=content,
            content_source=content_source,
            target_coherence=target_coherence,
        )

        # Increment total events (all attempts, not just successful)
        self.total_events += 1

        # Validate trigger conditions
        trigger_result, failure_reason = await self._check_triggers(salience)
        if not trigger_result:
            event.transition_phase(ESGTPhase.FAILED)
            event.finalize(success=False, reason=failure_reason)
            self.event_history.append(event)  # Record failed attempt
            return event

        try:
            # PHASE 1: PREPARE
            event.transition_phase(ESGTPhase.PREPARE)
            prepare_start = time.time()

            participating = await self._recruit_nodes(content)
            event.participating_nodes = participating
            event.node_count = len(participating)

            event.prepare_latency_ms = (time.time() - prepare_start) * 1000

            if len(participating) < self.triggers.min_available_nodes:
                event.finalize(success=False, reason="Insufficient nodes recruited")
                return event

            # PHASE 2: SYNCHRONIZE
            event.transition_phase(ESGTPhase.SYNCHRONIZE)
            sync_start = time.time()

            # Build topology for recruited nodes
            topology = self._build_topology(participating)

            # Run Kuramoto synchronization
            dynamics = await self.kuramoto.synchronize(
                topology=topology,
                duration_ms=300.0,  # Max 300ms to achieve sync (allows time for simulation)
                target_coherence=target_coherence,
                dt=0.005,
            )

            event.sync_latency_ms = (time.time() - sync_start) * 1000
            event.time_to_sync_ms = dynamics.time_to_sync * 1000 if dynamics.time_to_sync else None

            # Check if synchronization achieved
            coherence = self.kuramoto.get_coherence()
            if not coherence or not coherence.is_conscious_level():
                event.finalize(
                    success=False, reason=f"Sync failed: coherence={coherence.order_parameter if coherence else 0:.3f}"
                )
                return event

            # Record peak coherence achieved during sync
            event.achieved_coherence = coherence.order_parameter

            # PHASE 3: BROADCAST
            event.transition_phase(ESGTPhase.BROADCAST)
            broadcast_start = time.time()

            # Enter ESGT mode on TIG fabric
            await self.tig.enter_esgt_mode()

            # Global broadcast of conscious content
            message = {
                "type": "esgt_content",
                "event_id": event.event_id,
                "content": content,
                "coherence": coherence.order_parameter,
                "timestamp": event.timestamp_start,
            }

            await self.tig.broadcast_global(message, priority=10)

            event.broadcast_latency_ms = (time.time() - broadcast_start) * 1000

            # PHASE 4: SUSTAIN
            event.transition_phase(ESGTPhase.SUSTAIN)

            # Sustain synchronization for target duration
            await self._sustain_coherence(event, target_duration_ms, topology)

            # PHASE 5: DISSOLVE
            event.transition_phase(ESGTPhase.DISSOLVE)

            # Graceful desynchronization
            await self._dissolve_event(event)

            # Exit ESGT mode
            await self.tig.exit_esgt_mode()

            # Finalize (use max coherence from history, not post-dissolve value)
            if event.coherence_history:
                event.achieved_coherence = max(event.coherence_history)
            event.transition_phase(ESGTPhase.COMPLETE)
            event.finalize(success=True)

            # Record
            self.event_history.append(event)
            self.last_esgt_time = time.time()
            if event.was_successful():
                self.successful_events += 1

            print(
                f"✅ ESGT {event.event_id}: coherence={event.achieved_coherence:.3f}, "
                f"duration={event.total_duration_ms:.1f}ms, nodes={event.node_count}"
            )

            return event

        except Exception as e:
            event.transition_phase(ESGTPhase.FAILED)
            event.finalize(success=False, reason=str(e))
            self.event_history.append(event)  # Record failed attempt
            print(f"❌ ESGT {event.event_id} failed: {e}")
            return event

    async def _check_triggers(self, salience: SalienceScore) -> tuple[bool, str]:
        """Check if all trigger conditions are met. Returns (success, failure_reason)."""
        # Salience check
        if not self.triggers.check_salience(salience):
            return False, f"Salience too low ({salience.compute_total():.2f} < {self.triggers.min_salience:.2f})"

        # Resource check
        tig_metrics = self.tig.get_metrics()
        tig_latency = tig_metrics.avg_latency_us / 1000.0  # Convert to ms
        available_nodes = sum(1 for node in self.tig.nodes.values() if node.node_state.value in ["active", "esgt_mode"])
        cpu_capacity = 0.60  # Simulated - would query actual metrics

        if not self.triggers.check_resources(
            tig_latency_ms=tig_latency, available_nodes=available_nodes, cpu_capacity=cpu_capacity
        ):
            return False, f"Insufficient resources (nodes={available_nodes}, latency={tig_latency:.1f}ms)"

        # Temporal gating
        time_since_last = time.time() - self.last_esgt_time if self.last_esgt_time > 0 else float("inf")
        recent_count = sum(1 for e in self.event_history[-10:] if time.time() - e.timestamp_start < 1.0)

        if not self.triggers.check_temporal_gating(time_since_last, recent_count):
            return (
                False,
                f"Refractory period violation (time_since_last={time_since_last * 1000:.1f}ms < {self.triggers.refractory_period_ms:.1f}ms)",
            )

        # Arousal check (simulated - would query MCEA)
        arousal = 0.70  # Simulated
        if not self.triggers.check_arousal(arousal):
            return False, f"Arousal too low ({arousal:.2f} < {self.triggers.min_arousal:.2f})"

        return True, ""

    async def _recruit_nodes(self, content: Dict[str, Any]) -> Set[str]:
        """
        Recruit participating nodes for ESGT.

        Selection based on:
        - Relevance to content
        - Current load
        - Connectivity quality
        """
        recruited = set()

        for node_id, node in self.tig.nodes.items():
            # For now, recruit all active nodes
            # In full implementation, would use content-based selection
            if node.node_state.value in ["active", "esgt_mode"]:
                recruited.add(node_id)

        return recruited

    def _build_topology(self, node_ids: Set[str]) -> Dict[str, List[str]]:
        """Build connectivity topology for Kuramoto network."""
        topology = {}

        for node_id in node_ids:
            node = self.tig.nodes.get(node_id)
            if node:
                # Get neighbors that are also participating
                neighbors = [
                    conn.remote_node_id
                    for conn in node.connections.values()
                    if conn.active and conn.remote_node_id in node_ids
                ]
                topology[node_id] = neighbors

        return topology

    async def _sustain_coherence(self, event: ESGTEvent, duration_ms: float, topology: Dict[str, List[str]]) -> None:
        """
        Sustain synchronization for target duration.

        Continuously updates Kuramoto dynamics and monitors coherence.
        """
        start_time = time.time()
        duration_s = duration_ms / 1000.0

        while (time.time() - start_time) < duration_s:
            # Update network
            self.kuramoto.update_network(topology, dt=0.005)

            # Record coherence
            coherence = self.kuramoto.get_coherence()
            if coherence:
                event.coherence_history.append(coherence.order_parameter)

            # Small yield
            await asyncio.sleep(0.005)

    async def _dissolve_event(self, event: ESGTEvent) -> None:
        """Gracefully dissolve synchronization."""
        # Reduce coupling strength gradually
        for osc in self.kuramoto.oscillators.values():
            osc.config.coupling_strength *= 0.5

        # Continue for 50ms with reduced coupling
        topology = self._build_topology(event.participating_nodes)

        for _ in range(10):  # 10 x 5ms = 50ms
            self.kuramoto.update_network(topology, dt=0.005)
            await asyncio.sleep(0.005)

        # Reset oscillators
        self.kuramoto.reset_all()

    def get_success_rate(self) -> float:
        """Get percentage of successful ESGT events."""
        if self.total_events == 0:
            return 0.0
        return self.successful_events / self.total_events

    def get_recent_coherence(self, window: int = 10) -> float:
        """Get average coherence of recent events."""
        recent = self.event_history[-window:]
        if not recent:
            return 0.0

        coherences = [e.achieved_coherence for e in recent if e.success]
        return np.mean(coherences) if coherences else 0.0

    def __repr__(self) -> str:
        return (
            f"ESGTCoordinator(id={self.coordinator_id}, "
            f"events={self.total_events}, "
            f"success_rate={self.get_success_rate():.1%}, "
            f"running={self._running})"
        )
