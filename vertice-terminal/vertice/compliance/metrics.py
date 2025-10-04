"""
📊 Metrics Collector - Coleta e agregação de métricas de segurança e compliance

Métricas coletadas:
- Security Metrics (incidents, threats, vulnerabilities)
- Compliance Metrics (control coverage, assessment scores)
- Operational Metrics (MTTD, MTTR, SLA compliance)
- Performance Metrics (scan times, detection rates)
- Audit Metrics (event counts, failed authentications)

Features:
- Time-series data collection
- Aggregation (hourly, daily, weekly, monthly)
- KPI calculation
- Trend analysis
- Alerting on threshold violations
- Backend integration for distributed metrics
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Tipos de métrica"""
    # Security
    INCIDENTS_CREATED = "incidents_created"
    INCIDENTS_RESOLVED = "incidents_resolved"
    THREATS_DETECTED = "threats_detected"
    VULNERABILITIES_FOUND = "vulnerabilities_found"
    MALWARE_DETECTED = "malware_detected"

    # Compliance
    COMPLIANCE_SCORE = "compliance_score"
    CONTROLS_IMPLEMENTED = "controls_implemented"
    GAPS_IDENTIFIED = "gaps_identified"
    ASSESSMENTS_COMPLETED = "assessments_completed"

    # Operational
    MTTD = "mean_time_to_detect"  # Mean Time To Detect
    MTTR = "mean_time_to_resolve"  # Mean Time To Resolve
    SLA_BREACHES = "sla_breaches"
    SLA_COMPLIANCE = "sla_compliance_percentage"

    # Audit
    AUDIT_EVENTS = "audit_events"
    FAILED_LOGINS = "failed_logins"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATIONS = "privilege_escalations"

    # Performance
    SCAN_DURATION = "scan_duration_seconds"
    DETECTION_RATE = "detection_rate_percentage"
    FALSE_POSITIVE_RATE = "false_positive_rate_percentage"

    # Evidence
    EVIDENCE_COLLECTED = "evidence_collected"
    CHAIN_OF_CUSTODY_UPDATES = "chain_of_custody_updates"

    # Custom
    CUSTOM = "custom"


class AggregationType(Enum):
    """Tipo de agregação"""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    LAST = "last"


@dataclass
class Metric:
    """
    Métrica individual

    Attributes:
        id: Unique metric ID
        metric_type: Type of metric
        value: Metric value
        timestamp: When measured
        tags: Categorization tags
        metadata: Additional data
        unit: Unit of measurement
    """
    id: str
    metric_type: MetricType
    value: float
    timestamp: datetime

    # Categorization
    tags: Dict[str, str] = field(default_factory=dict)

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Units
    unit: str = ""  # seconds, percentage, count, etc


