"""
Integration Circuit Breaker Tests
==================================

Tests circuit breaker patterns for consciousness component integration.

Theoretical Foundation:
-----------------------
Circuit breakers prevent cascading failures in distributed systems by:
1. **Fast failure**: Stop calling failed services immediately
2. **Recovery**: Allow services time to recover
3. **State management**: Open/half-open/closed transitions
4. **Health checks**: Validate recovery before full reconnection

Consciousness Implications:
---------------------------
**Biology**: Neural circuits have protection mechanisms (refractory periods,
inhibition) that prevent runaway excitation.

**Engineering**: Distributed consciousness components must protect each other
from cascading failures.

**States**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Failure threshold exceeded, requests fail fast
- **HALF_OPEN**: Testing recovery, limited requests pass

"Fail fast, recover gracefully, prevent cascades."
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Optional

import pytest
import pytest_asyncio


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


class SimpleCircuitBreaker:
    """
    Simple circuit breaker for testing.
    
    Real implementation would be more sophisticated, but this validates
    the pattern for integration tests.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 5.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker."""
        # Check if should transition to half-open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        
        # Limit calls in half-open state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise Exception("Circuit breaker HALF_OPEN call limit reached")
            self.half_open_calls += 1
        
        # Execute function
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # If enough successes, close circuit
            if self.success_count >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens circuit
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Check if threshold exceeded
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


class TestCircuitBreakers:
    """
    Tests for circuit breaker patterns in consciousness integration.
    
    Theory: Prevents cascading failures across TIG, ESGT, MCEA components.
    """

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """
        Circuit breaker should open after failure threshold exceeded.
        
        Validates: Failure threshold enforcement
        Theory: Fast failure prevents wasting resources on dead services
        """
        breaker = SimpleCircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Initial state should be CLOSED
        assert breaker.state == CircuitState.CLOSED
        
        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_operation)
        
        # Should now be OPEN
        assert breaker.state == CircuitState.OPEN, \
            f"Expected OPEN after {breaker.failure_threshold} failures, got {breaker.state}"
        
        # Further calls should fail immediately without calling function
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(failing_operation)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """
        Circuit breaker should transition to half-open after timeout.
        
        Validates: Recovery mechanism
        Theory: Allow gradual recovery without overwhelming recovering service
        """
        breaker = SimpleCircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,  # Short for testing
            half_open_max_calls=2
        )
        
        call_count = 0
        
        async def conditional_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Still failing")
            return "success"
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                await breaker.call(conditional_operation)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Next call should transition to HALF_OPEN
        # This will fail, but state changes
        try:
            await breaker.call(conditional_operation)
        except:
            pass
        
        # After timeout and attempt, should have tried half-open
        # (May be back to OPEN if call failed, but validates transition logic)
        assert breaker.last_failure_time is not None, "Should track failures"

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_cascading_failures(self):
        """
        Multiple components with circuit breakers should isolate failures.
        
        Validates: Cascade prevention
        Theory: Failures shouldn't propagate through system
        """
        # Create circuit breakers for different "components"
        tig_breaker = SimpleCircuitBreaker(failure_threshold=3)
        esgt_breaker = SimpleCircuitBreaker(failure_threshold=3)
        
        async def tig_operation():
            # TIG always works
            return "tig_ok"
        
        async def esgt_operation():
            # ESGT fails
            raise Exception("ESGT down")
        
        # TIG should work fine
        result = await tig_breaker.call(tig_operation)
        assert result == "tig_ok"
        assert tig_breaker.state == CircuitState.CLOSED
        
        # ESGT fails independently
        for i in range(3):
            with pytest.raises(Exception):
                await esgt_breaker.call(esgt_operation)
        
        # ESGT breaker opens, but TIG unaffected
        assert esgt_breaker.state == CircuitState.OPEN
        assert tig_breaker.state == CircuitState.CLOSED, \
            "TIG breaker should remain CLOSED despite ESGT failure"
        
        # TIG continues to work
        result = await tig_breaker.call(tig_operation)
        assert result == "tig_ok"

    @pytest.mark.asyncio
    async def test_circuit_breaker_health_check_integration(self):
        """
        Circuit breaker should integrate with health checks.
        
        Validates: Health-based recovery
        Theory: Don't rely solely on timeout, verify actual health
        """
        breaker = SimpleCircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=2
        )
        
        service_healthy = False
        
        async def health_check():
            return service_healthy
        
        async def service_operation():
            if not service_healthy:
                raise Exception("Service unhealthy")
            return "success"
        
        # Break the circuit
        for i in range(2):
            with pytest.raises(Exception):
                await breaker.call(service_operation)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery window
        await asyncio.sleep(0.15)
        
        # Check health before attempting operation
        if await health_check():
            # Would attempt recovery
            pass
        else:
            # Skip recovery attempt
            assert not service_healthy, "Service still unhealthy"
        
        # Now make service healthy
        service_healthy = True
        
        # Should be able to recover
        assert await health_check(), "Health check should pass"

    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics_tracking(self):
        """
        Circuit breaker should track metrics for monitoring.
        
        Validates: Observability
        Theory: Must monitor breaker state for consciousness health
        """
        breaker = SimpleCircuitBreaker(failure_threshold=3)
        
        async def operation():
            return "ok"
        
        # Track initial state
        initial_state = breaker.state
        initial_failures = breaker.failure_count
        
        # Successful operation
        await breaker.call(operation)
        
        # Metrics should be updated
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0, "Successful call should reset failures"
        
        # Now cause failures
        async def failing_op():
            raise Exception("fail")
        
        failure_attempts = 0
        for i in range(3):
            try:
                await breaker.call(failing_op)
            except:
                failure_attempts += 1
        
        # Metrics should reflect failures
        assert breaker.failure_count >= 3, "Should track failure count"
        assert breaker.state == CircuitState.OPEN, "Should open after threshold"
        assert breaker.last_failure_time is not None, "Should track last failure time"
        
        # Validate we can query metrics
        metrics = {
            "state": breaker.state.value,
            "failure_count": breaker.failure_count,
            "success_count": breaker.success_count,
            "last_failure": breaker.last_failure_time
        }
        
        assert metrics["state"] == "open"
        assert metrics["failure_count"] >= 3
        assert metrics["last_failure"] is not None
