"""Attention System - Foveal/Peripheral Vision-Inspired Resource Allocation

Bio-inspired two-tier processing system that efficiently allocates analytical
resources by combining:
- Peripheral monitoring: Fast, lightweight scanning of all inputs
- Foveal analysis: Deep, expensive analysis of high-salience targets

This mimics human visual attention, where peripheral vision detects movement
and changes, triggering foveal (central) vision to focus on important details.

Key Components:
- AttentionSystem: Main coordinator of attention-driven monitoring
- PeripheralMonitor: Lightweight statistical scanning (<100ms)
- FovealAnalyzer: Deep threat analysis for high-salience targets
- SalienceScorer: Calculates attention priority scores
"""

from .attention_core import (
    AttentionSystem,
    FovealAnalysis,
    FovealAnalyzer,
    PeripheralDetection,
    PeripheralMonitor,
)
from .salience_scorer import SalienceLevel, SalienceScore, SalienceScorer

__all__ = [
    # Main components
    "AttentionSystem",
    "PeripheralMonitor",
    "FovealAnalyzer",
    # Data structures
    "PeripheralDetection",
    "FovealAnalysis",
    # Salience scoring
    "SalienceScorer",
    "SalienceScore",
    "SalienceLevel",
]
