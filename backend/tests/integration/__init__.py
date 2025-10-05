"""FASE 7: Integration Testing Suite

Production-ready integration testing for VÉRTICE.
"""

from test_framework import IntegrationTestFramework, TestResult, PerformanceMetrics
from test_scenarios import (
    APTSimulation,
    RansomwareSimulation,
    DDoSSimulation,
    ZeroDaySimulation
)

__all__ = [
    'IntegrationTestFramework',
    'TestResult',
    'PerformanceMetrics',
    'APTSimulation',
    'RansomwareSimulation',
    'DDoSSimulation',
    'ZeroDaySimulation'
]
