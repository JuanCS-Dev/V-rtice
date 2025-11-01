"""Dynamic Browser Pool - Auto-scaling Browser Instance Management.

Removes hardcoded max_instances=5 limit and implements auto-scaling
based on CPU metrics and demand.

Biblical Foundation:
- Proverbs 21:5: "The plans of the diligent lead surely to abundance"

Features:
- Auto-scaling based on CPU metrics
- Min/max instance limits
- Scale up threshold: 80% CPU
- Scale down threshold: 30% CPU
- Least-loaded instance selection
- Graceful shutdown of idle instances

Author: Vértice Platform Team
Created: 2025-11-01
"""

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)


@dataclass
class BrowserInstance:
    """Represents a browser instance with metrics."""

    instance_id: str
    created_at: datetime
    session_count: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    is_healthy: bool = True

    async def shutdown(self):
        """Shutdown browser instance."""
        logger.info(f"Shutting down browser instance: {self.instance_id}")
        # Implementation would close actual browser
        pass


# Prometheus metrics
browser_pool_size = Gauge(
    "maba_browser_pool_size", "Current number of browser instances"
)

browser_pool_sessions = Gauge(
    "maba_browser_pool_sessions", "Total active browser sessions"
)

browser_pool_scale_events = Counter(
    "maba_browser_pool_scale_events_total",
    "Browser pool scaling events",
    ["direction"],  # up/down
)

browser_instance_cpu = Gauge(
    "maba_browser_instance_cpu_percent",
    "Browser instance CPU usage",
    ["instance_id"],
)


