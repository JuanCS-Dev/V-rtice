"""
Metrics collection and aggregation
"""

import time
from typing import Dict, Any
from datetime import datetime
from collections import defaultdict


class MetricsCollector:
    """
    Collect and aggregate service metrics

    Tracks:
    - Request counts
    - Execution times
    - Success/failure rates
    - Resource usage
    """

    def __init__(self):
        self.start_time = time.time()
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}

    def increment(self, metric: str, value: int = 1):
        """Increment counter metric"""
        self.counters[metric] += value

    def record_time(self, metric: str, duration_ms: float):
        """Record timing metric"""
        self.timers[metric].append(duration_ms)

    def set_gauge(self, metric: str, value: Any):
        """Set gauge value"""
        self.gauges[metric] = value

    def get_uptime(self) -> int:
        """Get service uptime in seconds"""
        return int(time.time() - self.start_time)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': self.get_uptime(),
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers': {}
        }

        # Calculate timer statistics
        for metric, times in self.timers.items():
            if times:
                summary['timers'][metric] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times),
                    'min_ms': min(times),
                    'max_ms': max(times)
                }

        return summary

    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()
