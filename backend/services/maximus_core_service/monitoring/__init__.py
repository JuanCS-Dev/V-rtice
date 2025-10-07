"""
MAXIMUS AI 3.0 - Monitoring Package

Prometheus metrics exporter and observability tools for production monitoring.

Components:
- MaximusMetricsExporter: Comprehensive metrics collection for all MAXIMUS subsystems
- Predictive Coding metrics (free energy, latency)
- Neuromodulation metrics (dopamine, ACh, NE, 5-HT)
- Skill Learning metrics (executions, rewards, success rate)
- Attention System metrics (salience, thresholds)
- Ethical AI metrics (approval rate, violations)
- System metrics (throughput, latency, accuracy)

REGRA DE OURO: Zero mocks, production-ready monitoring
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from .prometheus_exporter import MaximusMetricsExporter

__all__ = [
    "MaximusMetricsExporter",
]

__version__ = "3.0.0"
__author__ = "Claude Code + JuanCS-Dev"
__regra_de_ouro__ = "10/10"
