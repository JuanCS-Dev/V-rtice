"""
MMEI Internal State Monitor - Interoception Implementation
============================================================

This module implements computational interoception - the ability to sense
and interpret internal physical/computational states as abstract needs.

Theoretical Foundation:
-----------------------
Biological interoception involves specialized receptors monitoring:
- Cardiovascular state (baroreceptors)
- Respiratory state (chemoreceptors)
- Metabolic state (glucose sensors)
- Thermal state (thermoreceptors)
- Visceral state (mechanoreceptors)

These signals are integrated in:
- Insula cortex: Primary interoceptive hub
- Anterior cingulate: Affective interpretation
- Hypothalamus: Homeostatic regulation

The result is phenomenal experience of bodily states ("feelings"):
- Hunger, thirst, fatigue, pain, comfort

Computational Translation:
---------------------------
MMEI translates computational metrics into abstract needs:

Physical Metrics          → Abstract Needs
----------------            ----------------
CPU usage (%)            → rest_need (computational fatigue)
Memory pressure (%)      → rest_need (resource exhaustion)
Error rate (errors/min)  → repair_need (system integrity)
Temperature (°C)         → efficiency_need (thermal stress)
Power draw (W)           → efficiency_need (energy conservation)
Network latency (ms)     → connectivity_need (isolation/lag)
Packet loss (%)          → connectivity_need (communication failure)
CPU idle time (%)        → curiosity_drive (underutilization → exploration)

This translation enables:
1. Autonomous motivation: Needs generate goals internally
2. Embodied cognition: Behavior grounded in "physical" state
3. Homeostatic regulation: Self-maintenance without external commands
4. Phenomenal grounding: "Feeling" states as foundation for awareness

Integration with Consciousness:
--------------------------------
MMEI feeds into ESGT via salience computation:
- High needs elevate salience of related content
- Critical needs (repair_need > 0.9) force ESGT ignition
- Curiosity drive enables spontaneous exploration during idle

Example:
  CPU usage → 95% sustained
  → rest_need = 0.95 (critical)
  → Goal: "reduce_load" with priority CRITICAL
  → ESGT ignited to broadcast need globally
  → HCL receives goal, triggers load shedding

Historical Context:
-------------------
First computational implementation of interoception for AI consciousness.
Enables "feeling" as foundation for embodied artificial experience.

"The body is not separate from the mind - it is the foundation of mind."
- Antonio Damasio, "Descartes' Error" (1994)

Implementation Notes:
---------------------
- Integrates with HCL (Homeostatic Control Loop) from FASE 1
- Metrics collection at ~10 Hz (100ms intervals)
- Need computation uses moving averages to prevent oscillation
- Threshold-based urgency classification
- Zero external dependencies for core functionality
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np


class NeedUrgency(Enum):
    """Classification of need urgency levels."""

    SATISFIED = "satisfied"  # need < 0.20 - no action required
    LOW = "low"  # 0.20 ≤ need < 0.40 - background concern
    MODERATE = "moderate"  # 0.40 ≤ need < 0.60 - should address soon
    HIGH = "high"  # 0.60 ≤ need < 0.80 - requires attention
    CRITICAL = "critical"  # need ≥ 0.80 - immediate action needed


@dataclass
class PhysicalMetrics:
    """
    Raw physical/computational metrics collected from system.

    These are the "receptor signals" analogous to biological interoception.
    Values are normalized to [0, 1] range where possible.
    """

    # Computational load
    cpu_usage_percent: float = 0.0  # 0-100 → normalized to 0-1
    memory_usage_percent: float = 0.0  # 0-100 → normalized to 0-1

    # System health
    error_rate_per_min: float = 0.0  # Errors detected per minute
    exception_count: int = 0  # Recent exceptions

    # Physical state (if available)
    temperature_celsius: Optional[float] = None  # CPU/system temp
    power_draw_watts: Optional[float] = None  # Power consumption

    # Network state
    network_latency_ms: float = 0.0  # Average latency
    packet_loss_percent: float = 0.0  # 0-100 → normalized to 0-1

    # Activity level
    idle_time_percent: float = 0.0  # 0-100 → normalized to 0-1
    throughput_ops_per_sec: float = 0.0  # Operations processed

    # Metadata
    timestamp: float = field(default_factory=time.time)
    collection_latency_ms: float = 0.0  # Time to collect metrics

    def normalize(self) -> "PhysicalMetrics":
        """Ensure all percentage values are in [0, 1] range."""
        return PhysicalMetrics(
            cpu_usage_percent=min(self.cpu_usage_percent / 100.0, 1.0),
            memory_usage_percent=min(self.memory_usage_percent / 100.0, 1.0),
            error_rate_per_min=self.error_rate_per_min,
            exception_count=self.exception_count,
            temperature_celsius=self.temperature_celsius,
            power_draw_watts=self.power_draw_watts,
            network_latency_ms=self.network_latency_ms,
            packet_loss_percent=min(self.packet_loss_percent / 100.0, 1.0),
            idle_time_percent=min(self.idle_time_percent / 100.0, 1.0),
            throughput_ops_per_sec=self.throughput_ops_per_sec,
            timestamp=self.timestamp,
            collection_latency_ms=self.collection_latency_ms,
        )


@dataclass
class AbstractNeeds:
    """
    Abstract psychological/phenomenal needs derived from physical metrics.

    This is the "feeling" layer - the phenomenal experience of bodily state.
    All values normalized to [0, 1] where 1.0 = maximum need.

    Biological Correspondence:
    - rest_need: Fatigue sensation
    - repair_need: Pain/discomfort signaling damage
    - efficiency_need: Thermal discomfort, energy depletion
    - connectivity_need: Social isolation feeling
    - curiosity_drive: Boredom, exploration urge
    """

    # Primary needs (deficit-based)
    rest_need: float = 0.0  # Need to reduce computational load
    repair_need: float = 0.0  # Need to fix errors/integrity issues
    efficiency_need: float = 0.0  # Need to optimize resource usage
    connectivity_need: float = 0.0  # Need to improve communication

    # Growth needs (exploration-based)
    curiosity_drive: float = 0.0  # Drive to explore when idle
    learning_drive: float = 0.0  # Drive to acquire new patterns

    # Metadata
    timestamp: float = field(default_factory=time.time)

    def get_most_urgent(self) -> tuple[str, float, NeedUrgency]:
        """
        Get the most urgent need.

        Returns:
            (need_name, need_value, urgency_level)
        """
        needs = {
            "rest_need": self.rest_need,
            "repair_need": self.repair_need,
            "efficiency_need": self.efficiency_need,
            "connectivity_need": self.connectivity_need,
            "curiosity_drive": self.curiosity_drive,
            "learning_drive": self.learning_drive,
        }

        most_urgent_name = max(needs.keys(), key=lambda k: needs[k])
        most_urgent_value = needs[most_urgent_name]
        urgency = self._classify_urgency(most_urgent_value)

        return (most_urgent_name, most_urgent_value, urgency)

    def get_critical_needs(self, threshold: float = 0.80) -> List[tuple[str, float]]:
        """Get all needs above critical threshold."""
        needs = {
            "rest_need": self.rest_need,
            "repair_need": self.repair_need,
            "efficiency_need": self.efficiency_need,
            "connectivity_need": self.connectivity_need,
        }

        return [(name, value) for name, value in needs.items() if value >= threshold]

    def _classify_urgency(self, need_value: float) -> NeedUrgency:
        """Classify urgency level based on need value."""
        if need_value < 0.20:
            return NeedUrgency.SATISFIED
        elif need_value < 0.40:
            return NeedUrgency.LOW
        elif need_value < 0.60:
            return NeedUrgency.MODERATE
        elif need_value < 0.80:
            return NeedUrgency.HIGH
        else:
            return NeedUrgency.CRITICAL

    def __repr__(self) -> str:
        most_urgent, value, urgency = self.get_most_urgent()
        return f"AbstractNeeds(most_urgent={most_urgent}={value:.2f}, urgency={urgency.value})"


@dataclass
class InteroceptionConfig:
    """Configuration for internal state monitoring."""

    # Collection intervals
    collection_interval_ms: float = 100.0  # 10 Hz default

    # Moving average windows
    short_term_window_samples: int = 10  # 1 second at 10 Hz
    long_term_window_samples: int = 50  # 5 seconds at 10 Hz

    # Need computation weights
    cpu_weight: float = 0.6  # CPU contributes 60% to rest_need
    memory_weight: float = 0.4  # Memory contributes 40% to rest_need

    # Thresholds
    error_rate_critical: float = 10.0  # 10 errors/min = critical
    temperature_warning_celsius: float = 80.0
    latency_warning_ms: float = 100.0

    # Curiosity parameters
    idle_curiosity_threshold: float = 0.70  # 70% idle → curiosity activates
    curiosity_growth_rate: float = 0.01  # Per-cycle curiosity increase when idle


class InternalStateMonitor:
    """
    Monitors internal physical/computational state and translates to abstract needs.

    This is the core interoception engine - continuously collecting physical
    metrics and computing phenomenal "feelings" (abstract needs).

    Architecture:
    -------------
    Physical Layer:
      ↓ (metrics collection)
    PhysicalMetrics
      ↓ (translation)
    AbstractNeeds
      ↓ (goal generation)
    Autonomous Goals → ESGT → HCL

    The monitor runs continuously in background (~10 Hz), maintaining
    moving averages to prevent oscillation and computing needs based on
    both short-term and long-term trends.

    Integration Points:
    -------------------
    - HCL: Receives goals generated from needs
    - ESGT: Critical needs elevate salience, force ignition
    - Attention: Needs bias attention toward relevant stimuli

    Usage:
    ------
        monitor = InternalStateMonitor(config)

        # Provide metrics collector
        async def collect_metrics() -> PhysicalMetrics:
            return PhysicalMetrics(
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_percent=psutil.virtual_memory().percent,
                # ...
            )

        monitor.set_metrics_collector(collect_metrics)
        await monitor.start()

        # Get current needs
        needs = monitor.get_current_needs()
        print(f"Most urgent: {needs.get_most_urgent()}")

        # Register callback for critical needs
        async def handle_critical(needs: AbstractNeeds):
            print(f"CRITICAL: {needs.get_critical_needs()}")

        monitor.register_need_callback(handle_critical, threshold=0.80)

    Historical Note:
    ----------------
    First implementation of computational interoception for artificial consciousness.
    Enables embodied cognition through grounding in "physical" substrate.

    "Consciousness is not just in the head - it is in the body."
    """

    def __init__(self, config: Optional[InteroceptionConfig] = None, monitor_id: str = "mmei-monitor-primary"):
        self.monitor_id = monitor_id
        self.config = config or InteroceptionConfig()

        # State
        self._running: bool = False
        self._monitoring_task: Optional[asyncio.Task] = None

        # Metrics history
        self._metrics_history: List[PhysicalMetrics] = []
        self._needs_history: List[AbstractNeeds] = []

        # Current state
        self._current_metrics: Optional[PhysicalMetrics] = None
        self._current_needs: Optional[AbstractNeeds] = None

        # Metrics collection
        self._metrics_collector: Optional[Callable[[], PhysicalMetrics]] = None

        # Callbacks
        self._need_callbacks: List[tuple[Callable, float]] = []  # (callback, threshold)

        # Performance tracking
        self.total_collections: int = 0
        self.failed_collections: int = 0
        self.callback_invocations: int = 0

        # Curiosity state
        self._accumulated_curiosity: float = 0.0
        self._last_curiosity_reset: float = time.time()

    def set_metrics_collector(self, collector: Callable[[], PhysicalMetrics]) -> None:
        """
        Set the metrics collection function.

        The collector should return PhysicalMetrics with current system state.
        Can be sync or async function.

        Args:
            collector: Function returning PhysicalMetrics
        """
        self._metrics_collector = collector

    def register_need_callback(self, callback: Callable[[AbstractNeeds], None], threshold: float = 0.80) -> None:
        """
        Register callback invoked when any need exceeds threshold.

        Args:
            callback: Async function to call with AbstractNeeds
            threshold: Need value that triggers callback (0-1)
        """
        self._need_callbacks.append((callback, threshold))

    async def start(self) -> None:
        """Start continuous interoception monitoring."""
        if self._running:
            return

        if not self._metrics_collector:
            raise RuntimeError("No metrics collector set. Call set_metrics_collector() first.")

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        print(f"🧠 MMEI Monitor {self.monitor_id} started (interoception active)")

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        print(f"🛑 MMEI Monitor {self.monitor_id} stopped")

    async def _monitoring_loop(self) -> None:
        """
        Continuous monitoring loop.

        Collects metrics, computes needs, invokes callbacks.
        Runs at configured interval (~10 Hz default).
        """
        interval = self.config.collection_interval_ms / 1000.0

        while self._running:
            try:
                cycle_start = time.time()

                # Collect metrics
                metrics = await self._collect_metrics()

                if metrics:
                    # Store in history
                    self._metrics_history.append(metrics)
                    if len(self._metrics_history) > self.config.long_term_window_samples:
                        self._metrics_history.pop(0)

                    self._current_metrics = metrics

                    # Compute needs
                    needs = self._compute_needs(metrics)

                    # Store in history
                    self._needs_history.append(needs)
                    if len(self._needs_history) > self.config.long_term_window_samples:
                        self._needs_history.pop(0)

                    self._current_needs = needs

                    # Invoke callbacks if thresholds exceeded
                    await self._invoke_callbacks(needs)

                    self.total_collections += 1

                # Sleep until next cycle
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, interval - cycle_duration)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.failed_collections += 1
                print(f"⚠️  MMEI collection error: {e}")
                await asyncio.sleep(interval)

    async def _collect_metrics(self) -> Optional[PhysicalMetrics]:
        """Collect current physical metrics."""
        try:
            start = time.time()

            # Call collector (may be sync or async)
            if asyncio.iscoroutinefunction(self._metrics_collector):
                metrics = await self._metrics_collector()
            else:
                metrics = self._metrics_collector()

            # Record collection latency
            metrics.collection_latency_ms = (time.time() - start) * 1000.0

            # Normalize percentages
            return metrics.normalize()

        except Exception as e:
            self.failed_collections += 1
            print(f"⚠️  Metrics collection failed: {e}")
            return None

    def _compute_needs(self, metrics: PhysicalMetrics) -> AbstractNeeds:
        """
        Translate physical metrics to abstract needs.

        This is the core interoception computation - the phenomenal
        translation from physical state to "feeling".

        Args:
            metrics: Current PhysicalMetrics

        Returns:
            AbstractNeeds computed from metrics
        """
        # REST NEED: Computational load/fatigue
        # Weighted combination of CPU and memory pressure
        rest_need = (
            self.config.cpu_weight * metrics.cpu_usage_percent
            + self.config.memory_weight * metrics.memory_usage_percent
        )

        # REPAIR NEED: Error rate and system integrity
        # Normalize error rate to [0, 1] using critical threshold
        error_rate_normalized = min(metrics.error_rate_per_min / self.config.error_rate_critical, 1.0)

        # Exception count contributes (saturates at 10 exceptions)
        exception_contribution = min(metrics.exception_count / 10.0, 1.0)

        repair_need = max(error_rate_normalized, exception_contribution)

        # EFFICIENCY NEED: Thermal and power state
        efficiency_need = 0.0

        if metrics.temperature_celsius is not None:
            # Temperature above warning threshold elevates efficiency need
            if metrics.temperature_celsius > self.config.temperature_warning_celsius:
                temp_excess = metrics.temperature_celsius - self.config.temperature_warning_celsius
                temp_contribution = min(temp_excess / 20.0, 1.0)  # Saturate at +20°C
                efficiency_need = max(efficiency_need, temp_contribution)

        if metrics.power_draw_watts is not None:
            # High power draw (>100W as baseline) elevates efficiency need
            if metrics.power_draw_watts > 100.0:
                power_contribution = min((metrics.power_draw_watts - 100.0) / 100.0, 1.0)
                efficiency_need = max(efficiency_need, power_contribution)

        # CONNECTIVITY NEED: Network state
        # Latency above warning threshold
        latency_contribution = 0.0
        if metrics.network_latency_ms > self.config.latency_warning_ms:
            latency_excess = metrics.network_latency_ms - self.config.latency_warning_ms
            latency_contribution = min(latency_excess / 100.0, 1.0)  # Saturate at +100ms

        # Packet loss
        packet_loss_contribution = metrics.packet_loss_percent

        connectivity_need = max(latency_contribution, packet_loss_contribution)

        # CURIOSITY DRIVE: Idle time → exploration urge
        # When CPU is idle, curiosity accumulates over time
        if metrics.idle_time_percent > self.config.idle_curiosity_threshold:
            # Curiosity grows when idle
            self._accumulated_curiosity = min(self._accumulated_curiosity + self.config.curiosity_growth_rate, 1.0)
        else:
            # Reset when active
            self._accumulated_curiosity = 0.0

        curiosity_drive = self._accumulated_curiosity

        # LEARNING DRIVE: Low throughput → seek new patterns
        # Inverse of throughput (normalized)
        # Low throughput suggests underutilization → opportunity to learn
        if metrics.throughput_ops_per_sec < 10.0:  # Arbitrary baseline
            learning_drive = 0.5  # Moderate drive when throughput low
        else:
            learning_drive = 0.1  # Low baseline drive

        return AbstractNeeds(
            rest_need=float(np.clip(rest_need, 0.0, 1.0)),
            repair_need=float(np.clip(repair_need, 0.0, 1.0)),
            efficiency_need=float(np.clip(efficiency_need, 0.0, 1.0)),
            connectivity_need=float(np.clip(connectivity_need, 0.0, 1.0)),
            curiosity_drive=float(np.clip(curiosity_drive, 0.0, 1.0)),
            learning_drive=float(np.clip(learning_drive, 0.0, 1.0)),
            timestamp=time.time(),
        )

    async def _invoke_callbacks(self, needs: AbstractNeeds) -> None:
        """Invoke registered callbacks if thresholds exceeded."""
        # Check if any need exceeds any callback threshold
        max_need = max(
            [
                needs.rest_need,
                needs.repair_need,
                needs.efficiency_need,
                needs.connectivity_need,
            ]
        )

        for callback, threshold in self._need_callbacks:
            if max_need >= threshold:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(needs)
                    else:
                        callback(needs)

                    self.callback_invocations += 1

                except Exception as e:
                    print(f"⚠️  Need callback error: {e}")

    def get_current_needs(self) -> Optional[AbstractNeeds]:
        """Get most recent computed needs."""
        return self._current_needs

    def get_current_metrics(self) -> Optional[PhysicalMetrics]:
        """Get most recent collected metrics."""
        return self._current_metrics

    def get_needs_trend(self, need_name: str, window_samples: Optional[int] = None) -> List[float]:
        """
        Get historical trend for specific need.

        Args:
            need_name: Name of need (e.g., "rest_need")
            window_samples: Number of samples to retrieve (None = all)

        Returns:
            List of need values in chronological order
        """
        if window_samples is None:
            history = self._needs_history
        else:
            history = self._needs_history[-window_samples:]

        return [getattr(needs, need_name, 0.0) for needs in history]

    def get_moving_average(self, need_name: str, window_samples: Optional[int] = None) -> float:
        """
        Get moving average of specific need.

        Args:
            need_name: Name of need
            window_samples: Window size (None = use short_term_window)

        Returns:
            Average need value over window
        """
        if window_samples is None:
            window_samples = self.config.short_term_window_samples

        trend = self.get_needs_trend(need_name, window_samples)

        if not trend:
            return 0.0

        return float(np.mean(trend))

    def get_statistics(self) -> Dict[str, any]:
        """Get monitor performance statistics."""
        success_rate = (
            (self.total_collections - self.failed_collections) / self.total_collections
            if self.total_collections > 0
            else 0.0
        )

        return {
            "monitor_id": self.monitor_id,
            "running": self._running,
            "total_collections": self.total_collections,
            "failed_collections": self.failed_collections,
            "success_rate": success_rate,
            "callback_invocations": self.callback_invocations,
            "history_samples": len(self._metrics_history),
            "current_needs": self._current_needs,
        }

    def __repr__(self) -> str:
        status = "RUNNING" if self._running else "STOPPED"
        needs_str = repr(self._current_needs) if self._current_needs else "None"
        return (
            f"InternalStateMonitor({self.monitor_id}, status={status}, "
            f"collections={self.total_collections}, needs={needs_str})"
        )
