"""
Canary Deployment System for PENELOPE

Biblical Foundation:
- Proverbs 21:5: "The plans of the diligent lead surely to abundance"
- Proverbs 14:8: "The wisdom of the prudent is to discern his way"

Implements A/B testing framework for gradual patch rollout:
1. Deploy patch to small percentage of traffic (canary)
2. Monitor metrics and compare to control group
3. Automatically promote or rollback based on metrics
4. Gradual rollout with safety gates

Author: PENELOPE Team
Created: 2025-11-01
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any
from uuid import uuid4

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class CanaryStatus(str, Enum):
    """Canary deployment status."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    PROMOTING = "promoting"
    ROLLING_BACK = "rolling_back"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CanaryDecision(str, Enum):
    """Canary analysis decision."""

    PROMOTE = "promote"  # Metrics good, increase traffic
    HOLD = "hold"  # Metrics unclear, keep current percentage
    ROLLBACK = "rollback"  # Metrics bad, revert patch


@dataclass
class MetricComparison:
    """Comparison between canary and control metrics."""

    metric_name: str
    canary_value: float
    control_value: float
    delta_percentage: float
    threshold_breached: bool
    severity: str  # "critical", "warning", "ok"


@dataclass
class CanaryConfig:
    """Configuration for canary deployment."""

    initial_percentage: int = 10  # Start with 10% traffic
    promotion_steps: list[int] = None  # [10, 25, 50, 100]
    analysis_duration_minutes: int = 15  # Analyze for 15 min per step
    success_threshold: float = 0.95  # 95% success rate required
    latency_threshold_ms: int = 500  # Max p99 latency increase
    error_rate_threshold: float = 0.02  # Max 2% error rate
    auto_promote: bool = True  # Automatically promote if metrics good
    auto_rollback: bool = True  # Automatically rollback if metrics bad

    def __post_init__(self):
        if self.promotion_steps is None:
            self.promotion_steps = [10, 25, 50, 100]


class CanaryDeployment:
    """
    Manages a single canary deployment.

    Tracks deployment state, metrics comparison, and rollout progress.
    """

    def __init__(
        self,
        deployment_id: str,
        patch_id: str,
        service_name: str,
        config: CanaryConfig,
    ):
        self.deployment_id = deployment_id
        self.patch_id = patch_id
        self.service_name = service_name
        self.config = config
        self.status = CanaryStatus.INITIALIZING
        self.current_percentage = 0
        self.current_step_index = 0
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.last_analysis_at: datetime | None = None
        self.metric_comparisons: list[MetricComparison] = []
        self.decisions: list[tuple[datetime, CanaryDecision, str]] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "deployment_id": self.deployment_id,
            "patch_id": self.patch_id,
            "service_name": self.service_name,
            "status": self.status.value,
            "current_percentage": self.current_percentage,
            "current_step_index": self.current_step_index,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "last_analysis_at": (
                self.last_analysis_at.isoformat() if self.last_analysis_at else None
            ),
            "metric_comparisons": [
                {
                    "metric_name": mc.metric_name,
                    "canary_value": mc.canary_value,
                    "control_value": mc.control_value,
                    "delta_percentage": mc.delta_percentage,
                    "threshold_breached": mc.threshold_breached,
                    "severity": mc.severity,
                }
                for mc in self.metric_comparisons
            ],
            "decisions": [
                {
                    "timestamp": ts.isoformat(),
                    "decision": decision.value,
                    "reason": reason,
                }
                for ts, decision, reason in self.decisions
            ],
        }


# Prometheus Metrics
canary_deployments_total = Counter(
    "penelope_canary_deployments_total",
    "Total canary deployments initiated",
    ["service", "status"],
)

canary_active_deployments = Gauge(
    "penelope_canary_active_deployments",
    "Number of active canary deployments",
    ["service"],
)

canary_traffic_percentage = Gauge(
    "penelope_canary_traffic_percentage",
    "Current canary traffic percentage",
    ["service", "deployment_id"],
)

