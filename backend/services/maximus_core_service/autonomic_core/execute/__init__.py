"""
Autonomic Execute Module - Actuators

5 actuators for implementing resource allocation decisions:
- Kubernetes (HPA, resource limits, pod restart, node drain)
- Docker (container restart, resource update)
- Database (connection pool, query killer, vacuum)
- Cache (Redis flush, warm)
- Load Balancer (traffic shift, circuit breaker)

Safety mechanisms: dry-run, auto-rollback, rate limiting, human approval.
"""

from .kubernetes_actuator import KubernetesActuator
from .docker_actuator import DockerActuator
from .database_actuator import DatabaseActuator
from .cache_actuator import CacheActuator
from .loadbalancer_actuator import LoadBalancerActuator, CircuitBreaker
from .safety_manager import SafetyManager

__all__ = [
    'KubernetesActuator',
    'DockerActuator',
    'DatabaseActuator',
    'CacheActuator',
    'LoadBalancerActuator',
    'CircuitBreaker',
    'SafetyManager'
]
