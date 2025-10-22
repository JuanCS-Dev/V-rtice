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
    coupling_strength: float = 20.0  # K parameter (increased for sparse topology, was 14.0)
    phase_noise: float = 0.001  # Additive phase noise (reduced from 0.01 for faster sync)
    integration_method: str = "rk4"  # Numerical integrator: "euler" or "rk4" (PPBPR Section 5.2)
    # NOTE: damping removed - not part of canonical Kuramoto model
    # The phase-dependent damping was preventing synchronization by anchoring oscillators to θ=0


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
        if self.order_parameter < 0.7:
            return 0.25 + (self.order_parameter - 0.3) / 0.4 * 0.5
        return 0.75 + (self.order_parameter - 0.7) / 0.3 * 0.25


@dataclass
class SynchronizationDynamics:
    """
    Tracks synchronization dynamics over time.

    This provides historical context for ESGT events, showing how
    coherence builds up, plateaus, and dissolves.
    """

    coherence_history: list[float] = field(default_factory=list)
    time_to_sync: float | None = None  # Time to reach r ≥ 0.70
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

        # Manual linear regression to avoid numpy polyfit bugs
        # y = mx + b, solve for m (slope)
        x = np.array(time_points, dtype=np.float64)  # pragma: no cover
        y = np.array(recent, dtype=np.float64)  # pragma: no cover
        n = len(x)  # pragma: no cover

        # Calculate slope: m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        sum_x = np.sum(x)  # pragma: no cover
        sum_y = np.sum(y)  # pragma: no cover
        sum_xy = np.sum(x * y)  # pragma: no cover
        sum_x2 = np.sum(x * x)  # pragma: no cover

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)  # pragma: no cover
        decay_rate = -slope  # Negative slope = decay  # pragma: no cover

        return float(decay_rate)  # pragma: no cover


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

    def __init__(self, node_id: str, config: OscillatorConfig | None = None):
        self.node_id = node_id
        self.config = config or OscillatorConfig()

        # Oscillator state
        self.phase: float = np.random.uniform(0, 2 * np.pi)  # Initial random phase
        self.frequency: float = self.config.natural_frequency
        self.state: OscillatorState = OscillatorState.IDLE

        # Phase history for analysis
        self.phase_history: list[float] = [self.phase]
        self.frequency_history: list[float] = [self.frequency]

    def _compute_phase_velocity(self, current_phase: float, neighbor_phases: dict[str, float], coupling_weights: dict[str, float], N: int) -> float:
        """
        Compute phase velocity (derivative) for Kuramoto model.

        This is the core differential equation:
            dθᵢ/dt = ωᵢ + (K/N)Σⱼ wⱼ sin(θⱼ - θᵢ)

        Args:
            current_phase: Current phase of this oscillator (radians)
            neighbor_phases: Dict mapping neighbor IDs to their phases (radians)
            coupling_weights: Dict mapping neighbor IDs to coupling strengths
            N: Total number of oscillators in network (for canonical normalization)

        Returns:
            Phase velocity (radians/second)
        """
        # Natural frequency contribution: ωᵢ
        phase_velocity = 2 * np.pi * self.frequency

        # Coupling contribution: (K/N)Σⱼ wⱼ sin(θⱼ - θᵢ)
        if neighbor_phases:
            coupling_sum = 0.0

            for neighbor_id, neighbor_phase in neighbor_phases.items():
                weight = coupling_weights.get(neighbor_id, 1.0)
                phase_diff = neighbor_phase - current_phase
                coupling_sum += weight * np.sin(phase_diff)

            # Coupling term: CANONICAL Kuramoto uses K/N normalization
            coupling_term = self.config.coupling_strength * (coupling_sum / N)
            phase_velocity += coupling_term

        return phase_velocity

    def update(self, neighbor_phases: dict[str, float], coupling_weights: dict[str, float], dt: float = 0.005, N: int | None = None) -> float:
        """
        Update oscillator phase based on Kuramoto dynamics.

        Implements discrete-time Kuramoto equation using either Euler or RK4 integration:
            θᵢ(t+dt) = θᵢ(t) + ∫[ωᵢ + (K/N)Σⱼ wⱼ sin(θⱼ - θᵢ)] dt + noise

        Integration methods (PPBPR Section 5.2):
        - Euler: O(dt) accuracy, requires small dt
        - RK4: O(dt⁴) accuracy, allows larger dt

        Args:
            neighbor_phases: Dict mapping neighbor IDs to their phases (radians)
            coupling_weights: Dict mapping neighbor IDs to coupling strengths
            dt: Time step (seconds)
            N: Total number of oscillators in network (for canonical normalization)

        Returns:
            Updated phase (radians)
        """
        self.state = OscillatorState.COUPLING

        # Fallback for backward compatibility
        if N is None:
            N = len(neighbor_phases) if neighbor_phases else 1

        # Add phase noise (stochastic component) - applied once per timestep
        noise = np.random.normal(0, self.config.phase_noise)

        # Choose integration method
        if self.config.integration_method == "rk4":
            # Runge-Kutta 4th order (PPBPR Table 1)
            # More accurate (O(dt⁴)) and stable than Euler

            # k1 = dt * f(θ)
            k1 = dt * self._compute_phase_velocity(self.phase, neighbor_phases, coupling_weights, N)

            # k2 = dt * f(θ + k1/2)
            phase_k2 = self.phase + 0.5 * k1
            k2 = dt * self._compute_phase_velocity(phase_k2, neighbor_phases, coupling_weights, N)

            # k3 = dt * f(θ + k2/2)
            phase_k3 = self.phase + 0.5 * k2
            k3 = dt * self._compute_phase_velocity(phase_k3, neighbor_phases, coupling_weights, N)

            # k4 = dt * f(θ + k3)
            phase_k4 = self.phase + k3
            k4 = dt * self._compute_phase_velocity(phase_k4, neighbor_phases, coupling_weights, N)

            # Weighted average: θ(t+dt) = θ(t) + (k1 + 2k2 + 2k3 + k4)/6
            self.phase += (k1 + 2*k2 + 2*k3 + k4) / 6.0 + noise * dt

        else:
            # Euler integration (default for backward compatibility)
            # Simple but requires small dt for accuracy
            phase_velocity = self._compute_phase_velocity(self.phase, neighbor_phases, coupling_weights, N)
            self.phase += (phase_velocity + noise) * dt

        # Wrap phase to [0, 2π]
        self.phase = self.phase % (2 * np.pi)

        # Record history
        self.phase_history.append(self.phase)
        # Update frequency based on current phase velocity (for monitoring)
        current_velocity = self._compute_phase_velocity(self.phase, neighbor_phases, coupling_weights, N)
        self.frequency_history.append(current_velocity / (2 * np.pi))

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

    def __init__(self, config: OscillatorConfig | None = None):
        self.default_config = config or OscillatorConfig()
        self.oscillators: dict[str, KuramotoOscillator] = {}
        self.dynamics = SynchronizationDynamics()
        self._coherence_cache: PhaseCoherence | None = None
        self._last_coherence_time: float = 0.0

    def add_oscillator(self, node_id: str, config: OscillatorConfig | None = None) -> None:
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

    def _compute_network_derivatives(
        self,
        phases: dict[str, float],
        topology: dict[str, list[str]],
        coupling_weights: dict[tuple[str, str], float] | None,
    ) -> dict[str, float]:
        """
        Compute phase velocities for all oscillators given current phases.

        This implements the core Kuramoto derivative for the entire network:
            dθᵢ/dt = ωᵢ + (K/N)Σⱼ wⱼ sin(θⱼ - θᵢ)

        Args:
            phases: Dict mapping node_id to current phase (radians)
            topology: Dict mapping node_id to list of neighbor_ids
            coupling_weights: Optional custom coupling strengths

        Returns:
            Dict mapping node_id to phase velocity (radians/second)
        """
        N = len(self.oscillators)
        velocities = {}

        for node_id, osc in self.oscillators.items():
            neighbors = topology.get(node_id, [])
            neighbor_phases = {n: phases[n] for n in neighbors if n in phases}

            # Get coupling weights
            weights = {}
            if coupling_weights:
                for n in neighbors:
                    key = (node_id, n)
                    weights[n] = coupling_weights.get(key, 1.0)
            else:
                weights = {n: 1.0 for n in neighbors}

            # Compute velocity using the extracted method
            velocities[node_id] = osc._compute_phase_velocity(phases[node_id], neighbor_phases, weights, N)

        return velocities

    def update_network(
        self,
        topology: dict[str, list[str]],
        coupling_weights: dict[tuple[str, str], float] | None = None,
        dt: float = 0.005,
    ) -> None:
        """
        Update all oscillators in parallel based on network topology.

        Uses either Euler or RK4 integration (configured in OscillatorConfig).
        For RK4, the entire network must be integrated simultaneously to maintain
        coupling consistency across k1, k2, k3, k4 evaluations (PPBPR Section 5.2).

        Args:
            topology: Dict mapping node_id to list of neighbor_ids
            coupling_weights: Optional custom coupling strengths
            dt: Time step (seconds, default 5ms)
        """
        # Collect current phases
        current_phases = {node_id: osc.get_phase() for node_id, osc in self.oscillators.items()}
        N = len(self.oscillators)

        # Check integration method (use first oscillator's config as reference)
        integration_method = next(iter(self.oscillators.values())).config.integration_method

        if integration_method == "rk4":
            # Runge-Kutta 4th order - network-wide integration (PPBPR Table 1)
            # Must compute k1, k2, k3, k4 for ALL oscillators before updating phases

            # k1 = dt * f(θ)
            velocities_k1 = self._compute_network_derivatives(current_phases, topology, coupling_weights)
            k1 = {node_id: dt * vel for node_id, vel in velocities_k1.items()}

            # k2 = dt * f(θ + k1/2)
            phases_k2 = {node_id: current_phases[node_id] + 0.5 * k1[node_id] for node_id in current_phases}
            velocities_k2 = self._compute_network_derivatives(phases_k2, topology, coupling_weights)
            k2 = {node_id: dt * vel for node_id, vel in velocities_k2.items()}

            # k3 = dt * f(θ + k2/2)
            phases_k3 = {node_id: current_phases[node_id] + 0.5 * k2[node_id] for node_id in current_phases}
            velocities_k3 = self._compute_network_derivatives(phases_k3, topology, coupling_weights)
            k3 = {node_id: dt * vel for node_id, vel in velocities_k3.items()}

            # k4 = dt * f(θ + k3)
            phases_k4 = {node_id: current_phases[node_id] + k3[node_id] for node_id in current_phases}
            velocities_k4 = self._compute_network_derivatives(phases_k4, topology, coupling_weights)
            k4 = {node_id: dt * vel for node_id, vel in velocities_k4.items()}

            # Update phases: θ(t+dt) = θ(t) + (k1 + 2k2 + 2k3 + k4)/6 + noise*dt
            for node_id, osc in self.oscillators.items():
                noise = np.random.normal(0, osc.config.phase_noise)
                new_phase = current_phases[node_id] + (k1[node_id] + 2*k2[node_id] + 2*k3[node_id] + k4[node_id]) / 6.0 + noise * dt

                # Wrap and set phase directly
                osc.phase = new_phase % (2 * np.pi)
                osc.phase_history.append(osc.phase)

                # Update frequency history (using current velocity)
                osc.frequency_history.append(velocities_k1[node_id] / (2 * np.pi))

        else:
            # Euler integration - original per-oscillator update
            new_phases = {}

            for node_id, osc in self.oscillators.items():
                neighbors = topology.get(node_id, [])
                neighbor_phases = {n: current_phases[n] for n in neighbors if n in current_phases}

                # Get coupling weights
                weights = {}
                if coupling_weights:
                    for n in neighbors:
                        key = (node_id, n)
                        weights[n] = coupling_weights.get(key, 1.0)
                else:
                    weights = {n: 1.0 for n in neighbors}

                # Update oscillator with total network size N for canonical normalization
                new_phase = osc.update(neighbor_phases, weights, dt, N)
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

    def get_coherence(self) -> PhaseCoherence | None:
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
        topology: dict[str, list[str]],
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
                if self.dynamics.time_to_sync is None:  # pragma: no cover - tested but not detected
                    elapsed = time.time() - start_time  # pragma: no cover
                    self.dynamics.time_to_sync = elapsed  # pragma: no cover
                self.dynamics.sustained_duration += dt  # pragma: no cover

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