canary_promotion_duration_seconds = Histogram(
    "penelope_canary_promotion_duration_seconds",
    "Time to complete canary promotion",
    ["service", "outcome"],
    buckets=[300, 900, 1800, 3600, 7200],  # 5m, 15m, 30m, 1h, 2h
)

canary_rollback_total = Counter(
    "penelope_canary_rollback_total",
    "Total canary rollbacks",
    ["service", "reason"],
)


class CanaryManager:
    """
    Manages canary deployments for PENELOPE patches.

    Implements A/B testing with gradual rollout:
    1. Deploy to 10% traffic (canary group)
    2. Compare metrics: success rate, latency, error rate
    3. If metrics good: promote to 25%, 50%, 100%
    4. If metrics bad: automatic rollback
    5. If metrics unclear: hold and wait

    Biblical Principle: Proverbs 14:8 - "The wisdom of the prudent is to discern his way"
    """

    def __init__(
        self,
        observability_client: Any | None = None,
        patch_history: Any | None = None,
        audit_logger: Any | None = None,
    ):
        """
        Initialize CanaryManager.

        Args:
            observability_client: Client for fetching metrics
            patch_history: For rollback capability
            audit_logger: For logging decisions
        """
        self.observability_client = observability_client
        self.patch_history = patch_history
        self.audit_logger = audit_logger
        self.active_deployments: dict[str, CanaryDeployment] = {}
        self._lock = asyncio.Lock()

    async def start_canary(
        self,
        patch_id: str,
        service_name: str,
        config: CanaryConfig | None = None,
    ) -> str:
        """
        Start canary deployment for patch.

        Args:
            patch_id: Patch to deploy
            service_name: Target service
            config: Canary configuration (uses defaults if None)

        Returns:
            deployment_id: Unique deployment identifier
        """
        deployment_id = str(uuid4())
        config = config or CanaryConfig()

        deployment = CanaryDeployment(
            deployment_id=deployment_id,
            patch_id=patch_id,
            service_name=service_name,
            config=config,
        )

        async with self._lock:
            self.active_deployments[deployment_id] = deployment

        deployment.status = CanaryStatus.INITIALIZING
        deployment.started_at = datetime.utcnow()

        logger.info(
            "CANARY_STARTED",
            extra={
                "labels": {
                    "component": "canary_manager",
                    "deployment_id": deployment_id,
                    "patch_id": patch_id,
                    "service": service_name,
                },
                "deployment": deployment.to_dict(),
            },
        )

        canary_deployments_total.labels(service=service_name, status="started").inc()
        canary_active_deployments.labels(service=service_name).inc()

        # Start with first percentage
        await self._apply_traffic_percentage(deployment, config.promotion_steps[0])

        deployment.status = CanaryStatus.RUNNING
        deployment.current_step_index = 0

        # Start background analysis loop
        asyncio.create_task(self._run_canary_analysis(deployment_id))

        return deployment_id

    async def _apply_traffic_percentage(
        self, deployment: CanaryDeployment, percentage: int
    ) -> None:
        """
        Apply patch to specified percentage of traffic.

        This would integrate with service mesh (Istio, Linkerd) or
        load balancer to route traffic to canary instances.
        """
        deployment.current_percentage = percentage

        logger.info(
            "CANARY_TRAFFIC_UPDATE",
            extra={
                "labels": {
                    "component": "canary_manager",
                    "deployment_id": deployment.deployment_id,
                    "service": deployment.service_name,
                },
                "percentage": percentage,
            },
        )

        canary_traffic_percentage.labels(
            service=deployment.service_name,
            deployment_id=deployment.deployment_id,
        ).set(percentage)

        # Integration point: Update service mesh routing rules
        # Example with Istio VirtualService:
        # await self._update_istio_virtual_service(
        #     deployment.service_name,
        #     canary_percentage=percentage
        # )

    async def _run_canary_analysis(self, deployment_id: str) -> None:
        """
        Background loop for canary analysis.

        Runs continuously during deployment, analyzing metrics and
        making promote/hold/rollback decisions.
        """
        try:
            while True:
                async with self._lock:
                    deployment = self.active_deployments.get(deployment_id)

                if not deployment or deployment.status not in (
                    CanaryStatus.RUNNING,
                    CanaryStatus.PROMOTING,
                ):
                    break

                # Wait for analysis duration
                await asyncio.sleep(deployment.config.analysis_duration_minutes * 60)

                # Analyze metrics
                decision = await self._analyze_canary_metrics(deployment)

                # Act on decision
                if decision == CanaryDecision.PROMOTE:
                    await self._promote_canary(deployment)
                elif decision == CanaryDecision.ROLLBACK:
                    await self._rollback_canary(deployment)
                # HOLD: do nothing, wait for next analysis

        except Exception as e:
            logger.error(
                "CANARY_ANALYSIS_ERROR",
                extra={
                    "labels": {
                        "component": "canary_manager",
                        "deployment_id": deployment_id,
                    },
                    "error": str(e),
                },
            )
            if deployment:
                await self._rollback_canary(deployment, reason=f"Analysis error: {e}")

    async def _analyze_canary_metrics(
        self, deployment: CanaryDeployment
    ) -> CanaryDecision:
        """
        Analyze canary metrics vs control group.

        Compares:
        - Success rate (should be ≥ threshold)
        - p99 latency (should not increase significantly)
        - Error rate (should be ≤ threshold)

        Returns:
            Decision to promote, hold, or rollback
        """
        deployment.last_analysis_at = datetime.utcnow()
        deployment.metric_comparisons = []

        # Fetch metrics for canary and control groups
        canary_metrics = await self._fetch_metrics(
            deployment.service_name, group="canary"
        )
        control_metrics = await self._fetch_metrics(
            deployment.service_name, group="control"
        )

        # Compare success rate
        success_comparison = self._compare_metric(
            "success_rate",
            canary_metrics.get("success_rate", 1.0),
            control_metrics.get("success_rate", 1.0),
            threshold=deployment.config.success_threshold,
            higher_is_better=True,
        )
        deployment.metric_comparisons.append(success_comparison)

        # Compare p99 latency
        latency_comparison = self._compare_metric(
            "p99_latency_ms",
            canary_metrics.get("p99_latency_ms", 0),
            control_metrics.get("p99_latency_ms", 0),
            threshold=deployment.config.latency_threshold_ms,
            higher_is_better=False,
        )
        deployment.metric_comparisons.append(latency_comparison)

        # Compare error rate
        error_comparison = self._compare_metric(
            "error_rate",
            canary_metrics.get("error_rate", 0),
            control_metrics.get("error_rate", 0),
            threshold=deployment.config.error_rate_threshold,
            higher_is_better=False,
        )
        deployment.metric_comparisons.append(error_comparison)

        # Make decision based on comparisons
        critical_issues = [
            mc for mc in deployment.metric_comparisons if mc.severity == "critical"
        ]
        warnings = [
            mc for mc in deployment.metric_comparisons if mc.severity == "warning"
        ]

        if critical_issues:
            decision = CanaryDecision.ROLLBACK
            reason = f"Critical metrics breached: {[mc.metric_name for mc in critical_issues]}"
        elif warnings:
            decision = CanaryDecision.HOLD
            reason = f"Warnings detected: {[mc.metric_name for mc in warnings]}"
        else:
            decision = CanaryDecision.PROMOTE
            reason = "All metrics within acceptable thresholds"

        deployment.decisions.append((datetime.utcnow(), decision, reason))

        logger.info(
            "CANARY_ANALYSIS_DECISION",
            extra={
                "labels": {
                    "component": "canary_manager",
                    "deployment_id": deployment.deployment_id,
                    "service": deployment.service_name,
                },
                "decision": decision.value,
                "reason": reason,
                "comparisons": [
                    {
                        "metric": mc.metric_name,
                        "canary": mc.canary_value,
                        "control": mc.control_value,
                        "delta": mc.delta_percentage,
                        "severity": mc.severity,
                    }
                    for mc in deployment.metric_comparisons
                ],
            },
        )

        if self.audit_logger:
            await self.audit_logger.log_canary_decision(
                deployment_id=deployment.deployment_id,
                decision=decision,
                reason=reason,
                metrics=deployment.metric_comparisons,
            )

        return decision

    def _compare_metric(
        self,
        metric_name: str,
        canary_value: float,
        control_value: float,
        threshold: float,
        higher_is_better: bool,
    ) -> MetricComparison:
        """
        Compare canary vs control metric.

        Args:
            metric_name: Name of metric
            canary_value: Value in canary group
            control_value: Value in control group
            threshold: Absolute threshold for acceptable values
            higher_is_better: Whether higher values are better

        Returns:
            MetricComparison with analysis
        """
        # Calculate percentage delta
        if control_value != 0:
            delta_percentage = ((canary_value - control_value) / control_value) * 100
        else:
            delta_percentage = 0.0

        # Determine if threshold breached
        if higher_is_better:
            threshold_breached = canary_value < threshold
            if threshold_breached:
                severity = "critical" if canary_value < threshold * 0.9 else "warning"
            else:
                severity = "ok"
        else:
            threshold_breached = canary_value > threshold
            if threshold_breached:
                severity = "critical" if canary_value > threshold * 1.2 else "warning"
            else:
                severity = "ok"

        return MetricComparison(
            metric_name=metric_name,
            canary_value=canary_value,
            control_value=control_value,
            delta_percentage=delta_percentage,
            threshold_breached=threshold_breached,
            severity=severity,
        )

    async def _fetch_metrics(self, service_name: str, group: str) -> dict[str, float]:
        """
        Fetch metrics for service group (canary or control).

        This would query Prometheus or other metrics backend.
        """
        if not self.observability_client:
            # Mock metrics for testing
            return {
                "success_rate": 0.98,
                "p99_latency_ms": 150,
                "error_rate": 0.01,
            }

        # Query Prometheus for actual metrics
        # queries = {
        #     "success_rate": f'sum(rate(http_requests_total{{service="{service_name}",group="{group}",status=~"2.."}}[5m])) / sum(rate(http_requests_total{{service="{service_name}",group="{group}"}}[5m]))',
        #     "p99_latency_ms": f'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{{service="{service_name}",group="{group}"}}[5m])) * 1000',
        #     "error_rate": f'sum(rate(http_requests_total{{service="{service_name}",group="{group}",status=~"5.."}}[5m])) / sum(rate(http_requests_total{{service="{service_name}",group="{group}"}}[5m]))',
        # }
        #
        # metrics = {}
        # for name, query in queries.items():
        #     result = await self.observability_client.query(query)
        #     metrics[name] = float(result)
        #
        # return metrics

        return {
            "success_rate": 0.98,
            "p99_latency_ms": 150,
            "error_rate": 0.01,
        }

    async def _promote_canary(self, deployment: CanaryDeployment) -> None:
        """
        Promote canary to next traffic percentage.

        If at 100%, mark deployment as completed.
        """
        if not deployment.config.auto_promote:
            logger.info(
                "CANARY_PROMOTION_SKIPPED",
                extra={
                    "labels": {
                        "component": "canary_manager",
                        "deployment_id": deployment.deployment_id,
                    },
                    "reason": "auto_promote disabled",
                },
            )
            return

        deployment.status = CanaryStatus.PROMOTING

        # Move to next percentage step
        next_step_index = deployment.current_step_index + 1

        if next_step_index >= len(deployment.config.promotion_steps):
            # Reached 100%, deployment complete
            deployment.status = CanaryStatus.COMPLETED
            deployment.completed_at = datetime.utcnow()

            duration_seconds = (
                deployment.completed_at - deployment.started_at
            ).total_seconds()

            logger.info(
                "CANARY_COMPLETED",
                extra={
                    "labels": {
                        "component": "canary_manager",
                        "deployment_id": deployment.deployment_id,
                        "service": deployment.service_name,
                    },
                    "duration_seconds": duration_seconds,
                },
            )

            canary_deployments_total.labels(
                service=deployment.service_name, status="completed"
            ).inc()
            canary_active_deployments.labels(service=deployment.service_name).dec()
            canary_promotion_duration_seconds.labels(
                service=deployment.service_name, outcome="success"
            ).observe(duration_seconds)

            async with self._lock:
                del self.active_deployments[deployment.deployment_id]

        else:
            # Promote to next percentage
            next_percentage = deployment.config.promotion_steps[next_step_index]
            await self._apply_traffic_percentage(deployment, next_percentage)
            deployment.current_step_index = next_step_index
            deployment.status = CanaryStatus.RUNNING

            logger.info(
                "CANARY_PROMOTED",
                extra={
                    "labels": {
                        "component": "canary_manager",
                        "deployment_id": deployment.deployment_id,
                        "service": deployment.service_name,
                    },
                    "from_percentage": deployment.config.promotion_steps[
                        next_step_index - 1
                    ],
                    "to_percentage": next_percentage,
                },
            )

    async def _rollback_canary(
        self, deployment: CanaryDeployment, reason: str | None = None
    ) -> None:
        """
        Rollback canary deployment.

        Reverts to 0% traffic and marks deployment as failed.
        """
        if not deployment.config.auto_rollback and reason is None:
            logger.info(
                "CANARY_ROLLBACK_SKIPPED",
                extra={
                    "labels": {
                        "component": "canary_manager",
                        "deployment_id": deployment.deployment_id,
                    },
                    "reason": "auto_rollback disabled",
                },
            )
            return

        deployment.status = CanaryStatus.ROLLING_BACK

        # Revert to 0% traffic
        await self._apply_traffic_percentage(deployment, 0)

        # Use patch history to rollback if available
        if self.patch_history:
            await self.patch_history.rollback_patch(deployment.patch_id)

        deployment.status = CanaryStatus.FAILED
        deployment.completed_at = datetime.utcnow()

        rollback_reason = reason or "Metrics threshold breached"

        logger.warning(
            "CANARY_ROLLBACK",
            extra={
                "labels": {
                    "component": "canary_manager",
                    "deployment_id": deployment.deployment_id,
                    "service": deployment.service_name,
                },
                "reason": rollback_reason,
            },
        )

        canary_deployments_total.labels(
            service=deployment.service_name, status="failed"
        ).inc()
        canary_active_deployments.labels(service=deployment.service_name).dec()
        canary_rollback_total.labels(
            service=deployment.service_name, reason=rollback_reason
        ).inc()

        async with self._lock:
            del self.active_deployments[deployment.deployment_id]

    async def get_deployment_status(self, deployment_id: str) -> dict[str, Any] | None:
        """Get current status of canary deployment."""
        async with self._lock:
            deployment = self.active_deployments.get(deployment_id)
            if deployment:
                return deployment.to_dict()
        return None

    async def get_active_deployments(self) -> list[dict[str, Any]]:
        """Get all active canary deployments."""
        async with self._lock:
            return [d.to_dict() for d in self.active_deployments.values()]

    async def cancel_deployment(self, deployment_id: str) -> bool:
        """Cancel active canary deployment."""
        async with self._lock:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                return False

            deployment.status = CanaryStatus.CANCELLED
            deployment.completed_at = datetime.utcnow()

            await self._apply_traffic_percentage(deployment, 0)

            logger.info(
                "CANARY_CANCELLED",
                extra={
                    "labels": {
                        "component": "canary_manager",
                        "deployment_id": deployment_id,
                    }
                },
            )

            canary_deployments_total.labels(
                service=deployment.service_name, status="cancelled"
            ).inc()
            canary_active_deployments.labels(service=deployment.service_name).dec()

            del self.active_deployments[deployment_id]
            return True
