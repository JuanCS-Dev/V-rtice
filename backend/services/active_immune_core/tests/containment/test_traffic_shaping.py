"""Tests for Traffic Shaping - Adaptive Rate Limiting & QoS

Comprehensive test suite for traffic shaping, rate limiting,
and QoS control.

Target: 90%+ coverage

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância vence!
"""

import asyncio
import pytest
import time
from prometheus_client import REGISTRY

from containment.traffic_shaping import (
    AdaptiveRateLimiter,
    AdaptiveTrafficShaper,
    QoSController,
    RateLimitAction,
    RateLimitConfig,
    TokenBucket,
    TrafficPriority,
    TrafficProfile,
    TrafficShapingMetrics,
    TrafficShapingResult,
)


@pytest.fixture(autouse=True)
def cleanup_prometheus():
    """Clean up Prometheus registry between tests"""
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    yield
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


@pytest.fixture
def token_bucket():
    """Create TokenBucket instance"""
    return TokenBucket(rate=10, capacity=20)


@pytest.fixture
def rate_limit_config():
    """Create RateLimitConfig"""
    return RateLimitConfig(
        rate_per_second=100,
        burst_size=200,
        window_seconds=1,
        action=RateLimitAction.DROP,
    )


@pytest.fixture
def adaptive_rate_limiter(rate_limit_config):
    """Create AdaptiveRateLimiter"""
    return AdaptiveRateLimiter(rate_limit_config)


@pytest.fixture
def qos_controller():
    """Create QoSController"""
    return QoSController(total_bandwidth_mbps=1000.0)


@pytest.fixture
def traffic_profile():
    """Create TrafficProfile"""
    return TrafficProfile(
        name="production",
        priority=TrafficPriority.HIGH,
        max_rate_mbps=500.0,
        burst_size_mb=100.0,
        ports=[80, 443],
        protocols=["tcp"],
    )


@pytest.fixture
def traffic_shaper():
    """Create AdaptiveTrafficShaper"""
    return AdaptiveTrafficShaper()


class TestTrafficPriority:
    """Test TrafficPriority enum"""

    def test_priority_levels_exist(self):
        """Test all priority levels are defined"""
        assert TrafficPriority.CRITICAL.value == 0
        assert TrafficPriority.HIGH.value == 1
        assert TrafficPriority.MEDIUM.value == 2
        assert TrafficPriority.LOW.value == 3
        assert TrafficPriority.BACKGROUND.value == 4

    def test_priority_comparable(self):
        """Test priorities can be compared"""
        assert TrafficPriority.CRITICAL.value < TrafficPriority.BACKGROUND.value
        assert TrafficPriority.HIGH.value < TrafficPriority.LOW.value


class TestRateLimitAction:
    """Test RateLimitAction enum"""

    def test_actions_exist(self):
        """Test all actions are defined"""
        assert RateLimitAction.DROP.value == "drop"
        assert RateLimitAction.DELAY.value == "delay"
        assert RateLimitAction.MARK.value == "mark"
        assert RateLimitAction.LOG.value == "log"


class TestTrafficProfile:
    """Test TrafficProfile dataclass"""

    def test_profile_creation(self, traffic_profile):
        """Test traffic profile creation"""
        assert traffic_profile.name == "production"
        assert traffic_profile.priority == TrafficPriority.HIGH
        assert traffic_profile.max_rate_mbps == 500.0
        assert 80 in traffic_profile.ports


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass"""

    def test_config_creation(self, rate_limit_config):
        """Test rate limit config creation"""
        assert rate_limit_config.rate_per_second == 100
        assert rate_limit_config.burst_size == 200
        assert rate_limit_config.action == RateLimitAction.DROP


class TestTokenBucket:
    """Test TokenBucket algorithm"""

    def test_initialization(self, token_bucket):
        """Test token bucket initialization"""
        assert token_bucket.rate == 10
        assert token_bucket.capacity == 20
        assert token_bucket.tokens == 20.0

    def test_consume_success(self, token_bucket):
        """Test successful token consumption"""
        result = token_bucket.consume(5)
        assert result is True
        assert token_bucket.tokens == 15.0

    def test_consume_insufficient(self, token_bucket):
        """Test consumption with insufficient tokens"""
        token_bucket.consume(20)  # Consume all
        result = token_bucket.consume(1)
        assert result is False

    def test_token_refill(self):
        """Test tokens refill over time"""
        bucket = TokenBucket(rate=100, capacity=100)
        bucket.consume(100)  # Empty bucket

        time.sleep(0.1)  # Wait 100ms = 10 tokens

        result = bucket.consume(5)
        assert result is True  # Should have refilled enough

    def test_refill_capped_at_capacity(self, token_bucket):
        """Test refill doesn't exceed capacity"""
        time.sleep(1)  # Wait long enough to overfill
        available = token_bucket.get_available_tokens()
        assert available <= token_bucket.capacity

    def test_get_available_tokens(self, token_bucket):
        """Test getting available tokens"""
        token_bucket.consume(5)
        available = token_bucket.get_available_tokens()
        assert available >= 15.0

    def test_reset(self, token_bucket):
        """Test bucket reset"""
        token_bucket.consume(15)
        token_bucket.reset()
        assert token_bucket.tokens == token_bucket.capacity


