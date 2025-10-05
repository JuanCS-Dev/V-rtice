"""Maximus Core Service - Autonomic Core Package.

This package contains the core components responsible for the self-managing
(autonomic) capabilities of the Maximus AI system. It implements the Homeostatic
Control Loop (HCL) which continuously monitors, analyzes, plans, and executes
resource adjustments to maintain optimal performance and stability.

Modules within this package include:
- `hcl_orchestrator`: The main HCL orchestrator.
- `monitor`: Collects real-time system metrics (Prometheus, Kafka).
- `analyze`: Analyzes metrics for anomalies, failures, degradation (SARIMA, XGBoost, PELT).
- `plan`: Generates resource allocation plans (Fuzzy Logic, RL).
- `execute`: Executes planned resource adjustments (K8s, Docker, DB, Cache, LB).
- `knowledge_base`: Stores decisions for learning (PostgreSQL + TimescaleDB).
"""

from .hcl_orchestrator import (
    HomeostaticControlLoop,
    run_homeostatic_control_loop
)

__all__ = [
    'HomeostaticControlLoop',
    'run_homeostatic_control_loop'
]
