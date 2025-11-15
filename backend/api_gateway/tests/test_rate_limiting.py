"""
Tests for User-Based Rate Limiting

DOUTRINA VÉRTICE - GAP #13 (P2)
Tests for user-based rate limiting middleware

Following Boris Cherny: "Tests or it didn't happen"
"""

import jwt
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from middleware.rate_limiting import (
    get_user_identifier,
    user_rate_limit,
    is_user_authenticated,
    get_rate_limit_key,
    JWT_SECRET,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()

    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}

    @app.get("/protected")
    @user_rate_limit("5/minute")
    async def protected_endpoint():
        return {"message": "protected"}

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_request():
    """Create mock request object."""
    request = MagicMock(spec=Request)
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "192.168.1.1"
    return request


@pytest.fixture
def valid_token():
    """Create valid JWT token."""
    return jwt.encode(
        {"sub": "user123", "name": "Test User"},
        JWT_SECRET,
        algorithm="HS256"
    )


@pytest.fixture
def expired_token():
    """Create expired JWT token."""
    import time
    return jwt.encode(
        {"sub": "user123", "exp": int(time.time()) - 3600},  # Expired 1 hour ago
        JWT_SECRET,
        algorithm="HS256"
    )


# ============================================================================
# TESTS: get_user_identifier
# ============================================================================

def test_get_user_identifier_with_valid_token(mock_request, valid_token):
    """Should return user ID when valid token provided."""
    mock_request.headers = {"Authorization": f"Bearer {valid_token}"}

    identifier = get_user_identifier(mock_request)

    assert identifier == "user:user123"


def test_get_user_identifier_with_expired_token(mock_request, expired_token):
    """Should return user ID even with expired token (rate limit still applies)."""
    mock_request.headers = {"Authorization": f"Bearer {expired_token}"}

    identifier = get_user_identifier(mock_request)

    # Expired tokens still get user-based rate limiting
    assert identifier == "user:user123"


def test_get_user_identifier_with_invalid_token(mock_request):
    """Should fallback to IP when token is invalid."""
    mock_request.headers = {"Authorization": "Bearer invalid_token"}

    identifier = get_user_identifier(mock_request)

    assert identifier == "ip:192.168.1.1"


def test_get_user_identifier_without_token(mock_request):
    """Should use IP address when no token provided."""
    identifier = get_user_identifier(mock_request)

    assert identifier == "ip:192.168.1.1"


def test_get_user_identifier_with_malformed_header(mock_request):
    """Should fallback to IP with malformed Authorization header."""
    mock_request.headers = {"Authorization": "InvalidFormat token"}

    identifier = get_user_identifier(mock_request)

    assert identifier == "ip:192.168.1.1"


# ============================================================================
# TESTS: is_user_authenticated
# ============================================================================

def test_is_user_authenticated_with_valid_token(mock_request, valid_token):
    """Should return True when user is authenticated."""
    mock_request.headers = {"Authorization": f"Bearer {valid_token}"}

    assert is_user_authenticated(mock_request) is True


def test_is_user_authenticated_without_token(mock_request):
    """Should return False when user is not authenticated."""
    assert is_user_authenticated(mock_request) is False


def test_is_user_authenticated_with_invalid_token(mock_request):
    """Should return False when token is invalid."""
    mock_request.headers = {"Authorization": "Bearer invalid_token"}

    assert is_user_authenticated(mock_request) is False


# ============================================================================
# TESTS: get_rate_limit_key
# ============================================================================

def test_get_rate_limit_key_for_authenticated_user(mock_request, valid_token):
    """Should return user:ID key for authenticated users."""
    mock_request.headers = {"Authorization": f"Bearer {valid_token}"}

    key = get_rate_limit_key(mock_request)

    assert key == "user:user123"


def test_get_rate_limit_key_for_anonymous_user(mock_request):
    """Should return ip:ADDRESS key for anonymous users."""
    key = get_rate_limit_key(mock_request)

    assert key == "ip:192.168.1.1"


# ============================================================================
# TESTS: Integration (would require Redis)
# ============================================================================