@dataclass
class KPI:
    """
    Key Performance Indicator

    KPIs are calculated metrics with targets and thresholds

    Attributes:
        name: KPI name
        current_value: Current value
        target_value: Target/goal value
        threshold_warning: Warning threshold
        threshold_critical: Critical threshold
        unit: Unit of measurement
        trend: Trend direction (up/down/stable)
        status: Status (ok/warning/critical)
    """
    name: str
    current_value: float
    target_value: float

    # Thresholds
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

    # Display
    unit: str = ""
    trend: str = "stable"  # up, down, stable
    status: str = "ok"  # ok, warning, critical

    # Metadata
    description: str = ""
    calculated_at: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """
    Security & Compliance Metrics Collection System

    Features:
    - Time-series metric storage
    - Aggregation and rollup
    - KPI calculation
    - Trend analysis
    - Threshold alerting
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do metrics_service
            use_backend: Se True, integra com backend
        """
        self.backend_url = backend_url or "http://localhost:8017"
        self.use_backend = use_backend

        # Metric storage (in-memory time-series)
        self.metrics: List[Metric] = []

        # KPI registry
        self.kpis: Dict[str, KPI] = {}

    def record(
        self,
        metric_type: MetricType,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        unit: str = "",
    ) -> Metric:
        """
        Registra métrica

        Args:
            metric_type: Type of metric
            value: Metric value
            tags: Categorization tags
            metadata: Additional data
            unit: Unit of measurement

        Returns:
            Metric object
        """
        import uuid

        metric = Metric(
            id=f"MET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            metadata=metadata or {},
            unit=unit,
        )

        self.metrics.append(metric)

        logger.debug(
            f"Metric recorded: {metric_type.value} = {value} {unit}"
        )

        # Send to backend
        if self.use_backend:
            try:
                self._send_to_backend(metric)
            except Exception as e:
                logger.error(f"Backend metric send failed: {e}")

        return metric

    def aggregate(
        self,
        metric_type: MetricType,
        aggregation: AggregationType,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> float:
        """
        Agrega métricas

        Args:
            metric_type: Type of metric
            aggregation: Aggregation type
            start_time: Start of time window
            end_time: End of time window
            tags: Filter by tags

        Returns:
            Aggregated value
        """
        # Filter metrics
        filtered = [
            m for m in self.metrics
            if m.metric_type == metric_type
        ]

        if start_time:
            filtered = [m for m in filtered if m.timestamp >= start_time]

        if end_time:
            filtered = [m for m in filtered if m.timestamp <= end_time]

        if tags:
            filtered = [
                m for m in filtered
                if all(m.tags.get(k) == v for k, v in tags.items())
            ]

        if not filtered:
            return 0.0

        values = [m.value for m in filtered]

        # Aggregate
        if aggregation == AggregationType.SUM:
            return sum(values)

        elif aggregation == AggregationType.AVERAGE:
            return sum(values) / len(values)

        elif aggregation == AggregationType.MIN:
            return min(values)

        elif aggregation == AggregationType.MAX:
            return max(values)

        elif aggregation == AggregationType.COUNT:
            return float(len(values))

        elif aggregation == AggregationType.LAST:
            return values[-1] if values else 0.0

        return 0.0

    def calculate_kpi(
        self,
        name: str,
        metric_type: MetricType,
        aggregation: AggregationType,
        target_value: float,
        threshold_warning: Optional[float] = None,
        threshold_critical: Optional[float] = None,
        time_window_hours: int = 24,
        unit: str = "",
        description: str = "",
    ) -> KPI:
        """
        Calcula KPI

        Args:
            name: KPI name
            metric_type: Type of metric to aggregate
            aggregation: Aggregation type
            target_value: Target value
            threshold_warning: Warning threshold
            threshold_critical: Critical threshold
            time_window_hours: Time window in hours
            unit: Unit of measurement
            description: KPI description

        Returns:
            KPI object
        """
        # Calculate time window
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)

        # Aggregate metric
        current_value = self.aggregate(
            metric_type=metric_type,
            aggregation=aggregation,
            start_time=start_time,
            end_time=end_time,
        )

        # Determine status
        status = "ok"

        if threshold_critical is not None:
            if current_value >= threshold_critical:
                status = "critical"

        if threshold_warning is not None:
            if current_value >= threshold_warning:
                status = "warning"

        # Calculate trend (compare to previous period)
        previous_start = start_time - timedelta(hours=time_window_hours)
        previous_end = start_time

        previous_value = self.aggregate(
            metric_type=metric_type,
            aggregation=aggregation,
            start_time=previous_start,
            end_time=previous_end,
        )

        if previous_value > 0:
            change = ((current_value - previous_value) / previous_value) * 100

            if change > 5:
                trend = "up"
            elif change < -5:
                trend = "down"
            else:
                trend = "stable"
        else:
            trend = "stable"

        kpi = KPI(
            name=name,
            current_value=current_value,
            target_value=target_value,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            unit=unit,
            trend=trend,
            status=status,
            description=description,
        )

        # Register KPI
        self.kpis[name] = kpi

        logger.info(
            f"KPI calculated: {name} = {current_value:.2f} {unit} "
            f"(target: {target_value}, status: {status})"
        )

        return kpi

    def get_security_kpis(self) -> Dict[str, KPI]:
        """
        Retorna KPIs de segurança principais

        Returns:
            Dict of KPIs
        """
        kpis = {}

        # MTTD (Mean Time To Detect)
        kpis["mttd"] = self.calculate_kpi(
            name="Mean Time To Detect (MTTD)",
            metric_type=MetricType.MTTD,
            aggregation=AggregationType.AVERAGE,
            target_value=15.0,  # 15 minutes target
            threshold_warning=30.0,
            threshold_critical=60.0,
            time_window_hours=24,
            unit="minutes",
            description="Average time to detect security incidents",
        )

        # MTTR (Mean Time To Resolve)
        kpis["mttr"] = self.calculate_kpi(
            name="Mean Time To Resolve (MTTR)",
            metric_type=MetricType.MTTR,
            aggregation=AggregationType.AVERAGE,
            target_value=120.0,  # 2 hours target
            threshold_warning=240.0,
            threshold_critical=480.0,
            time_window_hours=24,
            unit="minutes",
            description="Average time to resolve security incidents",
        )

        # Incidents Created
        kpis["incidents_created"] = self.calculate_kpi(
            name="Incidents Created (24h)",
            metric_type=MetricType.INCIDENTS_CREATED,
            aggregation=AggregationType.COUNT,
            target_value=0.0,
            threshold_warning=5.0,
            threshold_critical=10.0,
            time_window_hours=24,
            unit="count",
            description="Number of security incidents created",
        )

        # Threats Detected
        kpis["threats_detected"] = self.calculate_kpi(
            name="Threats Detected (24h)",
            metric_type=MetricType.THREATS_DETECTED,
            aggregation=AggregationType.COUNT,
            target_value=0.0,
            threshold_warning=10.0,
            threshold_critical=25.0,
            time_window_hours=24,
            unit="count",
            description="Number of threats detected",
        )

        # Detection Rate
        kpis["detection_rate"] = self.calculate_kpi(
            name="Detection Rate",
            metric_type=MetricType.DETECTION_RATE,
            aggregation=AggregationType.AVERAGE,
            target_value=95.0,  # 95% target
            threshold_warning=85.0,
            threshold_critical=75.0,
            time_window_hours=24,
            unit="%",
            description="Percentage of threats successfully detected",
        )

        return kpis

    def get_compliance_kpis(self) -> Dict[str, KPI]:
        """
        Retorna KPIs de compliance

        Returns:
            Dict of KPIs
        """
        kpis = {}

        # Compliance Score
        kpis["compliance_score"] = self.calculate_kpi(
            name="Compliance Score",
            metric_type=MetricType.COMPLIANCE_SCORE,
            aggregation=AggregationType.LAST,
            target_value=100.0,
            threshold_warning=80.0,
            threshold_critical=70.0,
            time_window_hours=720,  # 30 days
            unit="%",
            description="Overall compliance score across frameworks",
        )

        # Controls Implemented
        kpis["controls_implemented"] = self.calculate_kpi(
            name="Controls Implemented",
            metric_type=MetricType.CONTROLS_IMPLEMENTED,
            aggregation=AggregationType.LAST,
            target_value=100.0,
            time_window_hours=720,
            unit="count",
            description="Number of implemented security controls",
        )

        # Gaps Identified
        kpis["gaps_identified"] = self.calculate_kpi(
            name="Compliance Gaps",
            metric_type=MetricType.GAPS_IDENTIFIED,
            aggregation=AggregationType.LAST,
            target_value=0.0,
            threshold_warning=5.0,
            threshold_critical=10.0,
            time_window_hours=720,
            unit="count",
            description="Number of compliance gaps identified",
        )

        return kpis

    def get_operational_kpis(self) -> Dict[str, KPI]:
        """
        Retorna KPIs operacionais

        Returns:
            Dict of KPIs
        """
        kpis = {}

        # SLA Compliance
        kpis["sla_compliance"] = self.calculate_kpi(
            name="SLA Compliance",
            metric_type=MetricType.SLA_COMPLIANCE,
            aggregation=AggregationType.AVERAGE,
            target_value=95.0,
            threshold_warning=90.0,
            threshold_critical=85.0,
            time_window_hours=168,  # 7 days
            unit="%",
            description="Percentage of incidents meeting SLA targets",
        )

        # Failed Logins
        kpis["failed_logins"] = self.calculate_kpi(
            name="Failed Login Attempts (24h)",
            metric_type=MetricType.FAILED_LOGINS,
            aggregation=AggregationType.COUNT,
            target_value=0.0,
            threshold_warning=50.0,
            threshold_critical=100.0,
            time_window_hours=24,
            unit="count",
            description="Number of failed authentication attempts",
        )

        return kpis

    def get_all_kpis(self) -> Dict[str, KPI]:
        """
        Retorna todos os KPIs

        Returns:
            Dict of all KPIs
        """
        kpis = {}

        kpis.update(self.get_security_kpis())
        kpis.update(self.get_compliance_kpis())
        kpis.update(self.get_operational_kpis())

        return kpis

    def get_metrics_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Retorna resumo de métricas

        Args:
            start_time: Start of time window
            end_time: End of time window

        Returns:
            Summary dict
        """
        # Filter metrics
        metrics = self.metrics

        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]

        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]

        # Count by type
        by_type = defaultdict(int)
        for metric in metrics:
            by_type[metric.metric_type.value] += 1

        return {
            "total_metrics": len(metrics),
            "by_type": dict(by_type),
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
        }

    def get_time_series(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 60,
    ) -> List[Tuple[datetime, float]]:
        """
        Retorna time-series de métrica

        Args:
            metric_type: Type of metric
            start_time: Start time
            end_time: End time
            interval_minutes: Interval in minutes

        Returns:
            List of (timestamp, value) tuples
        """
        # Filter metrics
        metrics = [
            m for m in self.metrics
            if m.metric_type == metric_type
            and start_time <= m.timestamp <= end_time
        ]

        # Create time buckets
        time_series = []
        current = start_time

        while current <= end_time:
            bucket_end = current + timedelta(minutes=interval_minutes)

            # Get metrics in this bucket
            bucket_metrics = [
                m for m in metrics
                if current <= m.timestamp < bucket_end
            ]

            # Aggregate
            if bucket_metrics:
                avg_value = sum(m.value for m in bucket_metrics) / len(bucket_metrics)
            else:
                avg_value = 0.0

            time_series.append((current, avg_value))

            current = bucket_end

        return time_series

    def _send_to_backend(self, metric: Metric) -> None:
        """Envia métrica para backend"""
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/metrics",
                    json={
                        "id": metric.id,
                        "metric_type": metric.metric_type.value,
                        "value": metric.value,
                        "timestamp": metric.timestamp.isoformat(),
                        "tags": metric.tags,
                        "metadata": metric.metadata,
                        "unit": metric.unit,
                    }
                )
                response.raise_for_status()

        except Exception as e:
            logger.error(f"Backend metric send failed: {e}")
            raise

    def export_metrics_csv(
        self,
        output_path: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> bool:
        """
        Exporta métricas para CSV

        Args:
            output_path: Output file path
            start_time: Start time filter
            end_time: End time filter

        Returns:
            True se sucesso
        """
        # Filter metrics
        metrics = self.metrics

        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]

        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]

        try:
            with open(output_path, 'w') as f:
                f.write("Timestamp,Metric Type,Value,Unit,Tags\n")

                for metric in metrics:
                    tags_str = ";".join(f"{k}={v}" for k, v in metric.tags.items())

                    f.write(
                        f"{metric.timestamp.isoformat()},{metric.metric_type.value},"
                        f"{metric.value},{metric.unit},{tags_str}\n"
                    )

            logger.info(f"Exported {len(metrics)} metrics to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
