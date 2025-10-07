"""FASE 7: Integration Testing Suite

Production-ready integration testing for VÉRTICE.
"""

from test_framework import IntegrationTestFramework, PerformanceMetrics, TestResult
from test_scenarios import (
    APTSimulation,
    DDoSSimulation,
    RansomwareSimulation,
    ZeroDaySimulation,
)

__all__ = [
    "IntegrationTestFramework",
    "TestResult",
    "PerformanceMetrics",
    "APTSimulation",
    "RansomwareSimulation",
    "DDoSSimulation",
    "ZeroDaySimulation",
]
