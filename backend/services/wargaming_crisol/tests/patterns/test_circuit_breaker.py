"""Tests for circuit breaker pattern - Phase 5.7.1"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.wargaming_crisol.patterns.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError
)


class TestCircuitBreakerBasics:
    """Test basic circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_initial_state_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful call keeps circuit CLOSED."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_single_failure_stays_closed(self):
        """Test single failure doesn't open circuit."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        async def fail_func():
            raise Exception("Test failure")
        
        with pytest.raises(Exception):
            await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_multiple_failures_open_circuit(self):
        """Test multiple failures open the circuit."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        async def fail_func():
            raise Exception("Test failure")
        
        # Fail 3 times to reach threshold
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_open_circuit_rejects_immediately(self):
        """Test OPEN circuit rejects without calling function."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)
        
        async def fail_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Next call should raise CircuitBreakerOpenError immediately
        call_count = 0
        
        async def tracked_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("Should not be called")
        
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(tracked_fail)
        
        # Function should not have been called
        assert call_count == 0


class TestCircuitBreakerRecovery:
    """Test circuit breaker recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self):
        """Test circuit transitions to HALF_OPEN after recovery timeout."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=timedelta(seconds=0.1)
        )
        
        async def fail_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Next call should transition to HALF_OPEN
        async def success_func():
            return "recovered"
        
        result = await breaker.call(success_func)
        assert result == "recovered"
        assert breaker.state == CircuitState.CLOSED  # Successful recovery
    
    @pytest.mark.asyncio
    async def test_failed_recovery_back_to_open(self):
        """Test failed recovery returns circuit to OPEN."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=timedelta(seconds=0.1)
        )
        
        async def fail_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Failed recovery attempt
        with pytest.raises(Exception):
            await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerTimeout:
    """Test circuit breaker timeout functionality."""
    
    @pytest.mark.asyncio
    async def test_timeout_counted_as_failure(self):
        """Test timeout is counted as failure."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout=timedelta(seconds=0.1)
        )
        
        async def slow_func():
            await asyncio.sleep(0.5)  # Longer than timeout
            return "too slow"
        
        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await breaker.call(slow_func)
        
        assert breaker.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_multiple_timeouts_open_circuit(self):
        """Test multiple timeouts open the circuit."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout=timedelta(seconds=0.1)
        )
        
        async def slow_func():
            await asyncio.sleep(0.5)
            return "too slow"
        
        # Timeout twice
        for _ in range(2):
            with pytest.raises(asyncio.TimeoutError):
                await breaker.call(slow_func)
        
        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerStatus:
    """Test circuit breaker status reporting."""
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test status reporting."""
        breaker = CircuitBreaker(name="test_service", failure_threshold=5)
        
        status = breaker.get_status()
        
        assert status["name"] == "test_service"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 5
        assert status["healthy"] is True
    
    @pytest.mark.asyncio
    async def test_status_after_failures(self):
        """Test status reflects failures."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        async def fail_func():
            raise Exception("Fail")
        
        # Fail twice
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        status = breaker.get_status()
        assert status["failure_count"] == 2
        assert status["state"] == "closed"  # Not yet open
        assert status["healthy"] is True
    
    @pytest.mark.asyncio
    async def test_status_when_open(self):
        """Test status when circuit is OPEN."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)
        
        async def fail_func():
            raise Exception("Fail")
        
        # Open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        status = breaker.get_status()
        assert status["state"] == "open"
        assert status["healthy"] is False


class TestCircuitBreakerManualReset:
    """Test manual reset functionality."""
    
    @pytest.mark.asyncio
    async def test_manual_reset(self):
        """Test manual reset of circuit breaker."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)
        
        async def fail_func():
            raise Exception("Fail")
        
        # Open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Manual reset
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_reset_allows_immediate_retry(self):
        """Test reset allows immediate retry without waiting."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=timedelta(seconds=100)  # Long timeout
        )
        
        async def fail_func():
            raise Exception("Fail")
        
        # Open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Would normally need to wait 100s, but reset allows immediate retry
        breaker.reset()
        
        async def success_func():
            return "works"
        
        result = await breaker.call(success_func)
        assert result == "works"
