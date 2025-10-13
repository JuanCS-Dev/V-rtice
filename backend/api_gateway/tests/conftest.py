"""
API Gateway - Test Configuration.

Shared fixtures and configuration for API Gateway tests.
"""

import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock external dependencies before any imports
@pytest.fixture(scope="session", autouse=True)
def mock_external_services():
    """
    Mock external service dependencies for gateway tests.
    
    Mocks:
    - Redis (optional dependency)
    - Active Immune Core (external service)
    - Other microservices
    
    Returns:
        Dictionary of mock objects
    """
    mocks = {
        "redis": MagicMock(),
        "active_immune_core": AsyncMock(),
    }
    
    # Redis mock
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis_client.setex = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        mocks["redis"] = mock_redis_client
        
        yield mocks


@pytest.fixture
def mock_httpx_client():
    """
    Mock httpx.AsyncClient for testing external service calls.
    
    Returns:
        Mock httpx client with common response patterns
    """
    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        mock_context.get = AsyncMock()
        mock_context.post = AsyncMock()
        mock_context.request = AsyncMock()
        
        yield mock_context


@pytest.fixture
def mock_jwt_token():
    """
    Generate mock JWT token for authentication tests.
    
    Returns:
        Valid JWT token string
    """
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "sub": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "permissions": ["read", "write"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, "vertice-super-secret-key-2024", algorithm="HS256")
    return token


@pytest.fixture
def authorized_headers(mock_jwt_token):
    """
    Generate authorization headers for authenticated requests.
    
    Args:
        mock_jwt_token: JWT token fixture
    
    Returns:
        Dictionary with Authorization header
    """
    return {
        "Authorization": f"Bearer {mock_jwt_token}"
    }