class TestAdaptiveRateLimiter:
    """Test AdaptiveRateLimiter"""

    def test_initialization(self, adaptive_rate_limiter):
        """Test rate limiter initialization"""
        assert adaptive_rate_limiter.total_requests == 0
        assert adaptive_rate_limiter.blocked_requests == 0
        assert adaptive_rate_limiter.bucket is not None

    @pytest.mark.asyncio
    async def test_check_limit_allowed(self, adaptive_rate_limiter):
        """Test checking limit when allowed"""
        result = await adaptive_rate_limiter.check_limit()
        assert result is True
        assert adaptive_rate_limiter.total_requests == 1
        assert adaptive_rate_limiter.blocked_requests == 0

    @pytest.mark.asyncio
    async def test_check_limit_exceeded(self):
        """Test rate limit exceeded"""
        config = RateLimitConfig(rate_per_second=1, burst_size=2)
        limiter = AdaptiveRateLimiter(config)

        # Consume all tokens
        await limiter.check_limit()
        await limiter.check_limit()

        # Should be blocked now
        result = await limiter.check_limit()
        assert result is False
        assert limiter.blocked_requests > 0

    @pytest.mark.asyncio
    async def test_check_limit_with_cost(self, adaptive_rate_limiter):
        """Test checking limit with custom cost"""
        result = await adaptive_rate_limiter.check_limit(request_cost=10)
        assert result is True

    @pytest.mark.asyncio
    async def test_adapt_limit(self, adaptive_rate_limiter):
        """Test adapting rate limit"""
        old_rate = adaptive_rate_limiter.config.rate_per_second

        await adaptive_rate_limiter.adapt_limit(new_rate=50, new_burst=100)

        assert adaptive_rate_limiter.config.rate_per_second == 50
        assert adaptive_rate_limiter.config.burst_size == 100
        assert old_rate != 50

    def test_get_stats(self, adaptive_rate_limiter):
        """Test getting statistics"""
        stats = adaptive_rate_limiter.get_stats()

        assert "total_requests" in stats
        assert "blocked_requests" in stats
        assert "block_rate" in stats
        assert "available_tokens" in stats
        assert "config" in stats


class TestQoSController:
    """Test QoSController"""

    def test_initialization(self, qos_controller):
        """Test QoS controller initialization"""
        assert qos_controller.total_bandwidth == 1000.0
        assert qos_controller.allocated_bandwidth == {}
        assert qos_controller.traffic_profiles == {}

    @pytest.mark.asyncio
    async def test_create_profile(self, qos_controller, traffic_profile):
        """Test creating traffic profile"""
        result = await qos_controller.create_profile(traffic_profile)

        assert result is True
        assert "production" in qos_controller.traffic_profiles
        assert qos_controller.allocated_bandwidth["production"] == 500.0

    @pytest.mark.asyncio
    async def test_create_profile_insufficient_bandwidth(self, qos_controller):
        """Test creating profile with insufficient bandwidth"""
        # Allocate most bandwidth
        profile1 = TrafficProfile(
            name="big", priority=TrafficPriority.HIGH,
            max_rate_mbps=900.0, burst_size_mb=100.0
        )
        await qos_controller.create_profile(profile1)

        # Try to allocate more than available
        profile2 = TrafficProfile(
            name="too_big", priority=TrafficPriority.MEDIUM,
            max_rate_mbps=200.0, burst_size_mb=50.0
        )
        result = await qos_controller.create_profile(profile2)

        assert result is False
        assert "too_big" not in qos_controller.traffic_profiles

    @pytest.mark.asyncio
    async def test_remove_profile(self, qos_controller, traffic_profile):
        """Test removing traffic profile"""
        await qos_controller.create_profile(traffic_profile)

        removed = await qos_controller.remove_profile("production")

        assert removed is True
        assert "production" not in qos_controller.traffic_profiles
        assert "production" not in qos_controller.allocated_bandwidth

    @pytest.mark.asyncio
    async def test_remove_nonexistent_profile(self, qos_controller):
        """Test removing profile that doesn't exist"""
        removed = await qos_controller.remove_profile("nonexistent")
        assert removed is False

    def test_get_bandwidth_allocation(self, qos_controller):
        """Test getting bandwidth allocation"""
        allocation = qos_controller.get_bandwidth_allocation()
        assert isinstance(allocation, dict)

    def test_get_available_bandwidth(self, qos_controller):
        """Test getting available bandwidth"""
        available = qos_controller.get_available_bandwidth()
        assert available == 1000.0  # All available initially

    @pytest.mark.asyncio
    async def test_get_available_bandwidth_after_allocation(
        self, qos_controller, traffic_profile
    ):
        """Test available bandwidth after allocation"""
        await qos_controller.create_profile(traffic_profile)

        available = qos_controller.get_available_bandwidth()
        assert available == 500.0  # 1000 - 500


