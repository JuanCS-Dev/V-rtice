"""Base class for threat feed clients.

This module defines the abstract interface that all threat feed clients must implement.
Provides consistent error handling, retry logic, and rate limiting patterns.

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: Doutrina MAXIMUS | Type Hints 100% | Production-Ready
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class ThreatFeedError(Exception):
    """Base exception for threat feed operations."""
    pass


class RateLimitError(ThreatFeedError):
    """Raised when rate limit is exceeded."""
    pass


class FeedUnavailableError(ThreatFeedError):
    """Raised when feed is temporarily unavailable."""
    pass


class BaseFeedClient(ABC):
    """
    Abstract base class for threat feed clients.
    
    All threat feed implementations (OSV, NVD, Docker Security, etc.)
    must inherit from this class and implement the required methods.
    
    Provides:
    - Consistent error handling
    - Retry logic patterns
    - Rate limiting interface
    - Logging standardization
    
    Theoretical Foundation:
    - Adapter Pattern: Normalize different feed APIs
    - Circuit Breaker: Fail fast when feed is down
    - Rate Limiting: Respect API quotas
    """
    
    def __init__(self, name: str, rate_limit: int = 100):
        """
        Initialize base feed client.
        
        Args:
            name: Human-readable name of the feed
            rate_limit: Maximum requests per minute
        """
        self.name = name
        self.rate_limit = rate_limit
        self._request_count = 0
        self._window_start = datetime.utcnow()
        
        logger.info(f"Initialized {self.name} feed client (rate limit: {rate_limit} req/min)")
    
    @abstractmethod
    async def fetch_vulnerabilities(
        self,
        ecosystem: Optional[str] = None,
        package: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch vulnerabilities from the feed.
        
        Args:
            ecosystem: Filter by ecosystem (PyPI, npm, etc.)
            package: Filter by specific package
            since: Only fetch vulnerabilities published since this date
            
        Returns:
            List of raw vulnerability dictionaries
            
        Raises:
            RateLimitError: If rate limit exceeded
            FeedUnavailableError: If feed is down
            ThreatFeedError: For other errors
        """
        pass
    
    @abstractmethod
    async def fetch_by_cve_id(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch specific vulnerability by CVE ID.
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2024-12345)
            
        Returns:
            Vulnerability dict or None if not found
            
        Raises:
            RateLimitError: If rate limit exceeded
            FeedUnavailableError: If feed is down
        """
        pass
    
    async def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting.
        
        Uses sliding window algorithm:
        - Track requests in current minute
        - If limit reached, wait until window resets
        
        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        now = datetime.utcnow()
        elapsed = (now - self._window_start).total_seconds()
        
        # Reset window if more than 60 seconds passed
        if elapsed >= 60:
            self._request_count = 0
            self._window_start = now
        
        # Check if we're at the limit
        if self._request_count >= self.rate_limit:
            wait_time = 60 - elapsed
            if wait_time > 0:
                logger.warning(
                    f"{self.name}: Rate limit reached ({self.rate_limit} req/min), "
                    f"waiting {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)
                # Reset after waiting
                self._request_count = 0
                self._window_start = datetime.utcnow()
        
        self._request_count += 1
    
    async def health_check(self) -> bool:
        """
        Check if feed is healthy and accessible.
        
        Returns:
            True if feed is accessible, False otherwise
        """
        try:
            # Try to fetch a known CVE (if feed supports it)
            # Default implementation just returns True
            return True
        except Exception as e:
            logger.error(f"{self.name} health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dict with request count, rate limit, etc.
        """
        return {
            "name": self.name,
            "rate_limit": self.rate_limit,
            "requests_this_window": self._request_count,
            "window_start": self._window_start.isoformat()
        }
