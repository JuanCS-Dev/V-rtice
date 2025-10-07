"""
Monitoring & Alerting System for Cognitive Defense.

Prometheus metrics + alerting:
- Request latency (histogram)
- Throughput (counter)
- Model confidence (gauge)
- Cache hit rate (gauge)
- Error rate (counter)
- Model drift alerts
- Performance degradation alerts
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any, Dict, List, Optional

from config import get_settings
from prometheus_client import Counter, Gauge, generate_latest, Histogram, REGISTRY

logger = logging.getLogger(__name__)

settings = get_settings()


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Request metrics
request_total = Counter(
    "cognitive_defense_requests_total",
    "Total number of analysis requests",
    ["module", "status"],
)

request_duration = Histogram(
    "cognitive_defense_request_duration_seconds",
    "Request duration in seconds",
    ["module"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Module-specific metrics
credibility_score = Gauge(
    "cognitive_defense_credibility_score", "Source credibility score", ["source_domain"]
)

emotional_score = Gauge(
    "cognitive_defense_emotional_score", "Emotional manipulation score", ["emotion"]
)

fallacy_count = Counter(
    "cognitive_defense_fallacy_total", "Total fallacies detected", ["fallacy_type"]
)

verification_status = Counter(
    "cognitive_defense_verification_total",
    "Fact-check verification results",
    ["status"],
)

# Model performance
model_confidence = Gauge(
    "cognitive_defense_model_confidence", "Model prediction confidence", ["model_name"]
)

model_latency = Histogram(
    "cognitive_defense_model_latency_seconds",
    "Model inference latency",
    ["model_name"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
)

# Cache metrics
cache_hit_total = Counter(
    "cognitive_defense_cache_hits_total", "Cache hits", ["cache_category"]
)

cache_miss_total = Counter(
    "cognitive_defense_cache_misses_total", "Cache misses", ["cache_category"]
)

cache_hit_rate = Gauge(
    "cognitive_defense_cache_hit_rate", "Cache hit rate", ["cache_category"]
)

# Error metrics
error_total = Counter(
    "cognitive_defense_errors_total", "Total errors", ["error_type", "module"]
)

# Drift metrics
model_drift_detected = Counter(
    "cognitive_defense_drift_total", "Model drift events", ["model_name"]
)


class MetricsCollector:
    """
    Collects and exposes metrics for Prometheus scraping.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize metrics collector."""
        if self._initialized:
            return

        self._initialized = True
        logger.info("✅ Metrics collector initialized")

    def record_request(
        self, module: str, duration: float, status: str = "success"
    ) -> None:
        """
        Record request metrics.

        Args:
            module: Module name
            duration: Request duration in seconds
            status: Request status (success/error)
        """
        request_total.labels(module=module, status=status).inc()
        request_duration.labels(module=module).observe(duration)

    def record_credibility(self, source_domain: str, score: float) -> None:
        """Record source credibility score."""
        credibility_score.labels(source_domain=source_domain).set(score)

    def record_emotional(self, emotion: str, score: float) -> None:
        """Record emotional manipulation score."""
        emotional_score.labels(emotion=emotion).set(score)

    def record_fallacy(self, fallacy_type: str, count: int = 1) -> None:
        """Record fallacy detection."""
        fallacy_count.labels(fallacy_type=fallacy_type).inc(count)

    def record_verification(self, status: str) -> None:
        """Record fact-check verification."""
        verification_status.labels(status=status).inc()

    def record_model_metrics(
        self, model_name: str, confidence: float, latency: float
    ) -> None:
        """
        Record model performance metrics.

        Args:
            model_name: Model identifier
            confidence: Prediction confidence
            latency: Inference latency in seconds
        """
        model_confidence.labels(model_name=model_name).set(confidence)
        model_latency.labels(model_name=model_name).observe(latency)

    def record_cache_hit(self, category: str) -> None:
        """Record cache hit."""
        cache_hit_total.labels(cache_category=category).inc()

    def record_cache_miss(self, category: str) -> None:
        """Record cache miss."""
        cache_miss_total.labels(cache_category=category).inc()

    def update_cache_hit_rate(self, category: str, hit_rate: float) -> None:
        """Update cache hit rate gauge."""
        cache_hit_rate.labels(cache_category=category).set(hit_rate)

    def record_error(self, error_type: str, module: str) -> None:
        """Record error."""
        error_total.labels(error_type=error_type, module=module).inc()

    def record_drift(self, model_name: str) -> None:
        """Record model drift detection."""
        model_drift_detected.labels(model_name=model_name).inc()

    def get_metrics(self) -> bytes:
        """
        Get Prometheus metrics in text format.

        Returns:
            Metrics in Prometheus exposition format
        """
        return generate_latest(REGISTRY)


class AlertingSystem:
    """
    Alerting system for cognitive defense.

    Sends alerts for:
    - Model drift detected
    - Performance degradation
    - High error rate
    - Cache failures
    """

    # Alert thresholds
    ERROR_RATE_THRESHOLD = 0.05  # 5%
    LATENCY_THRESHOLD = 2.0  # seconds
    CACHE_HIT_RATE_THRESHOLD = 0.5  # 50%

    def __init__(self):
        """Initialize alerting system."""
        self.alerts: List[Dict[str, Any]] = []
        self._alert_cooldowns: Dict[str, datetime] = {}

    async def check_and_alert(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check metrics and send alerts if thresholds exceeded.

        Args:
            metrics: System metrics dict

        Returns:
            List of alerts sent
        """
        alerts_sent = []

        # Check error rate
        error_rate = metrics.get("error_rate", 0.0)
        if error_rate > self.ERROR_RATE_THRESHOLD:
            alert = await self._send_alert(
                title="High Error Rate",
                message=f"Error rate {error_rate:.2%} exceeds threshold {self.ERROR_RATE_THRESHOLD:.2%}",
                severity=AlertSeverity.ERROR,
                metrics={"error_rate": error_rate},
            )
            if alert:
                alerts_sent.append(alert)

        # Check latency
        avg_latency = metrics.get("avg_latency_ms", 0) / 1000.0
        if avg_latency > self.LATENCY_THRESHOLD:
            alert = await self._send_alert(
                title="High Latency",
                message=f"Average latency {avg_latency:.2f}s exceeds threshold {self.LATENCY_THRESHOLD}s",
                severity=AlertSeverity.WARNING,
                metrics={"avg_latency_s": avg_latency},
            )
            if alert:
                alerts_sent.append(alert)

        # Check cache hit rate
        cache_hit_rate = metrics.get("cache_hit_rate", 1.0)
        if cache_hit_rate < self.CACHE_HIT_RATE_THRESHOLD:
            alert = await self._send_alert(
                title="Low Cache Hit Rate",
                message=f"Cache hit rate {cache_hit_rate:.2%} below threshold {self.CACHE_HIT_RATE_THRESHOLD:.2%}",
                severity=AlertSeverity.WARNING,
                metrics={"cache_hit_rate": cache_hit_rate},
            )
            if alert:
                alerts_sent.append(alert)

        # Check model drift
        if metrics.get("drift_detected", False):
            alert = await self._send_alert(
                title="Model Drift Detected",
                message="Model performance degradation detected. Retraining recommended.",
                severity=AlertSeverity.CRITICAL,
                metrics=metrics.get("drift_metrics", {}),
            )
            if alert:
                alerts_sent.append(alert)

        return alerts_sent

    async def _send_alert(
        self, title: str, message: str, severity: AlertSeverity, metrics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Send alert (with cooldown to prevent spam).

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            metrics: Related metrics

        Returns:
            Alert dict if sent, None if cooled down
        """
        # Check cooldown
        alert_key = f"{title}_{severity.value}"

        if alert_key in self._alert_cooldowns:
            last_alert = self._alert_cooldowns[alert_key]
            cooldown_duration = timedelta(hours=1)

            if datetime.utcnow() - last_alert < cooldown_duration:
                logger.debug(f"Alert {alert_key} in cooldown")
                return None

        # Create alert
        alert = {
            "title": title,
            "message": message,
            "severity": severity.value,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send alert
        logger.warning(f"🚨 ALERT [{severity.value.upper()}]: {title} - {message}")

        # In production:
        # - Send to Slack/PagerDuty/email
        # - Store in database
        # - Trigger webhooks

        # Store alert
        self.alerts.append(alert)
        self._alert_cooldowns[alert_key] = datetime.utcnow()

        return alert

    async def send_drift_alert(
        self, model_name: str, drift_metrics: Dict[str, Any]
    ) -> None:
        """
        Send model drift alert.

        Args:
            model_name: Model identifier
            drift_metrics: Drift detection metrics
        """
        await self._send_alert(
            title=f"Model Drift: {model_name}",
            message=f"Drift detected in {model_name}. Confidence={drift_metrics.get('avg_confidence', 0):.3f}",
            severity=AlertSeverity.CRITICAL,
            metrics=drift_metrics,
        )

    def get_recent_alerts(
        self, hours: int = 24, severity: Optional[AlertSeverity] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts.

        Args:
            hours: Hours to look back
            severity: Filter by severity (None = all)

        Returns:
            List of recent alerts
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        recent = [
            alert
            for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff
        ]

        if severity:
            recent = [a for a in recent if a["severity"] == severity.value]

        return recent


class MonitoringDashboard:
    """
    Monitoring dashboard for cognitive defense system.

    Aggregates metrics for visualization (Grafana).
    """

    def __init__(self):
        """Initialize dashboard."""
        self.collector = MetricsCollector()

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health metrics.

        Returns:
            Health metrics dict
        """
        # In production: query Prometheus for aggregated metrics
        # For now, return mock data

        return {
            "status": "healthy",
            "uptime_hours": 72.5,
            "total_requests": 125000,
            "avg_latency_ms": 450,
            "error_rate": 0.02,
            "cache_hit_rate": 0.78,
            "modules": {
                "source_credibility": {"status": "healthy", "avg_score": 0.65},
                "emotional_manipulation": {"status": "healthy", "avg_score": 0.32},
                "logical_fallacy": {"status": "healthy", "fallacy_count": 1520},
                "reality_distortion": {"status": "healthy", "verified_claims": 3200},
            },
        }


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

metrics_collector = MetricsCollector()
alerting_system = AlertingSystem()
monitoring_dashboard = MonitoringDashboard()
