"""Feature Importance Tracker - Track feature importance over time.

This module tracks how feature importances change over time, helping identify
trends, drift, and anomalies in model behavior for cybersecurity operations.

Key Features:
    - Time-series tracking of feature importances
    - Drift detection for feature importance shifts
    - Top feature history and trends
    - Anomaly detection in feature patterns
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np

from .base import FeatureImportance

logger = logging.getLogger(__name__)


@dataclass
class FeatureHistory:
    """Historical tracking of a single feature.

    Attributes:
        feature_name: Name of the feature
        importances: List of importance values over time
        timestamps: List of timestamps
        mean_importance: Mean importance
        std_importance: Standard deviation of importance
        trend: Trend direction ('increasing', 'decreasing', 'stable')
    """
    feature_name: str
    importances: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    mean_importance: float = 0.0
    std_importance: float = 0.0
    trend: str = "stable"

    def add_observation(self, importance: float, timestamp: Optional[datetime] = None):
        """Add new importance observation.

        Args:
            importance: Importance value
            timestamp: Timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        self.importances.append(importance)
        self.timestamps.append(timestamp)

        # Update statistics
        self._update_statistics()

    def _update_statistics(self):
        """Update mean, std, and trend."""
        if not self.importances:
            return

        self.mean_importance = float(np.mean(self.importances))
        self.std_importance = float(np.std(self.importances))

        # Detect trend (simple linear regression slope)
        if len(self.importances) >= 3:
            x = np.arange(len(self.importances))
            y = np.array(self.importances)

            # Simple linear regression
            slope = np.cov(x, y)[0, 1] / np.var(x) if np.var(x) > 0 else 0

            # Determine trend
            if slope > 0.01:
                self.trend = "increasing"
            elif slope < -0.01:
                self.trend = "decreasing"
            else:
                self.trend = "stable"

    def get_recent_importances(self, hours: int = 24) -> List[float]:
        """Get importances from last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent importances
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = []

        for importance, timestamp in zip(self.importances, self.timestamps):
            if timestamp >= cutoff:
                recent.append(importance)

        return recent


class FeatureImportanceTracker:
    """Track feature importance over time for drift detection and analysis."""

    def __init__(self, max_history: int = 10000):
        """Initialize FeatureImportanceTracker.

        Args:
            max_history: Maximum number of observations to keep per feature
        """
        self.max_history = max_history

        # Feature histories
        self.feature_histories: Dict[str, FeatureHistory] = {}

        # Global statistics
        self.total_explanations: int = 0
        self.start_time: datetime = datetime.utcnow()

        logger.info(f"FeatureImportanceTracker initialized (max_history={max_history})")

    def track_explanation(
        self,
        features: List[FeatureImportance],
        timestamp: Optional[datetime] = None
    ):
        """Track features from an explanation.

        Args:
            features: List of FeatureImportance objects
            timestamp: Timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Track each feature
        for feature in features:
            if feature.feature_name not in self.feature_histories:
                self.feature_histories[feature.feature_name] = FeatureHistory(
                    feature_name=feature.feature_name
                )

            history = self.feature_histories[feature.feature_name]
            history.add_observation(feature.importance, timestamp)

            # Trim history if too large
            if len(history.importances) > self.max_history:
                history.importances = history.importances[-self.max_history:]
                history.timestamps = history.timestamps[-self.max_history:]
                history._update_statistics()

        self.total_explanations += 1

        logger.debug(f"Tracked {len(features)} features (total explanations: {self.total_explanations})")

    def get_top_features(self, n: int = 10, time_window_hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get top N most important features.

        Args:
            n: Number of top features to return
            time_window_hours: Optional time window (hours) to consider

        Returns:
            List of top feature dicts
        """
        feature_stats = []

        for feature_name, history in self.feature_histories.items():
            if time_window_hours:
                importances = history.get_recent_importances(time_window_hours)
            else:
                importances = history.importances

            if importances:
                mean_importance = np.mean(np.abs(importances))  # Absolute importance

                feature_stats.append({
                    'feature_name': feature_name,
                    'mean_importance': float(mean_importance),
                    'std_importance': float(np.std(importances)),
                    'count': len(importances),
                    'trend': history.trend
                })

        # Sort by mean importance
        feature_stats.sort(key=lambda x: x['mean_importance'], reverse=True)

        return feature_stats[:n]

    def detect_drift(
        self,
        feature_name: str,
        window_size: int = 100,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """Detect drift in feature importance.

        Args:
            feature_name: Feature to check
            window_size: Size of sliding window for comparison
            threshold: Drift threshold (relative change)

        Returns:
            Drift detection result dict
        """
        if feature_name not in self.feature_histories:
            return {
                'drift_detected': False,
                'reason': 'Feature not tracked'
            }

        history = self.feature_histories[feature_name]

        if len(history.importances) < window_size * 2:
            return {
                'drift_detected': False,
                'reason': 'Insufficient data'
            }

        # Compare recent window to older window
        recent = history.importances[-window_size:]
        older = history.importances[-2*window_size:-window_size]

        recent_mean = np.mean(np.abs(recent))
        older_mean = np.mean(np.abs(older))

        # Calculate relative change
        if older_mean > 0:
            relative_change = (recent_mean - older_mean) / older_mean
        else:
            relative_change = 0.0

        drift_detected = abs(relative_change) > threshold

        return {
            'drift_detected': drift_detected,
            'feature_name': feature_name,
            'recent_mean': float(recent_mean),
            'older_mean': float(older_mean),
            'relative_change': float(relative_change),
            'threshold': threshold,
            'direction': 'increase' if relative_change > 0 else 'decrease',
            'severity': 'high' if abs(relative_change) > 2*threshold else 'medium'
        }

    def detect_global_drift(
        self,
        top_n: int = 20,
        window_size: int = 100,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """Detect drift across all tracked features.

        Args:
            top_n: Number of top features to check
            window_size: Window size for comparison
            threshold: Drift threshold

        Returns:
            Global drift detection result
        """
        top_features = self.get_top_features(n=top_n)
        drifted_features = []

        for feature_info in top_features:
            feature_name = feature_info['feature_name']
            drift_result = self.detect_drift(feature_name, window_size, threshold)

            if drift_result['drift_detected']:
                drifted_features.append(drift_result)

        # Global drift severity
        if len(drifted_features) >= len(top_features) * 0.5:
            severity = 'critical'
        elif len(drifted_features) >= len(top_features) * 0.25:
            severity = 'high'
        elif len(drifted_features) > 0:
            severity = 'medium'
        else:
            severity = 'none'

        return {
            'drift_detected': len(drifted_features) > 0,
            'num_drifted_features': len(drifted_features),
            'total_features_checked': len(top_features),
            'drift_percentage': (len(drifted_features) / len(top_features) * 100) if top_features else 0,
            'severity': severity,
            'drifted_features': drifted_features
        }

    def get_feature_trend(self, feature_name: str) -> Dict[str, Any]:
        """Get trend information for a feature.

        Args:
            feature_name: Feature name

        Returns:
            Trend information dict
        """
        if feature_name not in self.feature_histories:
            return {
                'found': False,
                'feature_name': feature_name
            }

        history = self.feature_histories[feature_name]

        return {
            'found': True,
            'feature_name': feature_name,
            'mean_importance': history.mean_importance,
            'std_importance': history.std_importance,
            'trend': history.trend,
            'num_observations': len(history.importances),
            'first_seen': history.timestamps[0].isoformat() if history.timestamps else None,
            'last_seen': history.timestamps[-1].isoformat() if history.timestamps else None
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get global tracker statistics.

        Returns:
            Statistics dict
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            'total_explanations': self.total_explanations,
            'num_features_tracked': len(self.feature_histories),
            'uptime_seconds': uptime,
            'explanations_per_second': self.total_explanations / uptime if uptime > 0 else 0,
            'start_time': self.start_time.isoformat(),
            'memory_usage_mb': self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB.

        Returns:
            Estimated memory usage
        """
        # Rough estimate: each observation ~100 bytes
        total_observations = sum(len(h.importances) for h in self.feature_histories.values())
        return (total_observations * 100) / (1024 * 1024)

    def export_to_dict(self) -> Dict[str, Any]:
        """Export tracker state to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'statistics': self.get_statistics(),
            'top_features': self.get_top_features(n=50),
            'feature_histories': {
                name: {
                    'mean_importance': history.mean_importance,
                    'std_importance': history.std_importance,
                    'trend': history.trend,
                    'num_observations': len(history.importances)
                }
                for name, history in self.feature_histories.items()
            }
        }

    def clear_old_data(self, days: int = 30):
        """Clear data older than N days.

        Args:
            days: Number of days to keep
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        total_removed = 0

        for feature_name, history in self.feature_histories.items():
            # Find cutoff index
            cutoff_idx = 0
            for i, timestamp in enumerate(history.timestamps):
                if timestamp >= cutoff:
                    cutoff_idx = i
                    break

            if cutoff_idx > 0:
                # Remove old data
                removed = cutoff_idx
                history.importances = history.importances[cutoff_idx:]
                history.timestamps = history.timestamps[cutoff_idx:]
                history._update_statistics()
                total_removed += removed

        logger.info(f"Cleared {total_removed} old observations (older than {days} days)")

        return total_removed