class DynamicBrowserPool:
    """Auto-scaling browser instance pool.

    Scales up/down based on CPU metrics and demand, respects resource limits.

    Biblical Principle: Proverbs 21:5 - "The plans of the diligent lead surely to abundance"
    """

    def __init__(
        self,
        min_instances: int = 2,
        max_instances: int = 20,
        target_cpu_percent: float = 70.0,
        scale_up_threshold: float = 80.0,
        scale_down_threshold: float = 30.0,
        scale_check_interval: int = 30,
    ):
        """Initialize dynamic browser pool.

        Args:
            min_instances: Minimum browser instances to maintain
            max_instances: Maximum browser instances allowed
            target_cpu_percent: Target CPU utilization
            scale_up_threshold: CPU % to trigger scale up
            scale_down_threshold: CPU % to trigger scale down
            scale_check_interval: Seconds between scaling checks

        """
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.target_cpu = target_cpu_percent
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.scale_check_interval = scale_check_interval

        self.instances: list[BrowserInstance] = []
        self._scaling_lock = asyncio.Lock()
        self._initialized = False
        self._scaling_task: asyncio.Task | None = None

        logger.info(
            f"Dynamic browser pool initialized (min={min_instances}, max={max_instances})"
        )

    async def initialize(self) -> bool:
        """Initialize pool with minimum instances."""
        if self._initialized:
            return True

        try:
            # Bootstrap with minimum instances
            await self._scale_up(self.min_instances)

            # Start background scaling task
            self._scaling_task = asyncio.create_task(self._scaling_loop())

            self._initialized = True
            logger.info(
                f"✅ Browser pool initialized with {self.min_instances} instances"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize browser pool: {e}")
            return False

    async def _scaling_loop(self):
        """Background task to monitor and scale pool."""
        while True:
            try:
                await asyncio.sleep(self.scale_check_interval)
                await self._check_and_scale()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scaling loop: {e}")

    async def get_instance(self) -> BrowserInstance:
        """Get available browser instance (auto-scale if needed).

        Returns least-loaded instance based on session count.

        Returns:
            BrowserInstance with lowest session count

        """
        # Check if scaling needed
        await self._check_and_scale()

        # Find least loaded instance
        if not self.instances:
            raise RuntimeError("No browser instances available")

        instance = min(self.instances, key=lambda i: i.session_count)

        logger.debug(
            f"Assigned instance {instance.instance_id} (sessions: {instance.session_count})"
        )
        return instance

    async def _check_and_scale(self) -> None:
        """Check metrics and scale pool if needed."""
        async with self._scaling_lock:
            if len(self.instances) == 0:
                # Bootstrap
                await self._scale_up(self.min_instances)
                return

            # Calculate aggregate metrics
            total_cpu = sum(i.cpu_usage for i in self.instances)
            avg_cpu = total_cpu / len(self.instances)

            total_sessions = sum(i.session_count for i in self.instances)
            avg_sessions = total_sessions / len(self.instances)

            # Update Prometheus metrics
            browser_pool_size.set(len(self.instances))
            browser_pool_sessions.set(total_sessions)

            # Scale up if CPU high or sessions high
            if (avg_cpu > self.scale_up_threshold or avg_sessions > 3) and len(
                self.instances
            ) < self.max_instances:
                await self._scale_up(1)
                logger.info(
                    f"⬆️  Scaled up browser pool (CPU: {avg_cpu:.1f}%, Sessions: {avg_sessions:.1f})"
                )

            # Scale down if CPU low and sessions low
            elif (avg_cpu < self.scale_down_threshold and avg_sessions < 1) and len(
                self.instances
            ) > self.min_instances:
                await self._scale_down(1)
                logger.info(
                    f"⬇️  Scaled down browser pool (CPU: {avg_cpu:.1f}%, Sessions: {avg_sessions:.1f})"
                )

    async def _scale_up(self, count: int) -> None:
        """Add browser instances.

        Args:
            count: Number of instances to add

        """
        for _ in range(count):
            instance_id = f"browser-{len(self.instances) + 1}"
            instance = BrowserInstance(
                instance_id=instance_id, created_at=datetime.utcnow()
            )

            self.instances.append(instance)

            logger.info(f"➕ Added browser instance: {instance_id}")
            browser_pool_scale_events.labels(direction="up").inc()

    async def _scale_down(self, count: int) -> None:
        """Remove browser instances.

        Args:
            count: Number of instances to remove

        """
        # Sort by session count (ascending) - remove least utilized
        sorted_instances = sorted(self.instances, key=lambda i: i.session_count)

        removed = 0
        for instance in sorted_instances:
            if removed >= count:
                break

            # Only remove instances with no active sessions
            if instance.session_count == 0:
                await instance.shutdown()
                self.instances.remove(instance)

                logger.info(f"➖ Removed browser instance: {instance.instance_id}")
                browser_pool_scale_events.labels(direction="down").inc()
                removed += 1

        if removed < count:
            logger.warning(
                f"Could only remove {removed}/{count} instances (others have active sessions)"
            )

    async def update_instance_metrics(
        self, instance_id: str, cpu: float, memory: float
    ) -> None:
        """Update metrics for a browser instance.

        Args:
            instance_id: Instance identifier
            cpu: CPU usage percentage (0-100)
            memory: Memory usage in MB

        """
        for instance in self.instances:
            if instance.instance_id == instance_id:
                instance.cpu_usage = cpu
                instance.memory_usage = memory

                # Update Prometheus
                browser_instance_cpu.labels(instance_id=instance_id).set(cpu)

                logger.debug(
                    f"Updated metrics for {instance_id}: CPU={cpu:.1f}%, Mem={memory:.0f}MB"
                )
                break

    async def increment_session_count(self, instance_id: str) -> None:
        """Increment session count for instance."""
        for instance in self.instances:
            if instance.instance_id == instance_id:
                instance.session_count += 1
                break

    async def decrement_session_count(self, instance_id: str) -> None:
        """Decrement session count for instance."""
        for instance in self.instances:
            if instance.instance_id == instance_id:
                instance.session_count = max(0, instance.session_count - 1)
                break

    async def get_stats(self) -> dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool metrics

        """
        total_cpu = sum(i.cpu_usage for i in self.instances)
        total_sessions = sum(i.session_count for i in self.instances)

        return {
            "instances": len(self.instances),
            "min_instances": self.min_instances,
            "max_instances": self.max_instances,
            "total_sessions": total_sessions,
            "avg_cpu": total_cpu / len(self.instances) if self.instances else 0,
            "instances_detail": [
                {
                    "instance_id": i.instance_id,
                    "sessions": i.session_count,
                    "cpu": i.cpu_usage,
                    "memory_mb": i.memory_usage,
                    "healthy": i.is_healthy,
                }
                for i in self.instances
            ],
        }

    async def shutdown(self) -> None:
        """Shutdown pool and all instances."""
        logger.info("Shutting down browser pool...")

        # Cancel scaling task
        if self._scaling_task:
            self._scaling_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._scaling_task

        # Shutdown all instances
        for instance in self.instances:
            await instance.shutdown()

        self.instances.clear()
        logger.info("✅ Browser pool shutdown complete")
