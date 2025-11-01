"""MVP Core Module - Narrative generation and system observation.

This package contains the core functionality of the MAXIMUS Vision Protocol (MVP):

- NarrativeEngine: LLM-powered narrative generation from system metrics
- SystemObserver: Real-time metrics collection and analysis

Author: Vértice Platform Team
License: Proprietary
"""

from .narrative_engine import NarrativeEngine
from .system_observer import SystemObserver

__all__ = [
    "NarrativeEngine",
    "SystemObserver",
]
