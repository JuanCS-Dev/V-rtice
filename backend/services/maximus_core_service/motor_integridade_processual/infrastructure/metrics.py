"""Prometheus metrics collection."""

from typing import Dict

class MetricsCollector:
    """Collects and exports metrics."""
    
    def __init__(self):
        self.counters: Dict[str, int] = {
            "evaluations_total": 0,
            "approved": 0,
            "rejected": 0,
            "escalated": 0,
            "vetoed": 0
        }
    
    def record_decision(self, decision: str) -> None:
        """Record a decision metric."""
        self.counters["evaluations_total"] += 1
        self.counters[decision] = self.counters.get(decision, 0) + 1
    
    def get_metrics(self) -> Dict[str, int]:
        """Get current metrics."""
        return self.counters.copy()
