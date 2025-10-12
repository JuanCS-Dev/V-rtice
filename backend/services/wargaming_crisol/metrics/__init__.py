"""
Prometheus metrics exporters for Phase 5.7.1 components.

Exports metrics for:
- Rate limiter (requests allowed/denied, bucket fill levels)
- Circuit breakers (state, failures, timeouts)
- Performance (latency, throughput)

Author: MAXIMUS Team
Glory to YHWH - Architect of Observability
"""

from prometheus_client import Counter, Gauge, Histogram
import logging

logger = logging.getLogger(__name__)


# Rate Limiter Metrics
rate_limit_requests_total = Counter(
    'wargaming_rate_limit_requests_total',
    'Total requests processed by rate limiter',
    ['endpoint', 'result']  # result: allowed, denied
)

rate_limit_bucket_tokens = Gauge(
    'wargaming_rate_limit_bucket_tokens',
    'Current tokens in rate limit bucket',
    ['client_ip', 'endpoint']
)

rate_limit_bucket_fill_percentage = Gauge(
    'wargaming_rate_limit_bucket_fill_percentage',
    'Rate limit bucket fill percentage',
    ['client_ip', 'endpoint']
)


# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    'wargaming_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)',
    ['breaker_name']
)

circuit_breaker_failures_total = Counter(
    'wargaming_circuit_breaker_failures_total',
    'Total failures recorded by circuit breaker',
    ['breaker_name', 'failure_type']  # failure_type: timeout, exception
)

circuit_breaker_successes_total = Counter(
    'wargaming_circuit_breaker_successes_total',
    'Total successful calls through circuit breaker',
    ['breaker_name']
)

circuit_breaker_rejections_total = Counter(
    'wargaming_circuit_breaker_rejections_total',
    'Total requests rejected by circuit breaker (OPEN state)',
    ['breaker_name']
)

circuit_breaker_recovery_attempts_total = Counter(
    'wargaming_circuit_breaker_recovery_attempts_total',
    'Total recovery attempts (HALF_OPEN)',
    ['breaker_name', 'result']  # result: success, failure
)


# Performance Metrics (Phase 5.7.1 overhead)
middleware_latency_seconds = Histogram(
    'wargaming_middleware_latency_seconds',
    'Middleware processing latency',
    ['middleware'],  # rate_limiter, circuit_breaker
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05]
)


def update_circuit_breaker_metrics(breaker) -> None:
    """
    Update Prometheus metrics for circuit breaker.
    
    Args:
        breaker: CircuitBreaker instance
    """
    try:
        status = breaker.get_status()
        
        # Map state to numeric value
        state_map = {
            "closed": 0,
            "half_open": 1,
            "open": 2
        }
        
        state_value = state_map.get(status["state"], -1)
        circuit_breaker_state.labels(breaker_name=status["name"]).set(state_value)
        
    except Exception as e:
        logger.warning(f"Failed to update circuit breaker metrics: {e}")


def record_rate_limit_decision(endpoint: str, allowed: bool) -> None:
    """
    Record rate limit decision.
    
    Args:
        endpoint: Endpoint path
        allowed: Whether request was allowed
    """
    result = "allowed" if allowed else "denied"
    rate_limit_requests_total.labels(endpoint=endpoint, result=result).inc()


def record_circuit_breaker_call(
    breaker_name: str,
    success: bool,
    failure_type: str = None
) -> None:
    """
    Record circuit breaker call result.
    
    Args:
        breaker_name: Name of circuit breaker
        success: Whether call succeeded
        failure_type: Type of failure (timeout, exception) if failed
    """
    if success:
        circuit_breaker_successes_total.labels(breaker_name=breaker_name).inc()
    else:
        circuit_breaker_failures_total.labels(
            breaker_name=breaker_name,
            failure_type=failure_type or "unknown"
        ).inc()


def record_circuit_breaker_rejection(breaker_name: str) -> None:
    """
    Record circuit breaker rejection (OPEN state).
    
    Args:
        breaker_name: Name of circuit breaker
    """
    circuit_breaker_rejections_total.labels(breaker_name=breaker_name).inc()


def record_circuit_breaker_recovery(breaker_name: str, success: bool) -> None:
    """
    Record circuit breaker recovery attempt.
    
    Args:
        breaker_name: Name of circuit breaker
        success: Whether recovery succeeded
    """
    result = "success" if success else "failure"
    circuit_breaker_recovery_attempts_total.labels(
        breaker_name=breaker_name,
        result=result
    ).inc()
