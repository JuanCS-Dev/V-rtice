"""In-Memory APV Queue - Fallback for Kafka unavailability.

Provides graceful degradation when Kafka is unavailable.
Uses circular buffer (deque) with configurable maxlen.

Air Gap Fix: AG-RUNTIME-001 (Oráculo Kafka Hard Dependency)
Priority: CRITICAL
"""

from collections import deque
from typing import Dict, Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InMemoryAPVQueue:
    """
    In-memory circular queue for APVs when Kafka is unavailable.

    Features:
    - Circular buffer (drops oldest when full)
    - Thread-safe (deque operations are atomic)
    - Statistics tracking
    - Flush-to-Kafka support (for recovery)

    Use Case:
    When Kafka is unavailable, APVs are buffered in memory until:
    1. Kafka reconnects (flush to Kafka)
    2. Memory fills up (oldest APVs are dropped)
    3. Service restarts (APVs are lost)

    Trade-offs:
    - NOT persistent (lost on restart)
    - Limited capacity (maxlen)
    - Single-node only (no distribution)

    Alternative to:
    - Service crash (original behavior)
    - APV loss without buffering
    """

    def __init__(self, maxlen: int = 1000):
        """
        Initialize in-memory APV queue.

        Args:
            maxlen: Maximum queue size (circular buffer)
        """
        self.queue = deque(maxlen=maxlen)
        self.maxlen = maxlen
        self.total_sent = 0
        self.total_dropped = 0
        self.start_time = datetime.utcnow()

        logger.warning(
            f"⚠️  InMemoryAPVQueue initialized - DEGRADED MODE\n"
            f"   Reason: Kafka unavailable\n"
            f"   Max capacity: {maxlen} APVs\n"
            f"   Behavior: Circular buffer (oldest dropped when full)"
        )

    def send(self, apv: Dict[str, Any]) -> bool:
        """
        Add APV to in-memory queue.

        Args:
            apv: APV (Adaptive Prediction Value) dictionary

        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Check if queue is full (will drop oldest)
            was_full = len(self.queue) >= self.maxlen

            self.queue.append(apv)
            self.total_sent += 1

            if was_full:
                self.total_dropped += 1
                logger.debug(
                    f"Memory queue full - dropped oldest APV "
                    f"(total dropped: {self.total_dropped})"
                )

            if self.total_sent % 100 == 0:
                logger.info(
                    f"Memory queue stats: {len(self.queue)}/{self.maxlen} APVs | "
                    f"Sent: {self.total_sent} | Dropped: {self.total_dropped}"
                )

            return True

        except Exception as e:
            logger.error(f"Failed to add APV to memory queue: {e}")
            return False

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all APVs from queue (for flushing to Kafka).

        Returns:
            List of APV dictionaries
        """
        return list(self.queue)

    def clear(self):
        """Clear the queue (after successful flush to Kafka)."""
        size = len(self.queue)
        self.queue.clear()
        logger.info(f"Memory queue cleared ({size} APVs flushed)")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Statistics dictionary
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "mode": "in_memory_degraded",
            "current_size": len(self.queue),
            "max_capacity": self.maxlen,
            "utilization_percent": (len(self.queue) / self.maxlen) * 100,
            "total_sent": self.total_sent,
            "total_dropped": self.total_dropped,
            "uptime_seconds": uptime,
            "throughput_per_second": self.total_sent / uptime if uptime > 0 else 0
        }

    def is_full(self) -> bool:
        """Check if queue is at capacity."""
        return len(self.queue) >= self.maxlen

    def size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
