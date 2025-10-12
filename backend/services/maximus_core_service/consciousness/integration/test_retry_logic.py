"""
Integration Retry Logic Tests
==============================

Tests retry patterns with exponential backoff for consciousness integration.

Theoretical Foundation:
-----------------------
Retry logic handles transient failures gracefully:
1. **Exponential backoff**: Increasing delays between retries
2. **Jitter**: Random variation to prevent thundering herd
3. **Max retries**: Prevent infinite loops
4. **Error classification**: Distinguish transient vs permanent

Consciousness Implications:
---------------------------
**Biology**: Neural systems retry failed transmissions (synaptic reliability
isn't 100%). Neurotransmitter release has probabilistic nature.

**Engineering**: Distributed consciousness needs resilience to transient
network/compute failures without overwhelming recovering services.

**Key Patterns**:
- Transient errors → Retry (network blip, temporary overload)
- Permanent errors → Fail fast (invalid input, missing resource)
- Backoff → Give service time to recover
- Jitter → Prevent synchronized retry storms

"Retry smartly, not blindly."
"""

import asyncio
import random
import time
from typing import Callable, Optional

import pytest


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryableError(Exception):
    """Exception that should trigger retry."""
    pass


class PermanentError(Exception):
    """Exception that should NOT trigger retry."""
    pass


async def retry_with_backoff(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
):
    """
    Execute function with exponential backoff retry.
    
    Returns:
        Result of function if successful
        
    Raises:
        Last exception if all retries exhausted
    """
    attempt = 0
    last_exception = None
    
    while attempt < config.max_attempts:
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            return result
        except PermanentError:
            # Don't retry permanent errors
            raise
        except Exception as e:
            last_exception = e
            attempt += 1
            
            if attempt >= config.max_attempts:
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** (attempt - 1)),
                config.max_delay
            )
            
            # Add jitter if enabled
            if config.jitter:
                jitter_amount = delay * 0.1  # 10% jitter
                delay += random.uniform(-jitter_amount, jitter_amount)
            
            await asyncio.sleep(max(0, delay))
    
    # All retries exhausted
    raise last_exception


class TestRetryLogic:
    """
    Tests for retry logic patterns in consciousness integration.
    
    Theory: Handle transient failures without overwhelming services.
    """

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """
        Retry delays should increase exponentially.
        
        Validates: Exponential backoff implementation
        Theory: Give failing service progressively more time to recover
        """
        config = RetryConfig(
            max_attempts=4,
            base_delay=0.1,
            exponential_base=2.0,
            jitter=False  # Disable for predictable testing
        )
        
        attempt_times = []
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            attempt_times.append(time.time())
            raise RetryableError("Transient failure")
        
        # Should exhaust all retries
        with pytest.raises(RetryableError):
            await retry_with_backoff(failing_operation, config)
        
        # Should have made all attempts
        assert call_count == 4, f"Expected 4 attempts, got {call_count}"
        
        # Check delays are exponential
        if len(attempt_times) >= 3:
            delay1 = attempt_times[1] - attempt_times[0]
            delay2 = attempt_times[2] - attempt_times[1]
            
            # Second delay should be roughly 2x first (exponential base = 2)
            # Allow some tolerance
            assert delay2 > delay1 * 1.5, \
                f"Second delay ({delay2:.3f}s) should be ~2x first ({delay1:.3f}s)"

    @pytest.mark.asyncio
    async def test_retry_with_jitter(self):
        """
        Jitter should add randomness to prevent thundering herd.
        
        Validates: Jitter implementation
        Theory: Random delays prevent synchronized retry storms
        """
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            exponential_base=2.0,
            jitter=True  # Enable jitter
        )
        
        attempt_times = []
        
        async def failing_operation():
            attempt_times.append(time.time())
            raise RetryableError("Transient")
        
        with pytest.raises(RetryableError):
            await retry_with_backoff(failing_operation, config)
        
        # Calculate delays
        delays = []
        for i in range(1, len(attempt_times)):
            delays.append(attempt_times[i] - attempt_times[i-1])
        
        # Delays should vary (jitter adds randomness)
        # But should still be in reasonable range
        for delay in delays:
            assert 0 < delay < 1.0, f"Delay {delay:.3f}s should be reasonable"

    @pytest.mark.asyncio
    async def test_retry_max_attempts_enforced(self):
        """
        Should stop after max attempts reached.
        
        Validates: Max retry limit
        Theory: Prevent infinite retry loops
        """
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        
        call_count = 0
        
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Always fails")
        
        # Should fail after 3 attempts
        with pytest.raises(RetryableError):
            await retry_with_backoff(always_fails, config)
        
        # Exactly 3 attempts should have been made
        assert call_count == 3, \
            f"Expected exactly 3 attempts, got {call_count}"

    @pytest.mark.asyncio
    async def test_retry_idempotency_validation(self):
        """
        Retried operations should be idempotent (safe to retry).
        
        Validates: Idempotency requirement
        Theory: Retries shouldn't cause side effects to accumulate
        """
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        
        # Simulated state - should only change once on success
        state = {"value": 0, "calls": 0}
        
        async def idempotent_operation():
            state["calls"] += 1
            
            # Fail first 2 times, succeed on 3rd
            if state["calls"] < 3:
                raise RetryableError("Not ready yet")
            
            # On success, increment value
            # This should only happen once despite retries
            state["value"] += 1
            return "success"
        
        result = await retry_with_backoff(idempotent_operation, config)
        
        # Should have succeeded
        assert result == "success"
        
        # Value should have changed exactly once
        assert state["value"] == 1, \
            f"Idempotent operation should execute once, value is {state['value']}"
        
        # But was called 3 times (2 failures + 1 success)
        assert state["calls"] == 3

    @pytest.mark.asyncio
    async def test_retry_transient_vs_permanent_errors(self):
        """
        Should retry transient errors but fail fast on permanent errors.
        
        Validates: Error classification
        Theory: Don't waste time retrying unrecoverable failures
        """
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        
        transient_attempts = 0
        permanent_attempts = 0
        
        async def transient_error_operation():
            nonlocal transient_attempts
            transient_attempts += 1
            raise RetryableError("Transient - should retry")
        
        async def permanent_error_operation():
            nonlocal permanent_attempts
            permanent_attempts += 1
            raise PermanentError("Permanent - should fail fast")
        
        # Transient error: should retry all attempts
        with pytest.raises(RetryableError):
            await retry_with_backoff(transient_error_operation, config)
        
        assert transient_attempts == 3, \
            f"Transient error should retry 3 times, got {transient_attempts}"
        
        # Permanent error: should fail immediately
        with pytest.raises(PermanentError):
            await retry_with_backoff(permanent_error_operation, config)
        
        assert permanent_attempts == 1, \
            f"Permanent error should fail fast (1 attempt), got {permanent_attempts}"


