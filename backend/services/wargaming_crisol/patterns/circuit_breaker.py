"""
Circuit breaker pattern for external service calls.

Protects against cascading failures when ML model or database is slow/down.
Inspired by immune system's ability to prevent cytokine storm and
excessive inflammation response.

States:
- CLOSED: Normal operation (healthy)
- OPEN: Failing, reject immediately (circuit tripped)
- HALF_OPEN: Testing if recovered (cautious recovery)

Biological Analogy:
CLOSED = Immune tolerance (normal state)
OPEN = Anergy (shutdown to prevent autoimmunity)
HALF_OPEN = Regulatory T-cell mediated recovery
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"               # Failing, reject requests
    HALF_OPEN = "half_open"     # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    Prevents cascading failures by fast-failing when service is degraded.
    Similar to immune system's regulatory mechanisms that prevent
    excessive inflammation.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: timedelta = timedelta(seconds=60),
        recovery_timeout: timedelta = timedelta(seconds=30)
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker identifier (for logging)
            failure_threshold: Number of failures before opening
            timeout: Max time to wait for operation
            recovery_timeout: Time to wait before attempting recovery
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_attempt_time: Optional[datetime] = None
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            asyncio.TimeoutError: If operation times out
            Exception: Original exception from function
        """
        
        if self.state == CircuitState.OPEN:
            # Check if we should try half-open
            if (datetime.now() - self.last_failure_time) > self.recovery_timeout:
                logger.info(
                    f"Circuit breaker '{self.name}': Attempting recovery (HALF_OPEN)"
                )
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' OPEN - service unavailable. "
                    f"Retry after {self.recovery_timeout.total_seconds()}s"
                )
        
        try:
            # Execute with timeout
            self.last_attempt_time = datetime.now()
            
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout.total_seconds()
            )
            
            # Success - update state
            self._record_success()
            
            return result
        
        except asyncio.TimeoutError:
            logger.warning(
                f"Circuit breaker '{self.name}': Timeout after "
                f"{self.timeout.total_seconds()}s"
            )
            self._record_failure()
            raise
        
        except Exception as e:
            logger.warning(
                f"Circuit breaker '{self.name}': Exception - {type(e).__name__}: {e}"
            )
            self._record_failure()
            raise
    
    def _record_success(self) -> None:
        """Record successful operation and update state."""
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Recovery successful
            logger.info(
                f"Circuit breaker '{self.name}': Recovery successful (CLOSED)"
            )
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Successful operation in normal state
            # Gradually reduce failure count (forgiveness mechanism)
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
    
    def _record_failure(self) -> None:
        """Record failure and update state."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker '{self.name}': OPENED after "
                    f"{self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
        
        elif self.state == CircuitState.HALF_OPEN:
            # Recovery failed, back to OPEN
            logger.error(
                f"Circuit breaker '{self.name}': Recovery failed, back to OPEN"
            )
            self.state = CircuitState.OPEN
            self.success_count = 0
    
    def get_status(self) -> dict:
        """
        Get circuit breaker status for monitoring.
        
        Returns:
            Dict with current state and statistics
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "last_failure": (
                self.last_failure_time.isoformat() 
                if self.last_failure_time else None
            ),
            "last_attempt": (
                self.last_attempt_time.isoformat()
                if self.last_attempt_time else None
            ),
            "healthy": self.state == CircuitState.CLOSED
        }
    
    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(f"Circuit breaker '{self.name}': Manual reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


# Global circuit breakers for different services
ml_model_breaker = CircuitBreaker(
    name="ml_model",
    failure_threshold=5,
    timeout=timedelta(seconds=10),
    recovery_timeout=timedelta(seconds=30)
)

database_breaker = CircuitBreaker(
    name="database",
    failure_threshold=3,
    timeout=timedelta(seconds=5),
    recovery_timeout=timedelta(seconds=15)
)

cache_breaker = CircuitBreaker(
    name="redis_cache",
    failure_threshold=5,
    timeout=timedelta(seconds=3),
    recovery_timeout=timedelta(seconds=10)
)
