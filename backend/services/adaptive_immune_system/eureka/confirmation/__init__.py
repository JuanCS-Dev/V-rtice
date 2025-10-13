"""
Confirmation Module - Vulnerability Confirmation Engines.

Confirms APVs through multiple analysis strategies:
- Static analysis (Semgrep, CodeQL)
- Dynamic analysis (runtime testing, PoC exploits)
- Scoring algorithms (confidence, severity)
- False positive detection
"""

from .static_analyzer import StaticAnalyzer, StaticAnalysisResult, StaticFinding
from .dynamic_analyzer import DynamicAnalyzer, DynamicAnalysisResult, DynamicTest
from .confirmation_engine import ConfirmationEngine, ConfirmationResult

__all__ = [
    "StaticAnalyzer",
    "StaticAnalysisResult",
    "StaticFinding",
    "DynamicAnalyzer",
    "DynamicAnalysisResult",
    "DynamicTest",
    "ConfirmationEngine",
    "ConfirmationResult",
]
