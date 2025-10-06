"""Fairness Monitoring System for Cybersecurity AI Models.

This module implements continuous fairness monitoring with alerting,
historical tracking, and trend analysis for deployed AI models.

Features:
    - Real-time fairness monitoring
    - Historical tracking with time-series analysis
    - Alert generation for fairness violations
    - Trend analysis and drift detection
    - Dashboard integration support
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .base import (
    ProtectedAttribute,
    FairnessMetric,
    FairnessResult,
    BiasDetectionResult
)
from .constraints import FairnessConstraints
from .bias_detector import BiasDetector

logger = logging.getLogger(__name__)


@dataclass
class FairnessAlert:
    """Alert for fairness violation.

    Attributes:
        alert_id: Unique alert identifier
        timestamp: When alert was triggered
        severity: Alert severity (low, medium, high, critical)
        metric: Fairness metric that triggered alert
        protected_attribute: Affected protected attribute
        violation_details: Details of the violation
        recommended_action: Suggested mitigation action
        auto_mitigated: Whether automatic mitigation was applied
    """
    alert_id: str
    timestamp: datetime
    severity: str
    metric: FairnessMetric
    protected_attribute: ProtectedAttribute
    violation_details: Dict[str, Any]
    recommended_action: str
    auto_mitigated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FairnessSnapshot:
    """Snapshot of fairness metrics at a point in time.

    Attributes:
        timestamp: When snapshot was taken
        model_id: Model identifier
        protected_attribute: Protected attribute
        fairness_results: Fairness evaluation results
        bias_results: Bias detection results
        sample_size: Number of samples in snapshot
        metadata: Additional metadata
    """
    timestamp: datetime
    model_id: str
    protected_attribute: ProtectedAttribute
    fairness_results: Dict[FairnessMetric, FairnessResult]
    bias_results: Dict[str, BiasDetectionResult]
    sample_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class FairnessMonitor:
    """Fairness monitor for continuous tracking and alerting.

    Monitors fairness metrics over time, detects violations, generates alerts,
    and maintains historical records for trend analysis.

    Attributes:
        fairness_constraints: FairnessConstraints instance
        bias_detector: BiasDetector instance
        history_max_size: Maximum snapshots to keep in memory
        alert_threshold: Threshold for generating alerts
        enable_auto_mitigation: Whether to automatically mitigate violations
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize FairnessMonitor.

        Args:
            config: Configuration dictionary
        """
        config = config or {}

        # Initialize evaluators
        self.fairness_constraints = FairnessConstraints(config.get('fairness_config', {}))
        self.bias_detector = BiasDetector(config.get('bias_config', {}))

        # History settings
        self.history_max_size = config.get('history_max_size', 1000)
        self.history: deque = deque(maxlen=self.history_max_size)

        # Alert settings
        self.alert_threshold = config.get('alert_threshold', 'medium')  # low, medium, high, critical
        self.enable_auto_mitigation = config.get('enable_auto_mitigation', False)
        self.alerts: List[FairnessAlert] = []
        self.max_alerts = config.get('max_alerts', 500)

        # Monitoring frequency
        self.monitoring_frequency = config.get('monitoring_frequency', 'realtime')  # realtime, hourly, daily

        # Drift detection settings
        self.drift_window_size = config.get('drift_window_size', 100)
        self.drift_threshold = config.get('drift_threshold', 0.15)  # 15% change

        # Statistics
        self.total_evaluations = 0
        self.total_violations = 0
        self.total_alerts = 0

        logger.info(
            f"FairnessMonitor initialized with history_max_size={self.history_max_size}, "
            f"alert_threshold={self.alert_threshold}, "
            f"auto_mitigation={self.enable_auto_mitigation}"
        )

    def evaluate_fairness(
        self,
        predictions: np.ndarray,
        true_labels: Optional[np.ndarray],
        protected_attribute: np.ndarray,
        protected_value: Any,
        model_id: str,
        protected_attr_type: ProtectedAttribute = ProtectedAttribute.GEOGRAPHIC_LOCATION
    ) -> FairnessSnapshot:
        """Evaluate fairness and update monitoring state.

        Args:
            predictions: Model predictions
            true_labels: True labels (optional)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            model_id: Model identifier
            protected_attr_type: Type of protected attribute

        Returns:
            FairnessSnapshot with evaluation results
        """
        self.total_evaluations += 1

        # Evaluate fairness constraints
        fairness_results = self.fairness_constraints.evaluate_all_metrics(
            predictions,
            true_labels,
            protected_attribute,
            protected_value
        )

        # Update protected attribute in results
        for result in fairness_results.values():
            result.protected_attribute = protected_attr_type

        # Detect bias
        bias_results = self.bias_detector.detect_all_biases(
            predictions,
            protected_attribute,
            true_labels,
            protected_value
        )

        # Update protected attribute in bias results
        for result in bias_results.values():
            result.protected_attribute = protected_attr_type

        # Create snapshot
        snapshot = FairnessSnapshot(
            timestamp=datetime.utcnow(),
            model_id=model_id,
            protected_attribute=protected_attr_type,
            fairness_results=fairness_results,
            bias_results=bias_results,
            sample_size=len(predictions),
            metadata={
                'predictions_mean': float(np.mean(predictions)),
                'predictions_std': float(np.std(predictions))
            }
        )

        # Add to history
        self.history.append(snapshot)

        # Check for violations and generate alerts
        self._check_violations(snapshot)

        logger.debug(
            f"Fairness evaluation complete for model {model_id}: "
            f"{len(fairness_results)} fairness metrics, "
            f"{len(bias_results)} bias tests"
        )

        return snapshot

    def get_fairness_trends(
        self,
        model_id: Optional[str] = None,
        metric: Optional[FairnessMetric] = None,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """Get fairness trends over time.

        Args:
            model_id: Filter by model ID (optional)
            metric: Filter by metric (optional)
            lookback_hours: Hours to look back

        Returns:
            Dictionary with trend analysis
        """
        # Filter history
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        filtered_history = [
            s for s in self.history
            if s.timestamp >= cutoff_time and (model_id is None or s.model_id == model_id)
        ]

        if not filtered_history:
            return {
                'trend': 'no_data',
                'num_snapshots': 0,
                'time_range_hours': lookback_hours
            }

        # Extract metric values over time
        timestamps = [s.timestamp for s in filtered_history]
        metric_values = defaultdict(list)

        for snapshot in filtered_history:
            for m, result in snapshot.fairness_results.items():
                if metric is None or m == metric:
                    metric_values[m.value].append({
                        'timestamp': snapshot.timestamp,
                        'difference': result.difference,
                        'is_fair': result.is_fair
                    })

        # Analyze trends
        trends = {}
        for m, values in metric_values.items():
            if len(values) < 2:
                continue

            # Calculate trend direction
            diffs = [v['difference'] for v in values]
            recent_mean = np.mean(diffs[-10:]) if len(diffs) >= 10 else np.mean(diffs)
            older_mean = np.mean(diffs[:len(diffs)//2]) if len(diffs) >= 4 else np.mean(diffs)

            if recent_mean > older_mean * 1.1:
                trend_direction = 'worsening'
            elif recent_mean < older_mean * 0.9:
                trend_direction = 'improving'
            else:
                trend_direction = 'stable'

            # Violation rate
            violation_rate = sum(1 for v in values if not v['is_fair']) / len(values)

            trends[m] = {
                'trend_direction': trend_direction,
                'current_mean_difference': float(recent_mean),
                'historical_mean_difference': float(older_mean),
                'violation_rate': float(violation_rate),
                'num_snapshots': len(values)
            }

        return {
            'trends': trends,
            'num_snapshots': len(filtered_history),
            'time_range_hours': lookback_hours,
            'start_time': min(timestamps).isoformat(),
            'end_time': max(timestamps).isoformat()
        }

    def detect_drift(
        self,
        model_id: Optional[str] = None,
        metric: Optional[FairnessMetric] = None
    ) -> Dict[str, Any]:
        """Detect drift in fairness metrics.

        Args:
            model_id: Filter by model ID (optional)
            metric: Filter by metric (optional)

        Returns:
            Dictionary with drift detection results
        """
        # Filter history
        filtered_history = [
            s for s in self.history
            if model_id is None or s.model_id == model_id
        ]

        if len(filtered_history) < self.drift_window_size * 2:
            return {
                'drift_detected': False,
                'reason': 'insufficient_data',
                'required_snapshots': self.drift_window_size * 2,
                'actual_snapshots': len(filtered_history)
            }

        # Compare recent window to older window
        recent_window = filtered_history[-self.drift_window_size:]
        older_window = filtered_history[-2*self.drift_window_size:-self.drift_window_size]

        drift_results = {}

        # Analyze each metric
        for m in FairnessMetric:
            if metric is not None and m != metric:
                continue

            # Extract differences from both windows
            recent_diffs = []
            older_diffs = []

            for snapshot in recent_window:
                if m in snapshot.fairness_results:
                    recent_diffs.append(snapshot.fairness_results[m].difference)

            for snapshot in older_window:
                if m in snapshot.fairness_results:
                    older_diffs.append(snapshot.fairness_results[m].difference)

            if not recent_diffs or not older_diffs:
                continue

            # Calculate means
            recent_mean = np.mean(recent_diffs)
            older_mean = np.mean(older_diffs)

            # Relative change
            relative_change = (recent_mean - older_mean) / older_mean if older_mean > 0 else 0.0

            # Drift detected?
            drift_detected = abs(relative_change) > self.drift_threshold

            # Severity
            if abs(relative_change) > 0.5:
                severity = 'critical'
            elif abs(relative_change) > 0.3:
                severity = 'high'
            elif abs(relative_change) > self.drift_threshold:
                severity = 'medium'
            else:
                severity = 'low'

            drift_results[m.value] = {
                'drift_detected': drift_detected,
                'recent_mean': float(recent_mean),
                'older_mean': float(older_mean),
                'relative_change': float(relative_change),
                'direction': 'worsening' if relative_change > 0 else 'improving',
                'severity': severity
            }

        # Overall drift assessment
        num_drifted = sum(1 for r in drift_results.values() if r['drift_detected'])
        overall_drift = num_drifted > 0

        return {
            'drift_detected': overall_drift,
            'num_drifted_metrics': num_drifted,
            'total_metrics_checked': len(drift_results),
            'metrics': drift_results,
            'window_size': self.drift_window_size,
            'threshold': self.drift_threshold
        }

    def get_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 50,
        since_hours: Optional[int] = None
    ) -> List[FairnessAlert]:
        """Get recent alerts.

        Args:
            severity: Filter by severity (optional)
            limit: Maximum number of alerts to return
            since_hours: Only return alerts from last N hours (optional)

        Returns:
            List of FairnessAlert objects
        """
        filtered_alerts = self.alerts

        # Filter by severity
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]

        # Filter by time
        if since_hours is not None:
            cutoff = datetime.utcnow() - timedelta(hours=since_hours)
            filtered_alerts = [a for a in filtered_alerts if a.timestamp >= cutoff]

        # Sort by timestamp (newest first) and limit
        filtered_alerts = sorted(filtered_alerts, key=lambda a: a.timestamp, reverse=True)
        return filtered_alerts[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics.

        Returns:
            Dictionary with statistics
        """
        # Calculate violation rate
        violation_rate = self.total_violations / self.total_evaluations if self.total_evaluations > 0 else 0.0

        # Recent alerts by severity
        recent_alerts_24h = [
            a for a in self.alerts
            if a.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ]

        alerts_by_severity = defaultdict(int)
        for alert in recent_alerts_24h:
            alerts_by_severity[alert.severity] += 1

        return {
            'total_evaluations': self.total_evaluations,
            'total_violations': self.total_violations,
            'total_alerts': self.total_alerts,
            'violation_rate': float(violation_rate),
            'snapshots_in_history': len(self.history),
            'alerts_last_24h': len(recent_alerts_24h),
            'alerts_by_severity_24h': dict(alerts_by_severity),
            'auto_mitigation_enabled': self.enable_auto_mitigation
        }

    def clear_history(self, before_timestamp: Optional[datetime] = None):
        """Clear monitoring history.

        Args:
            before_timestamp: Clear history before this timestamp (optional, clears all if None)
        """
        if before_timestamp is None:
            self.history.clear()
            logger.info("Cleared all fairness monitoring history")
        else:
            original_size = len(self.history)
            self.history = deque(
                [s for s in self.history if s.timestamp >= before_timestamp],
                maxlen=self.history_max_size
            )
            cleared = original_size - len(self.history)
            logger.info(f"Cleared {cleared} snapshots from fairness history")

    def _check_violations(self, snapshot: FairnessSnapshot):
        """Check for fairness violations and generate alerts.

        Args:
            snapshot: FairnessSnapshot to check
        """
        violations_found = []

        # Check fairness results
        for metric, result in snapshot.fairness_results.items():
            if not result.is_fair:
                violations_found.append({
                    'type': 'fairness',
                    'metric': metric,
                    'result': result
                })

        # Check bias results
        for method, result in snapshot.bias_results.items():
            if result.bias_detected and self._meets_alert_threshold(result.severity):
                violations_found.append({
                    'type': 'bias',
                    'method': method,
                    'result': result
                })

        # Update statistics
        if violations_found:
            self.total_violations += 1

        # Generate alerts
        for violation in violations_found:
            alert = self._create_alert(snapshot, violation)
            self.alerts.append(alert)
            self.total_alerts += 1

            # Trim alerts if exceeding max
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]

            logger.warning(
                f"Fairness alert generated: {alert.severity} - {alert.metric.value} - "
                f"{alert.violation_details.get('summary', 'No summary')}"
            )

    def _meets_alert_threshold(self, severity: str) -> bool:
        """Check if severity meets alert threshold.

        Args:
            severity: Violation severity

        Returns:
            True if should generate alert
        """
        severity_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        threshold_level = severity_levels.get(self.alert_threshold, 1)
        violation_level = severity_levels.get(severity, 0)

        return violation_level >= threshold_level

    def _create_alert(
        self,
        snapshot: FairnessSnapshot,
        violation: Dict[str, Any]
    ) -> FairnessAlert:
        """Create alert from violation.

        Args:
            snapshot: FairnessSnapshot with violation
            violation: Violation details

        Returns:
            FairnessAlert object
        """
        alert_id = f"alert_{snapshot.model_id}_{snapshot.timestamp.timestamp()}_{violation['type']}"

        if violation['type'] == 'fairness':
            result = violation['result']
            metric = violation['metric']
            severity = self._map_fairness_severity(result)

            violation_details = {
                'summary': f"{metric.value} violation: difference={result.difference:.3f}, threshold={result.threshold:.3f}",
                'difference': result.difference,
                'threshold': result.threshold,
                'group_0_value': result.group_0_value,
                'group_1_value': result.group_1_value
            }

            recommended_action = self._get_recommended_action(metric, result)

        else:  # bias
            result = violation['result']
            metric = FairnessMetric.DEMOGRAPHIC_PARITY  # Default
            severity = result.severity

            violation_details = {
                'summary': f"Bias detected via {result.detection_method}: {result.affected_groups}",
                'method': result.detection_method,
                'p_value': result.p_value,
                'effect_size': result.effect_size,
                'affected_groups': result.affected_groups
            }

            recommended_action = "Review model predictions and consider bias mitigation"

        alert = FairnessAlert(
            alert_id=alert_id,
            timestamp=snapshot.timestamp,
            severity=severity,
            metric=metric,
            protected_attribute=snapshot.protected_attribute,
            violation_details=violation_details,
            recommended_action=recommended_action,
            auto_mitigated=False,
            metadata={
                'model_id': snapshot.model_id,
                'sample_size': snapshot.sample_size
            }
        )

        return alert

    def _map_fairness_severity(self, result: FairnessResult) -> str:
        """Map fairness result to severity level.

        Args:
            result: FairnessResult

        Returns:
            Severity level
        """
        # Based on how much the threshold is exceeded
        excess = result.difference - result.threshold

        if excess > result.threshold * 2:  # More than 3x threshold
            return 'critical'
        elif excess > result.threshold:  # More than 2x threshold
            return 'high'
        elif excess > result.threshold * 0.5:  # More than 1.5x threshold
            return 'medium'
        else:
            return 'low'

    def _get_recommended_action(
        self,
        metric: FairnessMetric,
        result: FairnessResult
    ) -> str:
        """Get recommended action for violation.

        Args:
            metric: Fairness metric
            result: FairnessResult

        Returns:
            Recommended action string
        """
        actions = {
            FairnessMetric.DEMOGRAPHIC_PARITY: "Consider threshold optimization or reweighing training data",
            FairnessMetric.EQUALIZED_ODDS: "Investigate performance disparity and apply threshold optimization",
            FairnessMetric.EQUAL_OPPORTUNITY: "Review true positive rates and adjust decision thresholds",
            FairnessMetric.CALIBRATION: "Apply calibration adjustment to align prediction scores",
            FairnessMetric.PREDICTIVE_PARITY: "Review precision across groups and retrain with balanced data",
            FairnessMetric.TREATMENT_EQUALITY: "Analyze error rates and apply error-based mitigation"
        }

        return actions.get(metric, "Review model and apply appropriate bias mitigation strategy")
