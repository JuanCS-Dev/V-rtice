"""Metrics Collector - Consciousness System Metrics

Collects real-time metrics from consciousness subsystems:
- TIG Fabric (network health, latency, coherence)
- ESGT Coordinator (event frequency, success rate)
- Arousal Controller (arousal level, stress, needs)
- PFC (social signals, actions, approval rate)
- ToM Engine (agents, beliefs, cache hits)

These metrics are used by the DataOrchestrator to determine
salience scores for ESGT ignition triggers.

Architecture:
    MetricsCollector → DataOrchestrator → ESGT

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Sprint: Reactive Fabric Sprint 3
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Aggregated system metrics snapshot."""

    timestamp: float

    # TIG Fabric metrics
    tig_node_count: int = 0
    tig_edge_count: int = 0
    tig_avg_latency_us: float = 0.0
    tig_coherence: float = 0.0

    # ESGT metrics
    esgt_event_count: int = 0
    esgt_success_rate: float = 0.0
    esgt_frequency_hz: float = 0.0
    esgt_avg_coherence: float = 0.0

    # Arousal metrics
    arousal_level: float = 0.5
    arousal_classification: str = "MODERATE"
    arousal_stress: float = 0.0
    arousal_need: float = 0.0

    # PFC metrics (Track 1)
    pfc_signals_processed: int = 0
    pfc_actions_generated: int = 0
    pfc_approval_rate: float = 0.0

    # ToM metrics (Track 1)
    tom_total_agents: int = 0
    tom_total_beliefs: int = 0
    tom_cache_hit_rate: float = 0.0

    # Safety metrics
    safety_violations: int = 0
    kill_switch_active: bool = False

    # Health score (0-1)
    health_score: float = 1.0

    # Metadata
    collection_duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)


