"""
Deception Engine for Reactive Fabric.

Creates and manages honeytokens, decoys, and deceptive elements.
Phase 1: PASSIVE deception only - monitoring without active engagement.
"""

from .deception_engine import (
    DeceptionEngine,
    DeceptionConfig,
    Honeytoken,
    DecoySystem,
    DeceptionEvent,
    DeceptionType
)

__all__ = [
    "DeceptionEngine",
    "DeceptionConfig",
    "Honeytoken",
    "DecoySystem",
    "DeceptionEvent",
    "DeceptionType"
]