class TestAdaptiveTrafficShaper:
    """Test AdaptiveTrafficShaper"""

    def test_initialization(self, traffic_shaper):
        """Test traffic shaper initialization"""
        assert traffic_shaper.qos is not None
        assert traffic_shaper.rate_limiters == {}
        assert traffic_shaper.metrics is not None

    @pytest.mark.asyncio
    async def test_shape_traffic_with_rate_limits(self, traffic_shaper):
        """Test shaping traffic with rate limits"""
        policy = {
            "rate_limits": {
                "api": {
                    "rate_per_second": 1000,
                    "burst_size": 2000,
                    "action": RateLimitAction.DROP.value,
                }
            }
        }

        result = await traffic_shaper.shape_traffic("high", policy)

        assert result.status == "SUCCESS"
        assert result.rate_limits_set == 1
        assert "api" in traffic_shaper.rate_limiters

    @pytest.mark.asyncio
    async def test_shape_traffic_with_qos(self, traffic_shaper):
        """Test shaping traffic with QoS profiles"""
        policy = {
            "qos_profiles": [
                {
                    "name": "critical",
                    "priority": TrafficPriority.CRITICAL,
                    "max_rate_mbps": 500.0,
                    "burst_size_mb": 100.0,
                }
            ]
        }

        result = await traffic_shaper.shape_traffic("high", policy)

        assert result.status == "SUCCESS"
        assert result.qos_policies_created == 1
        assert "critical" in result.profiles_applied
        assert result.bandwidth_allocated_mbps == 500.0

    @pytest.mark.asyncio
    async def test_shape_traffic_combined(self, traffic_shaper):
        """Test shaping with both rate limits and QoS"""
        policy = {
            "rate_limits": {
                "web": {
                    "rate_per_second": 500,
                    "burst_size": 1000,
                    "action": RateLimitAction.DROP.value,
                }
            },
            "qos_profiles": [
                {
                    "name": "web_traffic",
                    "priority": TrafficPriority.HIGH,
                    "max_rate_mbps": 300.0,
                    "burst_size_mb": 50.0,
                }
            ],
        }

        result = await traffic_shaper.shape_traffic("medium", policy)

        assert result.status == "SUCCESS"
        assert result.rate_limits_set == 1
        assert result.qos_policies_created == 1

    @pytest.mark.asyncio
    async def test_check_rate_limit(self, traffic_shaper):
        """Test checking rate limit"""
        policy = {
            "rate_limits": {
                "test": {
                    "rate_per_second": 100,
                    "burst_size": 200,
                    "action": RateLimitAction.DROP.value,
                }
            }
        }
        await traffic_shaper.shape_traffic("low", policy)

        allowed = await traffic_shaper.check_rate_limit("test")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_nonexistent(self, traffic_shaper):
        """Test checking nonexistent rate limiter"""
        allowed = await traffic_shaper.check_rate_limit("nonexistent")
        assert allowed is True  # Allow if no limiter

    @pytest.mark.asyncio
    async def test_adapt_to_threat(self, traffic_shaper):
        """Test adapting to threat level"""
        # Setup rate limiter
        policy = {
            "rate_limits": {
                "api": {
                    "rate_per_second": 1000,
                    "burst_size": 2000,
                    "action": RateLimitAction.DROP.value,
                }
            }
        }
        await traffic_shaper.shape_traffic("low", policy)

        # Adapt to high threat
        await traffic_shaper.adapt_to_threat("high")

        # Should have reduced rate
        limiter = traffic_shaper.rate_limiters["api"]
        assert limiter.config.rate_per_second == 500  # 1000 * 0.5

    @pytest.mark.asyncio
    async def test_adapt_to_threat_critical(self, traffic_shaper):
        """Test adapting to critical threat"""
        policy = {
            "rate_limits": {
                "api": {
                    "rate_per_second": 1000,
                    "burst_size": 2000,
                    "action": RateLimitAction.DROP.value,
                }
            }
        }
        await traffic_shaper.shape_traffic("low", policy)

        await traffic_shaper.adapt_to_threat("critical")

        limiter = traffic_shaper.rate_limiters["api"]
        assert limiter.config.rate_per_second == 250  # 1000 * 0.25

    def test_get_rate_limiter_stats(self, traffic_shaper):
        """Test getting rate limiter stats"""
        stats = traffic_shaper.get_rate_limiter_stats()
        assert isinstance(stats, dict)

    def test_get_bandwidth_usage(self, traffic_shaper):
        """Test getting bandwidth usage"""
        usage = traffic_shaper.get_bandwidth_usage()

        assert "total_mbps" in usage
        assert "allocated_mbps" in usage
        assert "available_mbps" in usage
        assert "utilization_percent" in usage

    @pytest.mark.asyncio
    async def test_get_bandwidth_usage_after_allocation(self, traffic_shaper):
        """Test bandwidth usage after allocation"""
        policy = {
            "qos_profiles": [
                {
                    "name": "test",
                    "priority": TrafficPriority.HIGH,
                    "max_rate_mbps": 500.0,
                    "burst_size_mb": 100.0,
                }
            ]
        }
        await traffic_shaper.shape_traffic("low", policy)

        usage = traffic_shaper.get_bandwidth_usage()
        assert usage["allocated_mbps"] == 500.0
        assert usage["available_mbps"] == 500.0
        assert usage["utilization_percent"] == 50.0

    def test_get_active_profiles(self, traffic_shaper):
        """Test getting active profiles"""
        profiles = traffic_shaper.get_active_profiles()
        assert isinstance(profiles, list)

    @pytest.mark.asyncio
    async def test_get_active_profiles_after_creation(self, traffic_shaper):
        """Test active profiles after creation"""
        policy = {
            "qos_profiles": [
                {
                    "name": "profile1",
                    "priority": TrafficPriority.HIGH,
                    "max_rate_mbps": 200.0,
                    "burst_size_mb": 50.0,
                }
            ]
        }
        await traffic_shaper.shape_traffic("low", policy)

        profiles = traffic_shaper.get_active_profiles()
        assert "profile1" in profiles

    def test_has_rate_limiter(self, traffic_shaper):
        """Test checking if rate limiter exists"""
        assert traffic_shaper.has_rate_limiter("test") is False

    @pytest.mark.asyncio
    async def test_has_rate_limiter_after_creation(self, traffic_shaper):
        """Test has_rate_limiter after creation"""
        policy = {
            "rate_limits": {
                "test": {
                    "rate_per_second": 100,
                    "burst_size": 200,
                    "action": RateLimitAction.DROP.value,
                }
            }
        }
        await traffic_shaper.shape_traffic("low", policy)

        assert traffic_shaper.has_rate_limiter("test") is True


