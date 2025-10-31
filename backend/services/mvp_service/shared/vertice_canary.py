"""
Vértice Canary Deployment System

Progressive traffic shifting for safe deployments:
- Blue/Green deployments
- Canary releases (5% → 25% → 50% → 100%)
- Automatic rollback on errors
- Health-based promotion

Author: Vértice Team
Glory to YHWH! 🙏
"""

import logging
import random
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentStage(Enum):
    """Canary deployment stages"""

    BLUE = "blue"  # Current stable version
    GREEN = "green"  # New version (0% traffic)
    CANARY_5 = "canary_5"  # 5% traffic
    CANARY_25 = "canary_25"  # 25% traffic
    CANARY_50 = "canary_50"  # 50% traffic
    CANARY_100 = "canary_100"  # 100% traffic (promoted)
    ROLLBACK = "rollback"  # Rolled back to blue


@dataclass
class ServiceVersion:
    """Service version information"""

    service_name: str
    version: str
    endpoint: str
    health_endpoint: str
    deployed_at: float
    error_rate: float = 0.0
    request_count: int = 0
    avg_latency_ms: float = 0.0


class CanaryDeploymentManager:
    """
    Manages canary deployments with progressive traffic shifting.

    Usage:
        manager = CanaryDeploymentManager()
        manager.register_blue("my-service", "v1.0", "http://service-v1:8000")
        manager.register_green("my-service", "v2.0", "http://service-v2:8000")

        # Start canary with 5% traffic
        manager.start_canary("my-service")

        # Gradually promote if healthy
        manager.promote_canary("my-service")  # 5% → 25%
        manager.promote_canary("my-service")  # 25% → 50%
        manager.promote_canary("my-service")  # 50% → 100%
    """

    def __init__(self):
        # service_name → {"blue": ServiceVersion, "green": ServiceVersion, "stage": DeploymentStage}
        self._deployments: dict[str, dict] = {}

        # Canary configuration
        self.canary_stages = [
            (DeploymentStage.CANARY_5, 0.05),
            (DeploymentStage.CANARY_25, 0.25),
            (DeploymentStage.CANARY_50, 0.50),
            (DeploymentStage.CANARY_100, 1.00),
        ]

        # Health thresholds
        self.max_error_rate = 0.05  # 5% max error rate
        self.max_latency_increase = 1.5  # 50% max latency increase
        self.min_requests_before_promote = 100  # Minimum requests before promotion

    def register_blue(
        self,
        service_name: str,
        version: str,
        endpoint: str,
        health_endpoint: str = "/health",
    ):
        """Register blue (stable) version"""
        if service_name not in self._deployments:
            self._deployments[service_name] = {"stage": DeploymentStage.BLUE}

        self._deployments[service_name]["blue"] = ServiceVersion(
            service_name=service_name,
            version=version,
            endpoint=endpoint,
            health_endpoint=health_endpoint,
            deployed_at=time.time(),
        )

        logger.info(f"✅ Registered BLUE: {service_name} v{version} at {endpoint}")

    def register_green(
        self,
        service_name: str,
        version: str,
        endpoint: str,
        health_endpoint: str = "/health",
    ):
        """Register green (new) version"""
        if service_name not in self._deployments:
            raise ValueError(f"Must register blue version first for {service_name}")

        self._deployments[service_name]["green"] = ServiceVersion(
            service_name=service_name,
            version=version,
            endpoint=endpoint,
            health_endpoint=health_endpoint,
            deployed_at=time.time(),
        )

        self._deployments[service_name]["stage"] = DeploymentStage.GREEN

        logger.info(f"✅ Registered GREEN: {service_name} v{version} at {endpoint}")

    def start_canary(self, service_name: str) -> bool:
        """Start canary deployment (5% traffic to green)"""
        if service_name not in self._deployments:
            raise ValueError(f"Service {service_name} not registered")

        deployment = self._deployments[service_name]

        if "green" not in deployment:
            raise ValueError(f"No green version registered for {service_name}")

        if deployment["stage"] != DeploymentStage.GREEN:
            logger.warning(
                f"Cannot start canary - current stage: {deployment['stage']}"
            )
            return False

        deployment["stage"] = DeploymentStage.CANARY_5

        logger.info(
            f"🚀 Started CANARY (5%): {service_name} v{deployment['green'].version}"
        )
        return True

    def promote_canary(self, service_name: str) -> bool:
        """
        Promote canary to next stage if healthy.
        Returns True if promoted, False if health check failed.
        """
        if service_name not in self._deployments:
            raise ValueError(f"Service {service_name} not registered")

        deployment = self._deployments[service_name]
        current_stage = deployment["stage"]

        # Check if we can promote
        if current_stage == DeploymentStage.BLUE:
            logger.warning(f"No canary in progress for {service_name}")
            return False

        if current_stage == DeploymentStage.GREEN:
            logger.warning(f"Must call start_canary() first for {service_name}")
            return False

        if current_stage == DeploymentStage.CANARY_100:
            logger.info(f"Already at 100% for {service_name}")
            return True

        # Health check
        if not self._is_green_healthy(service_name):
            logger.error(
                f"❌ Green version unhealthy - initiating rollback for {service_name}"
            )
            self.rollback(service_name)
            return False

        # Find next stage
        current_index = None
        for i, (stage, _) in enumerate(self.canary_stages):
            if stage == current_stage:
                current_index = i
                break

        if current_index is None or current_index >= len(self.canary_stages) - 1:
            logger.warning(f"Cannot promote further for {service_name}")
            return False

        next_stage, next_traffic = self.canary_stages[current_index + 1]
        deployment["stage"] = next_stage

        logger.info(
            f"📈 Promoted CANARY: {service_name} → {int(next_traffic * 100)}% traffic"
        )

        # If reached 100%, swap blue and green
        if next_stage == DeploymentStage.CANARY_100:
            self._finalize_deployment(service_name)

        return True

    def rollback(self, service_name: str):
        """Rollback to blue version (0% traffic to green)"""
        if service_name not in self._deployments:
            raise ValueError(f"Service {service_name} not registered")

        deployment = self._deployments[service_name]
        deployment["stage"] = DeploymentStage.ROLLBACK

        logger.warning(f"⏪ ROLLBACK: {service_name} → 100% blue traffic")

        # Optionally remove green
        if "green" in deployment:
            green_version = deployment["green"].version
            logger.info(
                f"Keeping green v{green_version} registered but not routing traffic"
            )

    def get_endpoint(self, service_name: str) -> str:
        """
        Get endpoint based on current canary stage.
        Uses probabilistic routing for canary stages.
        """
        if service_name not in self._deployments:
            raise ValueError(f"Service {service_name} not registered")

        deployment = self._deployments[service_name]
        stage = deployment["stage"]

        # If blue or rollback, always return blue
        if stage in (DeploymentStage.BLUE, DeploymentStage.ROLLBACK):
            return deployment["blue"].endpoint

        # If green (before canary), return blue
        if stage == DeploymentStage.GREEN:
            return deployment["blue"].endpoint

        # Canary stages - probabilistic routing
        traffic_percentage = self._get_green_traffic_percentage(stage)

        if random.random() < traffic_percentage:
            # Route to green
            deployment["green"].request_count += 1
            return deployment["green"].endpoint
        else:
            # Route to blue
            deployment["blue"].request_count += 1
            return deployment["blue"].endpoint

    def get_version_info(self, service_name: str) -> dict:
        """Get deployment information"""
        if service_name not in self._deployments:
            raise ValueError(f"Service {service_name} not registered")

        deployment = self._deployments[service_name]
        stage = deployment["stage"]

        info = {
            "service_name": service_name,
            "stage": stage.value,
            "traffic_split": self._get_traffic_split(service_name),
        }

        if "blue" in deployment:
            blue = deployment["blue"]
            info["blue"] = {
                "version": blue.version,
                "endpoint": blue.endpoint,
                "request_count": blue.request_count,
                "error_rate": blue.error_rate,
                "avg_latency_ms": blue.avg_latency_ms,
            }

        if "green" in deployment:
            green = deployment["green"]
            info["green"] = {
                "version": green.version,
                "endpoint": green.endpoint,
                "request_count": green.request_count,
                "error_rate": green.error_rate,
                "avg_latency_ms": green.avg_latency_ms,
            }

        return info

    def update_metrics(
        self, service_name: str, version: str, latency_ms: float, is_error: bool
    ):
        """Update metrics for a version (called after each request)"""
        if service_name not in self._deployments:
            return

        deployment = self._deployments[service_name]

        # Find which version to update
        target = None
        if "blue" in deployment and deployment["blue"].version == version:
            target = deployment["blue"]
        elif "green" in deployment and deployment["green"].version == version:
            target = deployment["green"]

        if target is None:
            return

        # Update metrics (rolling average)
        target.request_count += 1

        # Update error rate (exponential moving average)
        alpha = 0.1
        if is_error:
            target.error_rate = alpha * 1.0 + (1 - alpha) * target.error_rate
        else:
            target.error_rate = (1 - alpha) * target.error_rate

        # Update latency (exponential moving average)
        target.avg_latency_ms = alpha * latency_ms + (1 - alpha) * target.avg_latency_ms

    def _is_green_healthy(self, service_name: str) -> bool:
        """Check if green version is healthy enough to promote"""
        deployment = self._deployments[service_name]

        if "green" not in deployment or "blue" not in deployment:
            return False

        green = deployment["green"]
        blue = deployment["blue"]

        # Must have minimum requests
        if green.request_count < self.min_requests_before_promote:
            logger.info(
                f"Green has only {green.request_count} requests (need {self.min_requests_before_promote})"
            )
            return False

        # Check error rate
        if green.error_rate > self.max_error_rate:
            logger.error(
                f"Green error rate too high: {green.error_rate:.2%} > {self.max_error_rate:.2%}"
            )
            return False

        # Check latency increase
        if blue.avg_latency_ms > 0:
            latency_ratio = green.avg_latency_ms / blue.avg_latency_ms
            if latency_ratio > self.max_latency_increase:
                logger.error(
                    f"Green latency too high: {latency_ratio:.2f}x blue latency"
                )
                return False

        logger.info(
            f"✅ Green version healthy: error_rate={green.error_rate:.2%}, latency={green.avg_latency_ms:.1f}ms"
        )
        return True

    def _get_green_traffic_percentage(self, stage: DeploymentStage) -> float:
        """Get traffic percentage for green based on stage"""
        for s, percentage in self.canary_stages:
            if s == stage:
                return percentage
        return 0.0

    def _get_traffic_split(self, service_name: str) -> dict[str, float]:
        """Get current traffic split"""
        deployment = self._deployments[service_name]
        stage = deployment["stage"]

        if stage in (DeploymentStage.BLUE, DeploymentStage.ROLLBACK):
            return {"blue": 1.0, "green": 0.0}

        if stage == DeploymentStage.GREEN:
            return {"blue": 1.0, "green": 0.0}

        green_pct = self._get_green_traffic_percentage(stage)
        return {"blue": 1.0 - green_pct, "green": green_pct}

    def _finalize_deployment(self, service_name: str):
        """Finalize deployment by swapping blue and green"""
        deployment = self._deployments[service_name]

        old_blue = deployment.get("blue")
        new_blue = deployment["green"]

        # Swap
        deployment["blue"] = new_blue
        deployment["stage"] = DeploymentStage.BLUE

        # Remove green
        if "green" in deployment:
            del deployment["green"]

        logger.info(
            f"🎉 Deployment FINALIZED: {service_name} v{new_blue.version} is now stable (blue)"
        )

        if old_blue:
            logger.info(f"Previous version v{old_blue.version} can be decommissioned")


# Singleton instance
_canary_manager: CanaryDeploymentManager | None = None


def get_canary_manager() -> CanaryDeploymentManager:
    """Get global canary manager instance"""
    global _canary_manager
    if _canary_manager is None:
        _canary_manager = CanaryDeploymentManager()
    return _canary_manager