def test_public_endpoint_accessible(client):
    """Public endpoint should be accessible without rate limiting."""
    response = client.get("/public")

    assert response.status_code == 200
    assert response.json() == {"message": "public"}


# Note: Full integration tests would require Redis instance
# These tests verify the identifier logic, not the actual rate limiting


# ============================================================================
# TESTS: Different Users Get Separate Limits
# ============================================================================

def test_different_users_have_separate_limits():
    """Each authenticated user should have their own rate limit bucket."""
    # Create two different tokens
    token1 = jwt.encode({"sub": "user1"}, JWT_SECRET, algorithm="HS256")
    token2 = jwt.encode({"sub": "user2"}, JWT_SECRET, algorithm="HS256")

    # Create mock requests for each user
    request1 = MagicMock(spec=Request)
    request1.headers = {"Authorization": f"Bearer {token1}"}
    request1.client = MagicMock()
    request1.client.host = "192.168.1.1"

    request2 = MagicMock(spec=Request)
    request2.headers = {"Authorization": f"Bearer {token2}"}
    request2.client = MagicMock()
    request2.client.host = "192.168.1.1"  # Same IP!

    id1 = get_user_identifier(request1)
    id2 = get_user_identifier(request2)

    # Different users should get different rate limit keys
    assert id1 == "user:user1"
    assert id2 == "user:user2"
    assert id1 != id2


def test_anonymous_users_from_different_ips_have_separate_limits():
    """Anonymous users from different IPs should have separate limits."""
    request1 = MagicMock(spec=Request)
    request1.headers = {}
    request1.client = MagicMock()
    request1.client.host = "192.168.1.1"

    request2 = MagicMock(spec=Request)
    request2.headers = {}
    request2.client = MagicMock()
    request2.client.host = "192.168.1.2"

    id1 = get_user_identifier(request1)
    id2 = get_user_identifier(request2)

    assert id1 == "ip:192.168.1.1"
    assert id2 == "ip:192.168.1.2"
    assert id1 != id2


def test_user_cannot_bypass_limit_by_changing_ip():
    """Authenticated user should have same limit regardless of IP."""
    token = jwt.encode({"sub": "user123"}, JWT_SECRET, algorithm="HS256")

    # Same user from two different IPs
    request1 = MagicMock(spec=Request)
    request1.headers = {"Authorization": f"Bearer {token}"}
    request1.client = MagicMock()
    request1.client.host = "192.168.1.1"

    request2 = MagicMock(spec=Request)
    request2.headers = {"Authorization": f"Bearer {token}"}
    request2.client = MagicMock()
    request2.client.host = "10.0.0.1"  # Different IP!

    id1 = get_user_identifier(request1)
    id2 = get_user_identifier(request2)

    # Same user gets same rate limit key regardless of IP
    assert id1 == "user:user123"
    assert id2 == "user:user123"
    assert id1 == id2


# ============================================================================
# TESTS: Security Edge Cases
# ============================================================================

def test_cannot_impersonate_user_with_fake_sub():
    """Invalid tokens should not allow user impersonation."""
    # Attempt to create token with different user ID using wrong secret
    fake_token = jwt.encode(
        {"sub": "admin"},
        "wrong_secret",  # Wrong secret!
        algorithm="HS256"
    )

    request = MagicMock(spec=Request)
    request.headers = {"Authorization": f"Bearer {fake_token}"}
    request.client = MagicMock()
    request.client.host = "192.168.1.1"

    identifier = get_user_identifier(request)

    # Should fallback to IP-based (not user-based)
    assert identifier == "ip:192.168.1.1"
    assert not identifier.startswith("user:")


def test_empty_authorization_header():
    """Empty Authorization header should fallback to IP."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": ""}
    request.client = MagicMock()
    request.client.host = "192.168.1.1"

    identifier = get_user_identifier(request)

    assert identifier == "ip:192.168.1.1"


def test_bearer_without_token():
    """'Bearer ' without token should fallback to IP."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer "}
    request.client = MagicMock()
    request.client.host = "192.168.1.1"

    identifier = get_user_identifier(request)

    assert identifier == "ip:192.168.1.1"
