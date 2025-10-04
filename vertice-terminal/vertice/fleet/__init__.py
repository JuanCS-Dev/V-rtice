"""
🚀 VÉRTICE FLEET MANAGER
Gerenciamento de fleet de endpoints para threat hunting em escala

Componentes:
- EndpointRegistry: Inventory de endpoints (SQLite/PostgreSQL)
- HealthMonitor: Tracking de saúde e disponibilidade
- CapabilityDetector: Detecção de OS, ferramentas, recursos
- ResultAggregator: Agregação e deduplicação de resultados
- LoadBalancer: Distribuição inteligente de tasks
"""

from .registry import EndpointRegistry, Endpoint, EndpointStatus
from .health_monitor import HealthMonitor
from .capability_detector import CapabilityDetector
from .result_aggregator import ResultAggregator, AggregatedResult
from .load_balancer import (
    LoadBalancer,
    LoadBalancingStrategy,
    TaskAssignment,
    EndpointLoad
)

__all__ = [
    "EndpointRegistry",
    "Endpoint",
    "EndpointStatus",
    "HealthMonitor",
    "CapabilityDetector",
    "ResultAggregator",
    "AggregatedResult",
    "LoadBalancer",
    "LoadBalancingStrategy",
    "TaskAssignment",
    "EndpointLoad",
]
