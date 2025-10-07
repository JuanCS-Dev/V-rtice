"""Safety Manager - Dry-run, Rollback, Rate Limiting"""

from collections import deque
import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class SafetyManager:
    """Safety mechanisms for autonomous actions."""

    def __init__(self):
        self.action_history = deque(maxlen=1000)
        self.last_critical_action = 0

    def check_rate_limit(self, action_type: str) -> bool:
        """Prevent action oscillation - max 1 critical action/min."""
        if action_type == "CRITICAL":
            current_time = time.time()
            if current_time - self.last_critical_action < 60:
                logger.warning("Rate limit exceeded: CRITICAL action throttled")
                return False
            self.last_critical_action = current_time
        return True

    def auto_rollback(
        self, action: Dict, metrics_before: Dict, metrics_after: Dict
    ) -> bool:
        """Revert if metrics worsened >20% within 60s."""
        try:
            # Check key metrics for degradation
            for metric in ["cpu_usage", "latency_p99", "error_rate"]:
                before = metrics_before.get(metric, 0)
                after = metrics_after.get(metric, 0)

                if before > 0:
                    degradation = (after - before) / before
                    if degradation > 0.2:  # >20% worse
                        logger.error(
                            f"AUTO-ROLLBACK triggered: {metric} degraded "
                            f"{degradation*100:.1f}%"
                        )
                        return True

            return False

        except Exception as e:
            logger.error(f"Rollback check error: {e}")
            return True  # Rollback on error (conservative)

    def log_action(self, action: Dict):
        """Log action for audit trail."""
        self.action_history.append({"timestamp": time.time(), "action": action})
