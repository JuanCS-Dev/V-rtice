"""Prometheus Metrics Exporter - PRODUCTION-READY

Exports comprehensive metrics in Prometheus format for monitoring and alerting.

Features:
- Agent metrics (health, load, tasks, performance)
- Coordination metrics (elections, consensus, tasks)
- Infrastructure metrics (cytokines, hormones, lymph nodes)
- Latency histograms
- Resource gauges
- Counter increments

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
import time

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """
    Prometheus metrics exporter for Active Immune Core.

    Exposes comprehensive metrics for monitoring:
    - Agent health and performance
    - Task execution and latency
    - Leader elections and consensus
    - Infrastructure status
    - System-wide statistics

    Usage:
        exporter = PrometheusExporter()
        exporter.record_agent_registered("agent_1", "macrophage")
        exporter.record_task_completed("task_123", duration=2.5)
        metrics = exporter.export_metrics()
    """

    def __init__(self, namespace: str = "immune_core"):
        """
        Initialize Prometheus exporter.

        Args:
            namespace: Metric namespace prefix
        """
        self.namespace = namespace
        self._start_time = time.time()

        # System info
        self.system_info = Info(
            f"{namespace}_system",
            "System information",
            registry=REGISTRY,
        )
        self.system_info.info(
            {
                "version": "1.0.0",
                "component": "active_immune_core",
            }
        )

        # Agent metrics
        self.agents_total = Gauge(
            f"{namespace}_agents_total",
            "Total number of registered agents",
            ["type"],
            registry=REGISTRY,
        )

        self.agents_alive = Gauge(
            f"{namespace}_agents_alive",
            "Number of alive agents",
            ["type"],
            registry=REGISTRY,
        )

        self.agent_health_score = Gauge(
            f"{namespace}_agent_health_score",
            "Agent health score (0.0-1.0)",
            ["agent_id", "type"],
            registry=REGISTRY,
        )

        self.agent_load = Gauge(
            f"{namespace}_agent_load",
            "Agent current load (0.0-1.0)",
            ["agent_id", "type"],
            registry=REGISTRY,
        )

        self.agent_tasks_completed = Counter(
            f"{namespace}_agent_tasks_completed_total",
            "Total tasks completed by agent",
            ["agent_id", "type"],
            registry=REGISTRY,
        )

        self.agent_tasks_failed = Counter(
            f"{namespace}_agent_tasks_failed_total",
            "Total tasks failed by agent",
            ["agent_id", "type"],
            registry=REGISTRY,
        )

        # Task metrics
        self.tasks_submitted = Counter(
            f"{namespace}_tasks_submitted_total",
            "Total tasks submitted",
            ["task_type"],
            registry=REGISTRY,
        )

        self.tasks_assigned = Counter(
            f"{namespace}_tasks_assigned_total",
            "Total tasks assigned",
            ["task_type"],
            registry=REGISTRY,
        )

        self.tasks_completed = Counter(
            f"{namespace}_tasks_completed_total",
            "Total tasks completed",
            ["task_type"],
            registry=REGISTRY,
        )

        self.tasks_failed = Counter(
            f"{namespace}_tasks_failed_total",
            "Total tasks failed",
            ["task_type"],
            registry=REGISTRY,
        )

        self.tasks_pending = Gauge(
            f"{namespace}_tasks_pending",
            "Number of pending tasks",
            registry=REGISTRY,
        )

        self.task_duration = Histogram(
            f"{namespace}_task_duration_seconds",
            "Task execution duration",
            ["task_type"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=REGISTRY,
        )

        self.task_retries = Histogram(
            f"{namespace}_task_retries",
            "Number of task retries before completion",
            ["task_type"],
            buckets=[0, 1, 2, 3, 5, 10],
            registry=REGISTRY,
        )

        # Coordination metrics
        self.elections_total = Counter(
            f"{namespace}_elections_total",
            "Total leader elections",
            registry=REGISTRY,
        )

        self.leader_changes = Counter(
            f"{namespace}_leader_changes_total",
            "Total leader changes",
            registry=REGISTRY,
        )

        self.has_leader = Gauge(
            f"{namespace}_has_leader",
            "Whether system has a leader (1=yes, 0=no)",
            registry=REGISTRY,
        )

        self.proposals_total = Counter(
            f"{namespace}_proposals_total",
            "Total consensus proposals",
            ["proposal_type"],
            registry=REGISTRY,
        )

        self.proposals_approved = Counter(
            f"{namespace}_proposals_approved_total",
            "Total approved proposals",
            ["proposal_type"],
            registry=REGISTRY,
        )

        self.proposals_rejected = Counter(
            f"{namespace}_proposals_rejected_total",
            "Total rejected proposals",
            ["proposal_type"],
            registry=REGISTRY,
        )

        self.votes_cast = Counter(
            f"{namespace}_votes_cast_total",
            "Total votes cast",
            ["decision"],
            registry=REGISTRY,
        )

        # Fault tolerance metrics
        self.failures_detected = Counter(
            f"{namespace}_failures_detected_total",
            "Total agent failures detected",
            registry=REGISTRY,
        )

        self.recoveries_performed = Counter(
            f"{namespace}_recoveries_performed_total",
            "Total recovery actions performed",
            registry=REGISTRY,
        )

        self.heartbeat_timeouts = Counter(
            f"{namespace}_heartbeat_timeouts_total",
            "Total heartbeat timeouts",
            ["agent_id"],
            registry=REGISTRY,
        )

        # Infrastructure metrics
        self.cytokines_sent = Counter(
            f"{namespace}_cytokines_sent_total",
            "Total cytokines sent",
            ["type"],
            registry=REGISTRY,
        )

        self.cytokines_received = Counter(
            f"{namespace}_cytokines_received_total",
            "Total cytokines received",
            ["type"],
            registry=REGISTRY,
        )

        self.hormones_published = Counter(
            f"{namespace}_hormones_published_total",
            "Total hormones published",
            ["type"],
            registry=REGISTRY,
        )

        self.lymphnode_registrations = Counter(
            f"{namespace}_lymphnode_registrations_total",
            "Total lymph node registrations",
            registry=REGISTRY,
        )

        # Performance metrics
        self.operation_duration = Summary(
            f"{namespace}_operation_duration_seconds",
            "Operation duration summary",
            ["operation"],
            registry=REGISTRY,
        )

        self.api_requests = Counter(
            f"{namespace}_api_requests_total",
            "Total API requests",
            ["endpoint", "method", "status"],
            registry=REGISTRY,
        )

        self.api_latency = Histogram(
            f"{namespace}_api_latency_seconds",
            "API request latency",
            ["endpoint"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=REGISTRY,
        )

        logger.info(f"PrometheusExporter initialized (namespace={namespace})")

    # ==================== AGENT METRICS ====================

    def record_agent_registered(self, agent_id: str, agent_type: str) -> None:
        """Record agent registration"""
        self.agents_total.labels(type=agent_type).inc()
        self.agents_alive.labels(type=agent_type).inc()
        logger.debug(f"Agent registered: {agent_id} ({agent_type})")

    def record_agent_unregistered(self, agent_id: str, agent_type: str) -> None:
        """Record agent unregistration"""
        self.agents_total.labels(type=agent_type).dec()
        logger.debug(f"Agent unregistered: {agent_id}")

    def update_agent_health(self, agent_id: str, agent_type: str, health_score: float) -> None:
        """Update agent health score"""
        self.agent_health_score.labels(agent_id=agent_id, type=agent_type).set(health_score)

    def update_agent_load(self, agent_id: str, agent_type: str, load: float) -> None:
        """Update agent load"""
        self.agent_load.labels(agent_id=agent_id, type=agent_type).set(load)

    def record_agent_alive(self, agent_id: str, agent_type: str, is_alive: bool) -> None:
        """Update agent alive status"""
        if is_alive:
            self.agents_alive.labels(type=agent_type).inc()
        else:
            self.agents_alive.labels(type=agent_type).dec()

    def record_agent_task_completed(self, agent_id: str, agent_type: str) -> None:
        """Record task completion by agent"""
        self.agent_tasks_completed.labels(agent_id=agent_id, type=agent_type).inc()

    def record_agent_task_failed(self, agent_id: str, agent_type: str) -> None:
        """Record task failure by agent"""
        self.agent_tasks_failed.labels(agent_id=agent_id, type=agent_type).inc()

    # ==================== TASK METRICS ====================

    def record_task_submitted(self, task_type: str) -> None:
        """Record task submission"""
        self.tasks_submitted.labels(task_type=task_type).inc()

    def record_task_assigned(self, task_type: str) -> None:
        """Record task assignment"""
        self.tasks_assigned.labels(task_type=task_type).inc()

    def record_task_completed(self, task_type: str, duration: float, retries: int = 0) -> None:
        """Record task completion with duration and retries"""
        self.tasks_completed.labels(task_type=task_type).inc()
        self.task_duration.labels(task_type=task_type).observe(duration)
        self.task_retries.labels(task_type=task_type).observe(retries)

    def record_task_failed(self, task_type: str) -> None:
        """Record task failure"""
        self.tasks_failed.labels(task_type=task_type).inc()

    def update_tasks_pending(self, count: int) -> None:
        """Update pending tasks count"""
        self.tasks_pending.set(count)

    # ==================== COORDINATION METRICS ====================

    def record_election(self) -> None:
        """Record leader election"""
        self.elections_total.inc()

    def record_leader_change(self, has_leader: bool) -> None:
        """Record leader change"""
        self.leader_changes.inc()
        self.has_leader.set(1 if has_leader else 0)

    def record_proposal(self, proposal_type: str) -> None:
        """Record consensus proposal"""
        self.proposals_total.labels(proposal_type=proposal_type).inc()

    def record_proposal_result(self, proposal_type: str, approved: bool) -> None:
        """Record proposal result"""
        if approved:
            self.proposals_approved.labels(proposal_type=proposal_type).inc()
        else:
            self.proposals_rejected.labels(proposal_type=proposal_type).inc()

    def record_vote(self, decision: str) -> None:
        """Record vote cast"""
        self.votes_cast.labels(decision=decision).inc()

    # ==================== FAULT TOLERANCE METRICS ====================

    def record_failure_detected(self, agent_id: str) -> None:
        """Record agent failure detection"""
        self.failures_detected.inc()
        self.heartbeat_timeouts.labels(agent_id=agent_id).inc()

    def record_recovery_performed(self) -> None:
        """Record recovery action"""
        self.recoveries_performed.inc()

    # ==================== INFRASTRUCTURE METRICS ====================

    def record_cytokine_sent(self, cytokine_type: str) -> None:
        """Record cytokine sent"""
        self.cytokines_sent.labels(type=cytokine_type).inc()

    def record_cytokine_received(self, cytokine_type: str) -> None:
        """Record cytokine received"""
        self.cytokines_received.labels(type=cytokine_type).inc()

    def record_hormone_published(self, hormone_type: str) -> None:
        """Record hormone published"""
        self.hormones_published.labels(type=hormone_type).inc()

    def record_lymphnode_registration(self) -> None:
        """Record lymph node registration"""
        self.lymphnode_registrations.inc()

    # ==================== PERFORMANCE METRICS ====================

    def record_operation_duration(self, operation: str, duration: float) -> None:
        """Record operation duration"""
        self.operation_duration.labels(operation=operation).observe(duration)

    def record_api_request(self, endpoint: str, method: str, status: int, latency: float) -> None:
        """Record API request"""
        self.api_requests.labels(endpoint=endpoint, method=method, status=str(status)).inc()
        self.api_latency.labels(endpoint=endpoint).observe(latency)

    # ==================== EXPORT ====================

    def export_metrics(self) -> bytes:
        """
        Export metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(REGISTRY)

    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self._start_time

    def __repr__(self) -> str:
        """String representation"""
        return f"<PrometheusExporter namespace={self.namespace} uptime={self.get_uptime():.1f}s>"