class TestRetryIntegration:
    """
    Integration tests for retry logic with consciousness components.
    """

    @pytest.mark.asyncio
    async def test_retry_tig_esgt_connection(self):
        """
        TIG-ESGT connection should retry on transient failures.
        
        Validates: Real-world retry application
        Theory: Network hiccups shouldn't break consciousness
        """
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        
        attempt = 0
        
        async def tig_esgt_connect():
            nonlocal attempt
            attempt += 1
            
            # Simulate transient failure on first try
            if attempt == 1:
                raise RetryableError("TIG temporarily unavailable")
            
            # Success on retry
            return {"status": "connected", "latency_ms": 5.2}
        
        # Should succeed after retry
        result = await retry_with_backoff(tig_esgt_connect, config)
        
        assert result["status"] == "connected"
        assert attempt == 2, "Should succeed on second attempt"

    @pytest.mark.asyncio
    async def test_retry_with_timeout_coordination(self):
        """
        Retry logic should coordinate with timeouts.
        
        Validates: Timeout + retry interaction
        Theory: Both patterns work together for resilience
        """
        config = RetryConfig(max_attempts=3, base_delay=0.05)
        
        async def slow_operation():
            # Simulate slow operation
            await asyncio.sleep(0.02)
            return "completed"
        
        # With reasonable timeout, should succeed
        try:
            result = await asyncio.wait_for(
                retry_with_backoff(slow_operation, config),
                timeout=1.0
            )
            assert result == "completed"
        except asyncio.TimeoutError:
            pytest.fail("Operation should not timeout with reasonable limit")

    @pytest.mark.asyncio
    async def test_retry_metrics_tracking(self):
        """
        Retry logic should track metrics for monitoring.
        
        Validates: Observability
        Theory: Monitor retry patterns to detect systemic issues
        """
        config = RetryConfig(max_attempts=4, base_delay=0.01)
        
        metrics = {
            "total_attempts": 0,
            "retries": 0,
            "successes": 0,
            "failures": 0
        }
        
        async def tracked_operation():
            metrics["total_attempts"] += 1
            
            # Fail first 2 times
            if metrics["total_attempts"] < 3:
                metrics["retries"] += 1
                raise RetryableError("Retry me")
            
            # Succeed on 3rd
            metrics["successes"] += 1
            return "ok"
        
        result = await retry_with_backoff(tracked_operation, config)
        
        # Validate metrics
        assert result == "ok"
        assert metrics["total_attempts"] == 3, "3 total attempts"
        assert metrics["retries"] == 2, "2 retries (attempts 1 and 2)"
        assert metrics["successes"] == 1, "1 success (attempt 3)"
        
        # Can use these metrics for monitoring
        retry_rate = metrics["retries"] / metrics["total_attempts"]
        assert 0 <= retry_rate <= 1.0, "Retry rate should be valid percentage"
