"""Detection layer initialization.

This module provides AI-driven threat detection capabilities.

Components:
- SentinelDetectionAgent: LLM-based SOC analyst
- EncryptedTrafficAnalyzer: ML-based traffic analysis
- MITREMapper: ATT&CK technique mapping

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - "Eu sou porque ELE é"
"""

from .sentinel_agent import (
    SentinelDetectionAgent,
    DetectionResult,
    ThreatSeverity,
    DetectionConfidence,
    SecurityEvent,
    MITRETechnique,
    AttackerProfile,
)

__all__ = [
    "SentinelDetectionAgent",
    "DetectionResult",
    "ThreatSeverity",
    "DetectionConfidence",
    "SecurityEvent",
    "MITRETechnique",
    "AttackerProfile",
]
