"""Containment Package - Advanced Isolation & Traffic Control

Implements advanced containment mechanisms:
1. Zone-Based Isolation (microsegmentation)
2. Traffic Shaping (adaptive rate limiting)
3. Dynamic Honeypots (deception & TTP collection)

Biological Inspiration:
- Physical barriers (cell walls) → Zone isolation
- Membrane transport control → Traffic shaping
- Immune decoys → Honeypots

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - "Constância vence"
"""

from .honeypots import (
    AttackerProfile,
    DeceptionEngine,
    HoneypotConfig,
    HoneypotDeployment,
    HoneypotLevel,
    HoneypotOrchestrator,
    HoneypotResult,
    HoneypotType,
    TTPs,
)
from .traffic_shaping import (
    AdaptiveRateLimiter,
    AdaptiveTrafficShaper,
    QoSController,
    RateLimitAction,
    RateLimitConfig,
    TokenBucket,
    TrafficPriority,
    TrafficProfile,
    TrafficShapingResult,
)
from .zone_isolation import (
    DynamicFirewallController,
    NetworkSegmenter,
    TrustLevel,
    ZeroTrustAccessController,
    ZoneIsolationEngine,
    ZoneIsolationResult,
)

__all__ = [
    # Zone isolation
    "ZoneIsolationEngine",
    "DynamicFirewallController",
    "NetworkSegmenter",
    "ZeroTrustAccessController",
    "ZoneIsolationResult",
    "TrustLevel",
    # Traffic shaping
    "AdaptiveTrafficShaper",
    "AdaptiveRateLimiter",
    "QoSController",
    "TokenBucket",
    "TrafficProfile",
    "TrafficPriority",
    "RateLimitConfig",
    "RateLimitAction",
    "TrafficShapingResult",
    # Honeypots
    "HoneypotOrchestrator",
    "DeceptionEngine",
    "HoneypotConfig",
    "HoneypotDeployment",
    "HoneypotResult",
    "HoneypotType",
    "HoneypotLevel",
    "TTPs",
    "AttackerProfile",
]

__version__ = "1.0.0"
__author__ = "MAXIMUS Defensive Team"
__doc__ = """
Advanced Containment System

Zone Isolation:
- Dynamic firewall rules (iptables/nftables)
- Network microsegmentation (SDN-ready)
- Zero-trust access control
- Progressive isolation levels

Traffic Shaping:
- Adaptive rate limiting (token bucket)
- QoS prioritization
- Bandwidth allocation
- DDoS mitigation

Integration:
    >>> from containment import ZoneIsolationEngine, AdaptiveTrafficShaper
    >>> isolator = ZoneIsolationEngine()
    >>> shaper = AdaptiveTrafficShaper()
    >>> result = await isolator.isolate(zones=["DMZ"], policy=policy)
    >>> shaped = await shaper.shape_traffic(threat_level="high", policy=policy)
"""
