"""Performance Degradation Detector - PELT Change Point Detection"""

import logging

import numpy as np
import ruptures as rpt

logger = logging.getLogger(__name__)


class PerformanceDegradationDetector:
    """Detect performance degradation using PELT algorithm."""

    def __init__(self, penalty: int = 10, model: str = "rbf"):
        self.algo = rpt.Pelt(model=model, min_size=3)
        self.penalty = penalty

    def detect(self, latency_timeseries: np.ndarray) -> dict:
        """
        Identify degradation before SLA breach.

        Args:
            latency_timeseries: Array of latency measurements

        Returns:
            Dict with degradation_detected, changepoint_index, severity
        """
        if len(latency_timeseries) < 10:
            return {"degradation_detected": False, "reason": "insufficient_data"}

        try:
            # Detect change points
            result = self.algo.fit(latency_timeseries).predict(pen=self.penalty)

            if len(result) > 1:  # Has changepoint (last element is always len(signal))
                changepoint_idx = result[0]

                # Check if degradation is significant
                before = latency_timeseries[:changepoint_idx].mean()
                after = latency_timeseries[changepoint_idx:].mean()

                if after > before * 1.2:  # 20% degradation threshold
                    severity = (after - before) / before

                    logger.warning(
                        f"Performance degradation detected: {severity * 100:.1f}% increase at index {changepoint_idx}"
                    )

                    return {
                        "degradation_detected": True,
                        "changepoint_index": int(changepoint_idx),
                        "severity": float(severity),
                        "latency_before": float(before),
                        "latency_after": float(after),
                        "should_scale": severity > 0.3,
                    }

            return {"degradation_detected": False}

        except Exception as e:
            logger.error(f"Error in degradation detection: {e}")
            return {"degradation_detected": False, "error": str(e)}
