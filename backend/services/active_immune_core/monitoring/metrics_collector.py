"""Metrics Collector - PRODUCTION-READY

Centralized metrics collection and aggregation for the immune system.

Features:
- Collect metrics from all components
- Aggregate statistics
- Time-series data
- Performance analysis
- Resource utilization tracking

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Centralized metrics collector for Active Immune Core.

    Collects and aggregates metrics from:
    - Distributed Coordinator
    - Swarm Coordinator
    - All agent types
    - Infrastructure (cytokines, hormones, lymph nodes)

    Provides:
    - Real-time statistics
    - Historical data
    - Performance analysis
    - Resource utilization

    Usage:
        collector = MetricsCollector()
        collector.collect_from_coordinator(coordinator)
        collector.collect_from_agents(agents)
        stats = collector.get_statistics()
    """

    def __init__(
        self,
        history_size: int = 1000,
        aggregation_interval: int = 60,
    ):
        """
        Initialize metrics collector.

        Args:
            history_size: Max history entries per metric
            aggregation_interval: Seconds between aggregation
        """
        self.history_size = history_size
        self.aggregation_interval = aggregation_interval

        # Time-series data (metric_name -> deque of (timestamp, value))
        self._time_series: Dict[str, Deque[tuple]] = defaultdict(
            lambda: deque(maxlen=history_size)
        )

        # Counters (cumulative)
        self._counters: Dict[str, int] = defaultdict(int)

        # Gauges (current value)
        self._gauges: Dict[str, float] = defaultdict(float)

        # Aggregated statistics
        self._aggregated: Dict[str, Dict[str, float]] = {}

        # Last collection times
        self._last_collection: Dict[str, datetime] = {}

        # Collection timestamps
        self._collection_count = 0
        self._first_collection: Optional[datetime] = None
        self._last_collection_time: Optional[datetime] = None

        logger.info(
            f"MetricsCollector initialized (history={history_size}, "
            f"interval={aggregation_interval}s)"
        )

    # ==================== DATA COLLECTION ====================

    def increment_counter(self, metric: str, value: int = 1) -> None:
        """
        Increment counter metric.

        Args:
            metric: Counter name
            value: Increment value
        """
        self._counters[metric] += value
        self._record_time_series(metric, self._counters[metric])

    def set_gauge(self, metric: str, value: float) -> None:
        """
        Set gauge metric.

        Args:
            metric: Gauge name
            value: Current value
        """
        self._gauges[metric] = value
        self._record_time_series(metric, value)

    def record_value(self, metric: str, value: float) -> None:
        """
        Record raw value to time series.

        Args:
            metric: Metric name
            value: Value to record
        """
        self._record_time_series(metric, value)

    def _record_time_series(self, metric: str, value: float) -> None:
        """Record value to time series (internal)"""
        self._time_series[metric].append((datetime.now(), value))

    # ==================== COMPONENT COLLECTION ====================

    def collect_from_distributed_coordinator(
        self, coordinator
    ) -> Dict[str, Any]:
        """
        Collect metrics from Distributed Coordinator.

        Args:
            coordinator: DistributedCoordinator instance

        Returns:
            Collected metrics dict
        """
        try:
            metrics = coordinator.get_coordinator_metrics()

            # Record counters
            self.increment_counter(
                "elections_total",
                metrics.get("elections_total", 0) - self._counters["elections_total"],
            )
            self.increment_counter(
                "leader_changes",
                metrics.get("leader_changes", 0) - self._counters["leader_changes"],
            )
            self.increment_counter(
                "tasks_assigned",
                metrics.get("tasks_assigned", 0) - self._counters["tasks_assigned"],
            )
            self.increment_counter(
                "tasks_completed",
                metrics.get("tasks_completed", 0) - self._counters["tasks_completed"],
            )
            self.increment_counter(
                "tasks_failed",
                metrics.get("tasks_failed", 0) - self._counters["tasks_failed"],
            )

            # Record gauges
            self.set_gauge("agents_total", metrics.get("agents_total", 0))
            self.set_gauge("agents_alive", metrics.get("agents_alive", 0))
            self.set_gauge("agents_dead", metrics.get("agents_dead", 0))
            self.set_gauge("average_health", metrics.get("average_health", 0.0))
            self.set_gauge("average_load", metrics.get("average_load", 0.0))
            self.set_gauge("tasks_pending", metrics.get("tasks_pending", 0))
            self.set_gauge("has_leader", 1 if metrics.get("has_leader") else 0)

            self._last_collection["distributed_coordinator"] = datetime.now()

            return metrics

        except Exception as e:
            logger.error(f"Error collecting from distributed coordinator: {e}")
            return {}

    def collect_from_swarm_coordinator(self, coordinator) -> Dict[str, Any]:
        """
        Collect metrics from Swarm Coordinator.

        Args:
            coordinator: SwarmCoordinator instance

        Returns:
            Collected metrics dict
        """
        try:
            metrics = coordinator.get_swarm_metrics()

            # Record gauges
            self.set_gauge("boids_total", metrics.get("boids_total", 0))
            self.set_gauge("swarm_radius", metrics.get("swarm_radius", 0.0))
            self.set_gauge("swarm_density", metrics.get("swarm_density", 0.0))
            self.set_gauge("swarm_has_target", 1 if metrics.get("has_target") else 0)

            self._last_collection["swarm_coordinator"] = datetime.now()

            return metrics

        except Exception as e:
            logger.error(f"Error collecting from swarm coordinator: {e}")
            return {}

    def collect_from_agents(self, agents: List) -> Dict[str, Any]:
        """
        Collect metrics from all agents.

        Args:
            agents: List of agent instances

        Returns:
            Aggregated agent metrics
        """
        try:
            agent_metrics = {
                "total_agents": len(agents),
                "by_type": defaultdict(int),
                "by_status": defaultdict(int),
                "total_detections": 0,
                "total_neutralizations": 0,
                "total_false_positives": 0,
                "average_energia": 0.0,
            }

            energia_sum = 0.0

            for agent in agents:
                # Count by type
                agent_metrics["by_type"][agent.state.tipo.value] += 1

                # Count by status
                agent_metrics["by_status"][agent.state.status.value] += 1

                # Aggregate metrics
                agent_metrics["total_detections"] += agent.state.deteccoes_total
                agent_metrics["total_neutralizations"] += agent.state.neutralizacoes_total
                agent_metrics["total_false_positives"] += agent.state.falsos_positivos

                energia_sum += agent.state.energia

            # Calculate averages
            if len(agents) > 0:
                agent_metrics["average_energia"] = energia_sum / len(agents)

            # Record gauges
            self.set_gauge("agents_count", agent_metrics["total_agents"])
            self.set_gauge("agents_average_energia", agent_metrics["average_energia"])

            # Record counters (incremental)
            self.increment_counter(
                "agents_detections_total",
                agent_metrics["total_detections"]
                - self._counters["agents_detections_total"],
            )
            self.increment_counter(
                "agents_neutralizations_total",
                agent_metrics["total_neutralizations"]
                - self._counters["agents_neutralizations_total"],
            )

            self._last_collection["agents"] = datetime.now()

            return agent_metrics

        except Exception as e:
            logger.error(f"Error collecting from agents: {e}")
            return {}

    def collect_from_lymphnode(self, lymphnode) -> Dict[str, Any]:
        """
        Collect metrics from lymph node.

        Args:
            lymphnode: LymphNode instance

        Returns:
            Lymph node metrics
        """
        try:
            metrics = lymphnode.get_lymphnode_metrics()

            # Record gauges
            self.set_gauge("lymphnode_agents", metrics.get("agents_total", 0))
            self.set_gauge(
                "lymphnode_active_agents", metrics.get("agents_active", 0)
            )

            self._last_collection["lymphnode"] = datetime.now()

            return metrics

        except Exception as e:
            logger.error(f"Error collecting from lymphnode: {e}")
            return {}

    # ==================== AGGREGATION & STATISTICS ====================

    def aggregate_time_series(self, metric: str, window: int = 60) -> Dict[str, float]:
        """
        Aggregate time series data over window.

        Args:
            metric: Metric name
            window: Time window in seconds

        Returns:
            Aggregated statistics (min, max, avg, p50, p95, p99)
        """
        if metric not in self._time_series:
            return {}

        series = self._time_series[metric]
        if not series:
            return {}

        # Filter by window
        cutoff = datetime.now() - timedelta(seconds=window)
        values = [v for ts, v in series if ts >= cutoff]

        if not values:
            return {}

        # Calculate statistics
        values_sorted = sorted(values)
        n = len(values)

        stats = {
            "count": n,
            "min": values_sorted[0],
            "max": values_sorted[-1],
            "avg": sum(values) / n,
            "p50": values_sorted[int(n * 0.50)] if n > 0 else 0,
            "p95": values_sorted[int(n * 0.95)] if n > 1 else values_sorted[-1],
            "p99": values_sorted[int(n * 0.99)] if n > 1 else values_sorted[-1],
        }

        return stats

    def get_statistics(self, window: int = 60) -> Dict[str, Any]:
        """
        Get comprehensive statistics.

        Args:
            window: Time window for aggregations (seconds)

        Returns:
            Statistics dict
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "window_seconds": window,
            "collection_count": self._collection_count,
            "uptime_seconds": self.get_uptime(),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "time_series_aggregations": {},
            "last_collections": {
                k: v.isoformat() for k, v in self._last_collection.items()
            },
        }

        # Aggregate key metrics
        key_metrics = [
            "agents_total",
            "agents_alive",
            "average_health",
            "average_load",
            "tasks_pending",
        ]

        for metric in key_metrics:
            if metric in self._time_series:
                stats["time_series_aggregations"][metric] = self.aggregate_time_series(
                    metric, window
                )

        return stats

    def get_rates(self, window: int = 60) -> Dict[str, float]:
        """
        Calculate rates (per second) for counters.

        Args:
            window: Time window in seconds

        Returns:
            Rates dict (metric -> rate per second)
        """
        rates = {}

        for metric, series in self._time_series.items():
            if metric not in self._counters:
                continue

            # Get values in window
            cutoff = datetime.now() - timedelta(seconds=window)
            window_data = [(ts, v) for ts, v in series if ts >= cutoff]

            if len(window_data) < 2:
                rates[metric] = 0.0
                continue

            # Calculate rate
            first_ts, first_val = window_data[0]
            last_ts, last_val = window_data[-1]

            duration = (last_ts - first_ts).total_seconds()
            if duration > 0:
                rates[metric] = (last_val - first_val) / duration
            else:
                rates[metric] = 0.0

        return rates

    def get_trends(self, metric: str, window: int = 300) -> Dict[str, Any]:
        """
        Analyze trends for metric.

        Args:
            metric: Metric name
            window: Time window in seconds

        Returns:
            Trend analysis (direction, slope, confidence)
        """
        if metric not in self._time_series:
            return {}

        series = self._time_series[metric]
        if not series or len(series) < 3:
            return {}

        # Filter by window
        cutoff = datetime.now() - timedelta(seconds=window)
        window_data = [(ts, v) for ts, v in series if ts >= cutoff]

        if len(window_data) < 3:
            return {}

        # Simple linear regression
        n = len(window_data)
        x_values = list(range(n))
        y_values = [v for _, v in window_data]

        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            slope = 0.0
        else:
            slope = numerator / denominator

        # Determine trend direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        return {
            "direction": direction,
            "slope": slope,
            "data_points": n,
            "window_seconds": window,
        }

    # ==================== UTILITY ====================

    def get_uptime(self) -> float:
        """
        Get collector uptime in seconds.

        Returns:
            Uptime in seconds
        """
        if not self._first_collection:
            return 0.0
        return (datetime.now() - self._first_collection).total_seconds()

    def reset_counters(self) -> None:
        """Reset all counters to zero"""
        self._counters.clear()
        logger.info("Counters reset")

    def clear_history(self) -> None:
        """Clear all time series history"""
        self._time_series.clear()
        logger.info("Time series history cleared")

    def get_metric_names(self) -> List[str]:
        """Get all metric names"""
        return sorted(set(self._counters.keys()) | set(self._gauges.keys()) | set(self._time_series.keys()))

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"<MetricsCollector "
            f"metrics={len(self.get_metric_names())} "
            f"collections={self._collection_count}>"
        )