class MetricsCollector:
    """
    Collects metrics from consciousness subsystems.

    Usage:
        collector = MetricsCollector(consciousness_system)
        metrics = await collector.collect()

        # Access specific metrics
        print(f"Arousal: {metrics.arousal_level}")
        print(f"ESGT Success: {metrics.esgt_success_rate}")
    """

    def __init__(self, consciousness_system: Any):
        """Initialize metrics collector.

        Args:
            consciousness_system: ConsciousnessSystem instance
        """
        self.system = consciousness_system
        self.collection_count = 0
        self.total_collection_time_ms = 0.0

        logger.info("MetricsCollector initialized")

    async def collect(self) -> SystemMetrics:
        """Collect current system metrics.

        Returns:
            SystemMetrics snapshot with all subsystem data
        """
        start_time = time.time()
        self.collection_count += 1

        metrics = SystemMetrics(timestamp=start_time)

        try:
            # Collect TIG metrics
            if self.system.tig_fabric:
                await self._collect_tig_metrics(metrics)

            # Collect ESGT metrics
            if self.system.esgt_coordinator:
                await self._collect_esgt_metrics(metrics)

            # Collect Arousal metrics
            if self.system.arousal_controller:
                await self._collect_arousal_metrics(metrics)

            # Collect PFC metrics (Track 1)
            if self.system.prefrontal_cortex:
                await self._collect_pfc_metrics(metrics)

            # Collect ToM metrics (Track 1)
            if self.system.tom_engine:
                await self._collect_tom_metrics(metrics)

            # Collect Safety metrics
            if self.system.safety_protocol:
                await self._collect_safety_metrics(metrics)

            # Calculate health score
            metrics.health_score = self._calculate_health_score(metrics)

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            metrics.errors.append(str(e))

        # Record collection time
        collection_time = (time.time() - start_time) * 1000
        metrics.collection_duration_ms = collection_time
        self.total_collection_time_ms += collection_time

        logger.debug(
            f"Metrics collected: health={metrics.health_score:.2f}, "
            f"arousal={metrics.arousal_level:.2f}, "
            f"esgt_events={metrics.esgt_event_count}, "
            f"collection_time={collection_time:.1f}ms"
        )

        return metrics

    async def _collect_tig_metrics(self, metrics: SystemMetrics) -> None:
        """Collect TIG Fabric metrics."""
        try:
            tig_metrics = self.system.tig_fabric.get_metrics()

            metrics.tig_node_count = len(self.system.tig_fabric.nodes)
            metrics.tig_edge_count = tig_metrics.edge_count
            metrics.tig_avg_latency_us = tig_metrics.avg_latency_us if hasattr(tig_metrics, 'avg_latency_us') else 0.0

            # Get current coherence if available
            if hasattr(self.system.tig_fabric, 'get_coherence'):
                coherence = self.system.tig_fabric.get_coherence()
                metrics.tig_coherence = coherence if coherence else 0.0

        except Exception as e:
            logger.warning(f"Error collecting TIG metrics: {e}")
            metrics.errors.append(f"TIG: {str(e)}")

    async def _collect_esgt_metrics(self, metrics: SystemMetrics) -> None:
        """Collect ESGT Coordinator metrics."""
        try:
            coordinator = self.system.esgt_coordinator

            metrics.esgt_event_count = coordinator.total_events
            metrics.esgt_success_rate = coordinator.get_success_rate()
            metrics.esgt_avg_coherence = coordinator.get_recent_coherence(window=10)

            # Calculate frequency (events per second in last minute)
            if hasattr(coordinator, 'ignition_timestamps') and coordinator.ignition_timestamps:
                now = time.time()
                recent = [t for t in coordinator.ignition_timestamps if now - t < 60.0]
                metrics.esgt_frequency_hz = len(recent) / 60.0

        except Exception as e:
            logger.warning(f"Error collecting ESGT metrics: {e}")
            metrics.errors.append(f"ESGT: {str(e)}")

    async def _collect_arousal_metrics(self, metrics: SystemMetrics) -> None:
        """Collect Arousal Controller metrics."""
        try:
            arousal_state = self.system.arousal_controller.get_current_arousal()

            if arousal_state:
                metrics.arousal_level = arousal_state.arousal
                metrics.arousal_classification = arousal_state.level.value if hasattr(arousal_state.level, 'value') else str(arousal_state.level)
                metrics.arousal_stress = arousal_state.temporal_contribution
                metrics.arousal_need = arousal_state.need_contribution

        except Exception as e:
            logger.warning(f"Error collecting Arousal metrics: {e}")
            metrics.errors.append(f"Arousal: {str(e)}")

    async def _collect_pfc_metrics(self, metrics: SystemMetrics) -> None:
        """Collect PrefrontalCortex metrics (Track 1)."""
        try:
            pfc_status = await self.system.prefrontal_cortex.get_status()

            metrics.pfc_signals_processed = pfc_status.get("total_signals_processed", 0)
            metrics.pfc_actions_generated = pfc_status.get("total_actions_generated", 0)
            metrics.pfc_approval_rate = pfc_status.get("approval_rate", 0.0)

        except Exception as e:
            logger.warning(f"Error collecting PFC metrics: {e}")
            metrics.errors.append(f"PFC: {str(e)}")

    async def _collect_tom_metrics(self, metrics: SystemMetrics) -> None:
        """Collect ToM Engine metrics (Track 1)."""
        try:
            tom_stats = await self.system.tom_engine.get_stats()

            metrics.tom_total_agents = tom_stats.get("total_agents", 0)
            metrics.tom_total_beliefs = tom_stats.get("memory", {}).get("total_beliefs", 0)

            # Redis cache stats
            redis_cache = tom_stats.get("redis_cache", {})
            if redis_cache.get("enabled"):
                metrics.tom_cache_hit_rate = redis_cache.get("hit_rate", 0.0)

        except Exception as e:
            logger.warning(f"Error collecting ToM metrics: {e}")
            metrics.errors.append(f"ToM: {str(e)}")

    async def _collect_safety_metrics(self, metrics: SystemMetrics) -> None:
        """Collect Safety Protocol metrics."""
        try:
            safety_status = self.system.get_safety_status()

            if safety_status:
                metrics.safety_violations = safety_status.get("active_violations", 0)
                metrics.kill_switch_active = safety_status.get("kill_switch_triggered", False)

        except Exception as e:
            logger.warning(f"Error collecting Safety metrics: {e}")
            metrics.errors.append(f"Safety: {str(e)}")

    def _calculate_health_score(self, metrics: SystemMetrics) -> float:
        """Calculate overall system health score (0-1).

        Factors:
        - TIG latency (low is good)
        - ESGT success rate (high is good)
        - Arousal level (moderate is good)
        - Safety violations (none is good)
        - Kill switch (inactive is good)

        Returns:
            Health score between 0 (unhealthy) and 1 (healthy)
        """
        score = 1.0

        # Penalize high TIG latency (>10ms is concerning)
        if metrics.tig_avg_latency_us > 10000:
            score -= 0.2

        # Penalize low ESGT success rate
        if metrics.esgt_success_rate < 0.7:
            score -= 0.2

        # Penalize extreme arousal (too low or too high)
        if metrics.arousal_level < 0.2 or metrics.arousal_level > 0.9:
            score -= 0.1

        # Penalize safety violations
        if metrics.safety_violations > 0:
            score -= 0.3

        # Critical: Kill switch active
        if metrics.kill_switch_active:
            score = 0.0

        # Penalize collection errors
        if metrics.errors:
            score -= 0.1 * len(metrics.errors)

        return max(0.0, min(1.0, score))

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collector statistics.

        Returns:
            Dict with collection count and average time
        """
        avg_time = (
            self.total_collection_time_ms / self.collection_count
            if self.collection_count > 0
            else 0.0
        )

        return {
            "total_collections": self.collection_count,
            "total_time_ms": self.total_collection_time_ms,
            "avg_collection_time_ms": avg_time,
        }

    def __repr__(self) -> str:
        return (
            f"MetricsCollector("
            f"collections={self.collection_count}, "
            f"avg_time={self.total_collection_time_ms / max(1, self.collection_count):.1f}ms)"
        )
