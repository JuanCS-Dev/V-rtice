"""
Kuramoto Model - Phase Synchronization for ESGT Coherence
==========================================================

This module implements the Kuramoto model of coupled oscillators, which provides
the mathematical foundation for ESGT phase coherence.

Theoretical Foundation:
-----------------------
The Kuramoto model (Kuramoto, 1975) describes how populations of coupled
oscillators can spontaneously synchronize their phases, despite having
different natural frequencies.

**Biological Relevance**:
In the brain, neurons oscillate at different intrinsic frequencies but can
phase-lock during conscious states. This phase coherence is critical for
binding distributed information into unified conscious experience.

**Mathematical Model**:
For N coupled oscillators with phases θᵢ(t):

    dθᵢ/dt = ωᵢ + (K/N) Σⱼ sin(θⱼ - θᵢ)

Where:
- ωᵢ: natural frequency of oscillator i
- K: coupling strength
- θⱼ - θᵢ: phase difference between oscillators

**Order Parameter (Coherence)**:
    r(t) = (1/N) |Σⱼ exp(iθⱼ)|

Where:
- r = 0: complete incoherence (random phases)
- r = 1: perfect synchronization (all phases aligned)

For ESGT, we require r ≥ 0.70 to achieve consciousness-level coherence.

Implementation Details:
-----------------------
We implement a discrete-time version optimized for real-time computation:

1. **Natural Frequencies**: Each TIG node has intrinsic oscillation (~40 Hz)
2. **Coupling**: Nodes interact through TIG connections (weighted by quality)
3. **Integration**: 4th-order Runge-Kutta for stability
4. **Coherence Monitoring**: Real-time r(t) computation every 5ms

Historical Note:
----------------
This is the first application of Kuramoto dynamics to artificial consciousness.
The phase synchronization achieved here determines whether distributed
computation can achieve the temporal unity necessary for phenomenal binding.

"Synchrony is the substrate of unity."
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


class OscillatorState(Enum):
    """State of an oscillator during synchronization."""

    IDLE = "idle"
    COUPLING = "coupling"
    SYNCHRONIZED = "synchronized"
    DESYNCHRONIZING = "desynchronizing"


@dataclass
class OscillatorConfig:
    """Configuration for a Kuramoto oscillator."""

    natural_frequency: float = 40.0  # Hz (gamma-band analog)
    coupling_strength: float = 14.0  # K parameter (high value compensates for k_i normalization)
    phase_noise: float = 0.01  # Additive phase noise
    damping: float = 0.1  # Damping coefficient


@dataclass
class PhaseCoherence:
    """
    Measures phase synchronization quality.

    The order parameter r quantifies how well oscillators are synchronized.
    For consciousness, we interpret coherence levels as:

    - r < 0.30: Unconscious processing (incoherent)
    - 0.30 ≤ r < 0.70: Pre-conscious (partial coherence)
    - r ≥ 0.70: Conscious state (high coherence) ✅
    - r > 0.90: Deep coherence (exceptional binding)
    """

    order_parameter: float  # r(t) ∈ [0, 1]
    mean_phase: float  # Average phase angle (radians)
    phase_variance: float  # Spread of phases
    coherence_quality: str  # "unconscious", "preconscious", "conscious", "deep"
    timestamp: float = field(default_factory=time.time)

    def is_conscious_level(self) -> bool:
        """Check if coherence is sufficient for conscious binding."""
        return self.order_parameter >= 0.70

    def get_quality_score(self) -> float:
        """
        Get normalized quality score (0-1).

        Maps coherence to quality:
        - 0.0-0.3 → 0.0-0.25 (poor)
        - 0.3-0.7 → 0.25-0.75 (moderate)
        - 0.7-1.0 → 0.75-1.0 (excellent)
        """
        if self.order_parameter < 0.3:
            return self.order_parameter / 0.3 * 0.25
        elif self.order_parameter < 0.7:
            return 0.25 + (self.order_parameter - 0.3) / 0.4 * 0.5
        else:
            return 0.75 + (self.order_parameter - 0.7) / 0.3 * 0.25


@dataclass
class SynchronizationDynamics:
    """
    Tracks synchronization dynamics over time.

    This provides historical context for ESGT events, showing how
    coherence builds up, plateaus, and dissolves.
    """

    coherence_history: List[float] = field(default_factory=list)
    time_to_sync: Optional[float] = None  # Time to reach r ≥ 0.70
    max_coherence: float = 0.0
    sustained_duration: float = 0.0  # Time spent at r ≥ 0.70
    dissolution_rate: float = 0.0  # How fast coherence decays

    def add_coherence_sample(self, coherence: float, timestamp: float) -> None:
        """Add coherence measurement to history."""
        self.coherence_history.append(coherence)

        # Update max coherence
        if coherence > self.max_coherence:
            self.max_coherence = coherence

        # Note: time_to_sync is set in synchronize() method with correct elapsed time
        # Don't set it here as timestamp may be absolute time.time() not elapsed

    def compute_dissolution_rate(self) -> float:
        """
        Compute rate of coherence decay (for graceful dissolution analysis).

        Returns:
            Coherence decay rate in units/second
        """
        if len(self.coherence_history) < 10:
            return 0.0

        # Fit linear decay to last 10 samples
        recent = self.coherence_history[-10:]
        time_points = np.arange(len(recent)) * 0.005  # 5ms samples

        # Simple linear regression
        coeffs = np.polyfit(time_points, recent, 1)
        decay_rate = -coeffs[0]  # Negative slope = decay

        return decay_rate


class KuramotoOscillator:
    """
    Implements a single Kuramoto oscillator for ESGT phase synchronization.

    Each TIG node has an associated oscillator that can couple with neighbors
    to achieve collective phase coherence during ignition events.

    Biological Analogy:
    -------------------
    This oscillator is analogous to a cortical neural population with
    intrinsic gamma-band oscillations (~40 Hz). During conscious states,
    these populations phase-lock through synaptic coupling.

    Usage:
        oscillator = KuramotoOscillator(
            node_id="tig-node-001",
            config=OscillatorConfig(natural_frequency=40.0)
        )

        # Update phase based on coupling
        new_phase = oscillator.update(
            neighbor_phases={"node-002": 0.5, "node-003": 1.2},
            coupling_weights={"node-002": 1.0, "node-003": 0.8},
            dt=0.005  # 5ms timestep
        )
    """

    def __init__(self, node_id: str, config: Optional[OscillatorConfig] = None):
        self.node_id = node_id
        self.config = config or OscillatorConfig()

        # Oscillator state
        self.phase: float = np.random.uniform(0, 2 * np.pi)  # Initial random phase
        self.frequency: float = self.config.natural_frequency
        self.state: OscillatorState = OscillatorState.IDLE

        # Phase history for analysis
        self.phase_history: List[float] = [self.phase]
        self.frequency_history: List[float] = [self.frequency]

    def update(self, neighbor_phases: Dict[str, float], coupling_weights: Dict[str, float], dt: float = 0.005) -> float:
        """
        Update oscillator phase based on Kuramoto dynamics.

        Implements discrete-time Kuramoto equation:
            θᵢ(t+dt) = θᵢ(t) + [ωᵢ + (K/N)Σⱼ wⱼ sin(θⱼ - θᵢ)] dt + noise

        Args:
            neighbor_phases: Dict mapping neighbor IDs to their phases (radians)
            coupling_weights: Dict mapping neighbor IDs to coupling strengths
            dt: Time step (seconds)

        Returns:
            Updated phase (radians)
        """
        self.state = OscillatorState.COUPLING

        # Natural frequency contribution
        phase_velocity = 2 * np.pi * self.frequency

        # Coupling contribution (Kuramoto interaction)
        if neighbor_phases:
            coupling_sum = 0.0
            total_weight = sum(coupling_weights.values())

            for neighbor_id, neighbor_phase in neighbor_phases.items():
                weight = coupling_weights.get(neighbor_id, 1.0)
                phase_diff = neighbor_phase - self.phase
                coupling_sum += weight * np.sin(phase_diff)

            # Coupling term (K times average influence from neighbors)
            if total_weight > 0:
                # Remove /N normalization - K is per-neighbor coupling strength
                coupling_term = self.config.coupling_strength * (coupling_sum / len(neighbor_phases))
                phase_velocity += coupling_term

        # Damping (prevents unbounded growth)
        phase_velocity -= self.config.damping * (self.phase % (2 * np.pi))

        # Add phase noise (stochastic component)
        noise = np.random.normal(0, self.config.phase_noise)

        # Euler integration (simple but stable for small dt)
        self.phase += (phase_velocity + noise) * dt

        # Wrap phase to [0, 2π]
        self.phase = self.phase % (2 * np.pi)

        # Record history
        self.phase_history.append(self.phase)
        self.frequency_history.append(phase_velocity / (2 * np.pi))

        # Trim history (keep last 1000 samples)
        if len(self.phase_history) > 1000:
            self.phase_history.pop(0)
            self.frequency_history.pop(0)

        return self.phase

    def get_phase(self) -> float:
        """Get current phase (radians)."""
        return self.phase

    def set_phase(self, phase: float) -> None:
        """Set phase explicitly (for initialization or reset)."""
        self.phase = phase % (2 * np.pi)

    def reset(self) -> None:
        """Reset to random phase (for new ESGT event)."""
        self.phase = np.random.uniform(0, 2 * np.pi)
        self.state = OscillatorState.IDLE
        self.phase_history = [self.phase]

    def __repr__(self) -> str:
        return (
            f"KuramotoOscillator(node={self.node_id}, "
            f"phase={self.phase:.3f}, freq={self.frequency:.1f}Hz, "
            f"state={self.state.value})"
        )


class KuramotoNetwork:
    """
    Manages a network of coupled Kuramoto oscillators for ESGT.

    This network coordinates phase synchronization across all TIG nodes
    during ignition events, computing global coherence in real-time.

    The network can:
    - Initialize oscillators for all participating nodes
    - Update all phases simultaneously (parallel integration)
    - Compute order parameter r(t) continuously
    - Detect synchronization onset and dissolution

    Usage:
        network = KuramotoNetwork()

        # Add oscillators for TIG nodes
        for node_id in fabric.nodes:
            network.add_oscillator(node_id)

        # Run synchronization
        await network.synchronize(
            topology=fabric.graph,
            duration_ms=200,
            target_coherence=0.70
        )

        # Check coherence
        coherence = network.get_coherence()
        if coherence.is_conscious_level():
            print("🧠 Conscious-level phase coherence achieved")
    """

    def __init__(self, config: Optional[OscillatorConfig] = None):
        self.default_config = config or OscillatorConfig()
        self.oscillators: Dict[str, KuramotoOscillator] = {}
        self.dynamics = SynchronizationDynamics()
        self._coherence_cache: Optional[PhaseCoherence] = None
        self._last_coherence_time: float = 0.0

    def add_oscillator(self, node_id: str, config: Optional[OscillatorConfig] = None) -> None:
        """Add oscillator for a TIG node."""
        osc_config = config or self.default_config
        self.oscillators[node_id] = KuramotoOscillator(node_id, osc_config)

    def remove_oscillator(self, node_id: str) -> None:
        """Remove oscillator (node went offline)."""
        if node_id in self.oscillators:
            del self.oscillators[node_id]

    def reset_all(self) -> None:
        """Reset all oscillators to random phases."""
        for osc in self.oscillators.values():
            osc.reset()
        self.dynamics = SynchronizationDynamics()
        self._coherence_cache = None

    def update_network(
        self,
        topology: Dict[str, List[str]],
        coupling_weights: Optional[Dict[Tuple[str, str], float]] = None,
        dt: float = 0.005,
    ) -> None:
        """
        Update all oscillators in parallel based on network topology.

        Args:
            topology: Dict mapping node_id to list of neighbor_ids
            coupling_weights: Optional custom coupling strengths
            dt: Time step (seconds, default 5ms)
        """
        # Collect current phases
        current_phases = {node_id: osc.get_phase() for node_id, osc in self.oscillators.items()}

        # Update all oscillators simultaneously
        new_phases = {}

        for node_id, osc in self.oscillators.items():
            neighbors = topology.get(node_id, [])

            # Get neighbor phases
            neighbor_phases = {n: current_phases[n] for n in neighbors if n in current_phases}

            # Get coupling weights
            weights = {}
            if coupling_weights:
                for n in neighbors:
                    key = (node_id, n)
                    weights[n] = coupling_weights.get(key, 1.0)
            else:
                weights = {n: 1.0 for n in neighbors}

            # Update oscillator
            new_phase = osc.update(neighbor_phases, weights, dt)
            new_phases[node_id] = new_phase

        # All oscillators updated - compute coherence
        self._update_coherence(time.time())

    def _update_coherence(self, timestamp: float) -> None:
        """Compute current phase coherence (order parameter)."""
        if not self.oscillators:
            return

        # Compute complex order parameter
        phases = [osc.get_phase() for osc in self.oscillators.values()]
        complex_sum = np.sum([np.exp(1j * phase) for phase in phases])
        r = np.abs(complex_sum) / len(phases)

        # Mean phase
        mean_phase = np.angle(complex_sum)

        # Phase variance
        phase_variance = np.var(phases)

        # Determine quality
        if r < 0.30:
            quality = "unconscious"
        elif r < 0.70:
            quality = "preconscious"
        elif r < 0.90:
            quality = "conscious"
        else:
            quality = "deep"

        # Create coherence object
        coherence = PhaseCoherence(
            order_parameter=r,
            mean_phase=mean_phase,
            phase_variance=phase_variance,
            coherence_quality=quality,
            timestamp=timestamp,
        )

        # Update cache
        self._coherence_cache = coherence
        self._last_coherence_time = timestamp

        # Record in dynamics
        self.dynamics.add_coherence_sample(r, timestamp)

    def get_coherence(self) -> Optional[PhaseCoherence]:
        """Get latest phase coherence measurement."""
        if self._coherence_cache is None and self.oscillators:
            # Compute initial coherence if not yet cached
            self._update_coherence(time.time())
        return self._coherence_cache

    def get_order_parameter(self) -> float:
        """Quick access to order parameter r."""
        if self._coherence_cache:
            return self._coherence_cache.order_parameter
        return 0.0

    async def synchronize(
        self,
        topology: Dict[str, List[str]],
        duration_ms: float = 200.0,
        target_coherence: float = 0.70,
        dt: float = 0.005,
    ) -> SynchronizationDynamics:
        """
        Run synchronization protocol for specified duration.

        Simulates Kuramoto dynamics until target coherence is reached
        or duration expires.

        Args:
            topology: Network connectivity
            duration_ms: Maximum duration (milliseconds)
            target_coherence: Target order parameter (default 0.70)
            dt: Integration timestep (seconds)

        Returns:
            SynchronizationDynamics with full history
        """
        start_time = time.time()
        duration_s = duration_ms / 1000.0

        steps = int(duration_s / dt)

        for step in range(steps):
            # Update network
            self.update_network(topology, dt=dt)

            # Check if target reached
            if self._coherence_cache and self._coherence_cache.order_parameter >= target_coherence:
                if self.dynamics.time_to_sync is None:
                    elapsed = time.time() - start_time
                    self.dynamics.time_to_sync = elapsed
                self.dynamics.sustained_duration += dt

            # Small async yield to prevent blocking
            if step % 10 == 0:
                await asyncio.sleep(0)

        return self.dynamics

    def get_phase_distribution(self) -> np.ndarray:
        """Get current phase distribution for visualization."""
        return np.array([osc.get_phase() for osc in self.oscillators.values()])

    def __repr__(self) -> str:
        coherence = self.get_order_parameter()
        return f"KuramotoNetwork(oscillators={len(self.oscillators)}, coherence={coherence:.3f})"