class TestTrafficShapingMetrics:
    """Test Prometheus metrics"""

    def test_metrics_initialization(self):
        """Test metrics are initialized"""
        metrics = TrafficShapingMetrics()

        assert metrics.shaping_operations_total is not None
        assert metrics.active_rate_limits is not None
        assert metrics.packets_shaped_total is not None
        assert metrics.bandwidth_allocated is not None


class TestTrafficShapingErrorHandling:
    """Test error handling in traffic shaping"""

    @pytest.mark.asyncio
    async def test_shape_traffic_empty_policy(self, traffic_shaper):
        """Test shaping with empty policy (should fail)"""
        result = await traffic_shaper.shape_traffic("high", {})

        assert result.status == "FAILED"

    @pytest.mark.asyncio
    async def test_shape_traffic_exception_handling(self, traffic_shaper):
        """Test exception handling in shape_traffic"""
        # Mock QoS to raise exception
        async def mock_raise(*args, **kwargs):
            raise Exception("Simulated QoS error")

        traffic_shaper.qos.create_profile = mock_raise

        policy = {
            "qos_profiles": [
                {
                    "name": "test",
                    "priority": TrafficPriority.HIGH,
                    "max_rate_mbps": 100.0,
                    "burst_size_mb": 50.0,
                }
            ]
        }

        result = await traffic_shaper.shape_traffic("high", policy)

        assert result.status == "FAILED"
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_adapt_to_invalid_threat_level(self, traffic_shaper):
        """Test adapting to invalid threat level"""
        policy = {
            "rate_limits": {
                "api": {
                    "rate_per_second": 1000,
                    "burst_size": 2000,
                    "action": RateLimitAction.DROP.value,
                }
            }
        }
        await traffic_shaper.shape_traffic("low", policy)

        # Should handle gracefully
        await traffic_shaper.adapt_to_threat("invalid_level")

        # Rate should remain unchanged
        limiter = traffic_shaper.rate_limiters["api"]
        assert limiter.config.rate_per_second == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
