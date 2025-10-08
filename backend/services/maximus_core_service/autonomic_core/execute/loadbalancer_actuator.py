"""Load Balancer Actuator - Traffic Shift and Circuit Breaker"""

import logging
import time
from collections import deque
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker for service health monitoring."""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60,
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

        self.failure_count = 0
        self.success_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = None

    def record_success(self):
        """Record successful request."""
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.success_count = 0
                logger.info("Circuit breaker: HALF_OPEN -> CLOSED")

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker: CLOSED -> OPEN (failures: {self.failure_count})")

        elif self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.success_count = 0
            logger.warning("Circuit breaker: HALF_OPEN -> OPEN")

    def can_attempt(self) -> bool:
        """Check if request can be attempted."""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if timeout expired
            if self.last_failure_time and time.time() - self.last_failure_time >= self.timeout_seconds:
                self.state = "HALF_OPEN"
                self.success_count = 0
                logger.info("Circuit breaker: OPEN -> HALF_OPEN (timeout expired)")
                return True
            return False

        # HALF_OPEN state
        return True

    def get_state(self) -> str:
        """Get current circuit breaker state."""
        return self.state


class LoadBalancerActuator:
    """Manage traffic distribution and circuit breaker."""

    def __init__(
        self,
        lb_api_url: str = "http://localhost:8080/api/lb",
        dry_run_mode: bool = True,
    ):
        self.lb_api_url = lb_api_url
        self.dry_run_mode = dry_run_mode
        self.action_log = []
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.traffic_history = deque(maxlen=1000)

    def get_circuit_breaker(self, service: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = CircuitBreaker()
        return self.circuit_breakers[service]

    async def shift_traffic(self, service: str, target_version: str, weight_percent: int) -> dict:
        """Shift traffic between service versions (canary/blue-green).

        Args:
            service: Service name
            target_version: Target version (e.g., 'v2', 'canary')
            weight_percent: Traffic weight 0-100
        """
        if self.dry_run_mode:
            logger.info(f"DRY-RUN: Shift {weight_percent}% traffic to {service}:{target_version}")
            self.action_log.append(
                {
                    "action": "shift_traffic",
                    "service": service,
                    "target_version": target_version,
                    "weight_percent": weight_percent,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.lb_api_url}/traffic-shift",
                    json={
                        "service": service,
                        "target_version": target_version,
                        "weight": weight_percent,
                    },
                    timeout=10.0,
                )

                success = response.status_code == 200

                self.action_log.append(
                    {
                        "action": "shift_traffic",
                        "service": service,
                        "target_version": target_version,
                        "weight_percent": weight_percent,
                        "executed": True,
                        "success": success,
                    }
                )

                if success:
                    logger.info(f"Traffic shifted: {service}:{target_version} -> {weight_percent}%")
                    return {
                        "success": True,
                        "service": service,
                        "target_version": target_version,
                        "weight_percent": weight_percent,
                    }
                logger.error(f"Traffic shift failed: {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Traffic shift error: {e}")
            return {"success": False, "error": str(e)}

    async def enable_circuit_breaker(self, service: str, enabled: bool = True) -> dict:
        """Enable/disable circuit breaker for service.

        Args:
            service: Service name
            enabled: True to enable, False to disable
        """
        if self.dry_run_mode:
            action = "Enable" if enabled else "Disable"
            logger.info(f"DRY-RUN: {action} circuit breaker for {service}")
            self.action_log.append(
                {
                    "action": "circuit_breaker",
                    "service": service,
                    "enabled": enabled,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            cb = self.get_circuit_breaker(service)

            if not enabled:
                # Reset circuit breaker
                cb.state = "CLOSED"
                cb.failure_count = 0
                cb.success_count = 0
                logger.info(f"Circuit breaker disabled (reset) for {service}")

            self.action_log.append(
                {
                    "action": "circuit_breaker",
                    "service": service,
                    "enabled": enabled,
                    "executed": True,
                    "success": True,
                }
            )

            return {
                "success": True,
                "service": service,
                "circuit_breaker_enabled": enabled,
                "state": cb.get_state(),
            }

        except Exception as e:
            logger.error(f"Circuit breaker toggle error: {e}")
            return {"success": False, "error": str(e)}

    async def adjust_rate_limit(self, service: str, requests_per_second: int) -> dict:
        """Adjust rate limiting for service.

        Args:
            service: Service name
            requests_per_second: Max requests per second (1-10000)
        """
        if self.dry_run_mode:
            logger.info(f"DRY-RUN: Set rate limit {service} -> {requests_per_second} req/s")
            self.action_log.append(
                {
                    "action": "rate_limit",
                    "service": service,
                    "requests_per_second": requests_per_second,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.lb_api_url}/rate-limit",
                    json={"service": service, "rate": requests_per_second},
                    timeout=10.0,
                )

                success = response.status_code == 200

                self.action_log.append(
                    {
                        "action": "rate_limit",
                        "service": service,
                        "requests_per_second": requests_per_second,
                        "executed": True,
                        "success": success,
                    }
                )

                if success:
                    logger.info(f"Rate limit set: {service} -> {requests_per_second} req/s")
                    return {
                        "success": True,
                        "service": service,
                        "requests_per_second": requests_per_second,
                    }
                return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Rate limit adjustment error: {e}")
            return {"success": False, "error": str(e)}

    async def get_traffic_stats(self, service: str) -> dict:
        """Get traffic statistics for service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.lb_api_url}/stats/{service}", timeout=5.0)

                if response.status_code == 200:
                    data = response.json()

                    # Add circuit breaker state
                    cb = self.get_circuit_breaker(service)

                    return {
                        "success": True,
                        "service": service,
                        "requests_per_second": data.get("rps", 0),
                        "error_rate_percent": data.get("error_rate", 0),
                        "latency_p50_ms": data.get("p50_latency", 0),
                        "latency_p99_ms": data.get("p99_latency", 0),
                        "active_connections": data.get("active_connections", 0),
                        "circuit_breaker": {
                            "state": cb.get_state(),
                            "failure_count": cb.failure_count,
                            "success_count": cb.success_count,
                        },
                    }
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Traffic stats retrieval error: {e}")
            return {"success": False, "error": str(e)}

    async def canary_rollout(
        self,
        service: str,
        canary_version: str,
        initial_weight: int = 5,
        increment: int = 10,
        wait_seconds: int = 300,
    ) -> dict:
        """Gradual canary rollout with automatic rollback on errors.

        Args:
            service: Service name
            canary_version: Canary version identifier
            initial_weight: Initial traffic % (default 5%)
            increment: Traffic increment per step (default 10%)
            wait_seconds: Wait time between increments (default 5min)
        """
        if self.dry_run_mode:
            logger.info(
                f"DRY-RUN: Canary rollout {service}:{canary_version} (start={initial_weight}%, step={increment}%)"
            )
            return {"success": True, "dry_run": True}

        try:
            current_weight = initial_weight
            rollout_log = []

            while current_weight <= 100:
                # Shift traffic
                shift_result = await self.shift_traffic(service, canary_version, current_weight)

                if not shift_result["success"]:
                    logger.error(f"Canary rollout failed at {current_weight}%")
                    # Rollback to 0%
                    await self.shift_traffic(service, canary_version, 0)
                    return {
                        "success": False,
                        "error": "Traffic shift failed",
                        "rollback": True,
                        "failed_at_percent": current_weight,
                    }

                rollout_log.append(
                    {
                        "weight_percent": current_weight,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                logger.info(f"Canary rollout: {service}:{canary_version} @ {current_weight}%")

                # Wait before next increment (except last step)
                if current_weight < 100:
                    await asyncio.sleep(wait_seconds)

                    # Check circuit breaker state
                    cb = self.get_circuit_breaker(service)
                    if cb.get_state() == "OPEN":
                        logger.error("Circuit breaker OPEN, rolling back canary")
                        await self.shift_traffic(service, canary_version, 0)
                        return {
                            "success": False,
                            "error": "Circuit breaker triggered",
                            "rollback": True,
                            "failed_at_percent": current_weight,
                        }

                current_weight += increment
                current_weight = min(current_weight, 100)  # Cap at 100%

            logger.info(f"Canary rollout completed: {service}:{canary_version} @ 100%")

            return {
                "success": True,
                "service": service,
                "canary_version": canary_version,
                "final_weight_percent": 100,
                "rollout_log": rollout_log,
            }

        except Exception as e:
            logger.error(f"Canary rollout error: {e}")
            # Attempt rollback
            await self.shift_traffic(service, canary_version, 0)
            return {"success": False, "error": str(e), "rollback": True}

    def get_action_log(self) -> list[dict]:
        """Return action history for audit."""
        return self.action_log


# Import asyncio for canary rollout sleep
import asyncio
