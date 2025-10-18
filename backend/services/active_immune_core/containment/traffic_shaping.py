"""Traffic Shaping - Adaptive Rate Limiting & QoS Control

Implements intelligent traffic control inspired by biological
membrane transport mechanisms (selective permeability).

Key Features:
- Adaptive rate limiting (token bucket algorithm)
- QoS prioritization (bandwidth allocation)
- Traffic classification
- DDoS mitigation

Biological Inspiration:
- Cell membrane transport → Traffic control
- Ion channels (selective) → QoS priorities
- Osmotic pressure regulation → Rate limiting

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância vence!
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class TrafficPriority(Enum):
    """Traffic priority levels (QoS)"""

    CRITICAL = 0  # Management, emergency
    HIGH = 1  # Production traffic
    MEDIUM = 2  # Normal business
    LOW = 3  # Bulk transfers
    BACKGROUND = 4  # Backups, updates


class RateLimitAction(Enum):
    """Actions when rate limit exceeded"""

    DROP = "drop"  # Drop packets
    DELAY = "delay"  # Queue with delay
    MARK = "mark"  # Mark for later processing
    LOG = "log"  # Log only


@dataclass
class TrafficProfile:
    """Traffic classification profile"""

    name: str
    priority: TrafficPriority
    max_rate_mbps: float  # Maximum bandwidth in Mbps
    burst_size_mb: float  # Burst allowance in MB
    ports: List[int] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    source_cidrs: List[str] = field(default_factory=list)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    rate_per_second: int  # Requests per second
    burst_size: int  # Burst allowance
    window_seconds: int = 1  # Time window
    action: RateLimitAction = RateLimitAction.DROP


@dataclass
class TrafficShapingResult:
    """Result of traffic shaping operation"""

    status: str  # SUCCESS, PARTIAL, FAILED
    profiles_applied: List[str] = field(default_factory=list)
    rate_limits_set: int = 0
    qos_policies_created: int = 0
    bandwidth_allocated_mbps: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)


class TrafficShapingMetrics:
    """Prometheus metrics for traffic shaping"""

    def __init__(self):
        self.shaping_operations_total = Counter(
            "traffic_shaping_operations_total",
            "Total traffic shaping operations",
            ["status"],
        )
        self.active_rate_limits = Gauge(
            "traffic_rate_limits_active", "Active rate limiters"
        )
        self.packets_shaped_total = Counter(
            "traffic_packets_shaped_total",
            "Total packets shaped",
            ["action"],
        )
        self.bandwidth_allocated = Gauge(
            "traffic_bandwidth_allocated_mbps",
            "Total bandwidth allocated in Mbps",
        )


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.

    Allows burst traffic while maintaining average rate.
    Biological analogy: Neurotransmitter vesicle release.
    """

    def __init__(self, rate: int, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum tokens (burst size)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.time()
        logger.debug(f"TokenBucket initialized: rate={rate}, capacity={capacity}")

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens available, False if rate limited
        """
        # Refill tokens based on time passed
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

        # Check if enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_available_tokens(self) -> float:
        """Get current available tokens"""
        now = time.time()
        elapsed = now - self.last_update
        return min(self.capacity, self.tokens + elapsed * self.rate)

    def reset(self):
        """Reset bucket to full capacity"""
        self.tokens = float(self.capacity)
        self.last_update = time.time()


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with dynamic adjustment.

    Adjusts limits based on threat level and system load.
    """

    def __init__(self, config: RateLimitConfig):
        """
        Initialize adaptive rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.bucket = TokenBucket(config.rate_per_second, config.burst_size)
        self.total_requests = 0
        self.blocked_requests = 0
        self.created_at = datetime.utcnow()

        logger.info(
            f"AdaptiveRateLimiter initialized: "
            f"rate={config.rate_per_second}/s, burst={config.burst_size}"
        )

    async def check_limit(self, request_cost: int = 1) -> bool:
        """
        Check if request is within rate limit.

        Args:
            request_cost: Cost in tokens (default 1)

        Returns:
            True if allowed, False if rate limited
        """
        self.total_requests += 1

        if self.bucket.consume(request_cost):
            return True

        self.blocked_requests += 1
        logger.debug(
            f"Rate limit exceeded: {self.blocked_requests}/{self.total_requests} blocked"
        )
        return False

    async def adapt_limit(self, new_rate: int, new_burst: int):
        """
        Adapt rate limit dynamically.

        Args:
            new_rate: New rate per second
            new_burst: New burst size
        """
        logger.info(f"Adapting rate limit: {self.config.rate_per_second} → {new_rate}")
        self.config.rate_per_second = new_rate
        self.config.burst_size = new_burst
        self.bucket = TokenBucket(new_rate, new_burst)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": (
                self.blocked_requests / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
            "available_tokens": self.bucket.get_available_tokens(),
            "config": {
                "rate": self.config.rate_per_second,
                "burst": self.config.burst_size,
            },
        }


class QoSController:
    """
    Quality of Service controller.

    Manages bandwidth allocation and traffic prioritization.
    Biological analogy: Ion channel selectivity.
    """

    def __init__(self, total_bandwidth_mbps: float = 1000.0):
        """
        Initialize QoS controller.

        Args:
            total_bandwidth_mbps: Total available bandwidth in Mbps
        """
        self.total_bandwidth = total_bandwidth_mbps
        self.allocated_bandwidth: Dict[str, float] = {}
        self.traffic_profiles: Dict[str, TrafficProfile] = {}

        logger.info(f"QoSController initialized: {total_bandwidth_mbps} Mbps available")

    async def create_profile(self, profile: TrafficProfile) -> bool:
        """
        Create traffic profile with QoS.

        Args:
            profile: Traffic profile configuration

        Returns:
            True if created successfully
        """
        # Check bandwidth availability
        used_bandwidth = sum(self.allocated_bandwidth.values())
        available = self.total_bandwidth - used_bandwidth

        if profile.max_rate_mbps > available:
            logger.warning(
                f"Insufficient bandwidth for profile {profile.name}: "
                f"requested={profile.max_rate_mbps}, available={available}"
            )
            return False

        # Integrate with tc (traffic control) for real QoS
        try:
            import subprocess
            
            interface = os.getenv("NETWORK_INTERFACE", "eth0")
            
            # Create HTB qdisc if not exists
            subprocess.run(
                ["tc", "qdisc", "add", "dev", interface, "root", "handle", "1:", "htb", "default", "30"],
                capture_output=True,
                timeout=5,
            )
            
            # Create class for this profile
            class_id = f"1:{profile.priority.value + 10}"
            rate = f"{profile.max_rate_mbps}mbit"
            
            subprocess.run(
                ["tc", "class", "add", "dev", interface, "parent", "1:", "classid", class_id, "htb", "rate", rate],
                capture_output=True,
                timeout=5,
            )
            
            logger.info(f"QoS profile {profile.name} configured with tc: {rate}")
            
        except Exception as e:
            logger.warning(f"tc integration failed, using logical QoS: {e}")
        
        logger.info(
            f"Creating QoS profile: {profile.name}, "
            f"priority={profile.priority.name}, "
            f"bandwidth={profile.max_rate_mbps} Mbps"
        )
        await asyncio.sleep(0.05)

        self.traffic_profiles[profile.name] = profile
        self.allocated_bandwidth[profile.name] = profile.max_rate_mbps

        return True

    async def remove_profile(self, profile_name: str) -> bool:
        """Remove traffic profile"""
        if profile_name in self.traffic_profiles:
            del self.traffic_profiles[profile_name]
            if profile_name in self.allocated_bandwidth:
                del self.allocated_bandwidth[profile_name]
            logger.info(f"Removed QoS profile: {profile_name}")
            return True
        return False

    def get_bandwidth_allocation(self) -> Dict[str, float]:
        """Get current bandwidth allocation"""
        return self.allocated_bandwidth.copy()

    def get_available_bandwidth(self) -> float:
        """Get available bandwidth"""
        used = sum(self.allocated_bandwidth.values())
        return max(0, self.total_bandwidth - used)


class AdaptiveTrafficShaper:
    """
    Complete adaptive traffic shaping system.

    Combines rate limiting and QoS for comprehensive
    traffic control. Adapts to threat conditions.

    Biological Inspiration:
    - Membrane transport selectivity
    - Osmotic pressure regulation
    - Neurotransmitter vesicle release control
    """

    def __init__(
        self,
        qos_controller: Optional[QoSController] = None,
        total_bandwidth_mbps: float = 1000.0,
    ):
        """
        Initialize adaptive traffic shaper.

        Args:
            qos_controller: QoS controller (created if None)
            total_bandwidth_mbps: Total bandwidth available
        """
        self.qos = qos_controller or QoSController(total_bandwidth_mbps)
        self.rate_limiters: Dict[str, AdaptiveRateLimiter] = {}
        self.metrics = TrafficShapingMetrics()

        logger.info("AdaptiveTrafficShaper initialized")

    async def shape_traffic(
        self,
        threat_level: str,
        policy: Dict[str, Any],
    ) -> TrafficShapingResult:
        """
        Apply traffic shaping based on threat.

        Args:
            threat_level: Threat severity level
            policy: Shaping policy configuration

        Returns:
            TrafficShapingResult with applied configurations
        """
        result = TrafficShapingResult(status="IN_PROGRESS")

        try:
            # 1. Apply rate limiting
            if "rate_limits" in policy:
                for name, config_dict in policy["rate_limits"].items():
                    config = RateLimitConfig(**config_dict)
                    limiter = AdaptiveRateLimiter(config)
                    self.rate_limiters[name] = limiter
                    result.rate_limits_set += 1

            # 2. Apply QoS profiles
            if "qos_profiles" in policy:
                for profile_dict in policy["qos_profiles"]:
                    profile = TrafficProfile(**profile_dict)
                    if await self.qos.create_profile(profile):
                        result.profiles_applied.append(profile.name)
                        result.qos_policies_created += 1
                        result.bandwidth_allocated_mbps += profile.max_rate_mbps

            # Determine status
            if result.rate_limits_set > 0 or result.qos_policies_created > 0:
                result.status = "SUCCESS"
            else:
                result.status = "FAILED"

            # Update metrics
            self.metrics.shaping_operations_total.labels(status=result.status).inc()
            self.metrics.active_rate_limits.set(len(self.rate_limiters))
            self.metrics.bandwidth_allocated.set(result.bandwidth_allocated_mbps)

            logger.info(
                f"Traffic shaping complete: "
                f"limiters={result.rate_limits_set}, "
                f"profiles={result.qos_policies_created}"
            )

            return result

        except Exception as e:
            logger.error(f"Traffic shaping failed: {e}", exc_info=True)
            return TrafficShapingResult(
                status="FAILED",
                errors=[str(e)],
            )

    async def check_rate_limit(self, limiter_name: str, cost: int = 1) -> bool:
        """
        Check rate limit for specific limiter.

        Args:
            limiter_name: Name of rate limiter
            cost: Request cost in tokens

        Returns:
            True if allowed, False if limited
        """
        if limiter_name not in self.rate_limiters:
            logger.warning(f"Rate limiter {limiter_name} not found")
            return True  # Allow if no limiter configured

        allowed = await self.rate_limiters[limiter_name].check_limit(cost)

        # Update metrics
        action = "allowed" if allowed else "blocked"
        self.metrics.packets_shaped_total.labels(action=action).inc()

        return allowed

    async def adapt_to_threat(self, threat_level: str):
        """
        Adapt traffic shaping to threat level.

        Args:
            threat_level: Current threat level (low, medium, high, critical)
        """
        logger.info(f"Adapting traffic shaping to threat level: {threat_level}")

        # Adjust rate limits based on threat
        adjustments = {
            "low": {"multiplier": 1.0},
            "medium": {"multiplier": 0.75},
            "high": {"multiplier": 0.5},
            "critical": {"multiplier": 0.25},
        }

        if threat_level not in adjustments:
            return

        multiplier = adjustments[threat_level]["multiplier"]

        # Adapt all rate limiters
        for name, limiter in self.rate_limiters.items():
            new_rate = int(limiter.config.rate_per_second * multiplier)
            new_burst = int(limiter.config.burst_size * multiplier)
            await limiter.adapt_limit(new_rate, new_burst)

    def get_rate_limiter_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all rate limiters"""
        return {name: limiter.get_stats() for name, limiter in self.rate_limiters.items()}

    def get_bandwidth_usage(self) -> Dict[str, Any]:
        """Get bandwidth usage statistics"""
        allocation = self.qos.get_bandwidth_allocation()
        available = self.qos.get_available_bandwidth()
        total = self.qos.total_bandwidth

        return {
            "total_mbps": total,
            "allocated_mbps": sum(allocation.values()),
            "available_mbps": available,
            "allocation_by_profile": allocation,
            "utilization_percent": (sum(allocation.values()) / total * 100) if total > 0 else 0,
        }

    def get_active_profiles(self) -> List[str]:
        """Get list of active traffic profiles"""
        return list(self.qos.traffic_profiles.keys())

    def has_rate_limiter(self, name: str) -> bool:
        """Check if rate limiter exists"""
        return name in self.rate_limiters
