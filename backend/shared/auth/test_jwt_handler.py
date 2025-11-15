"""
JWT Handler Tests
=================

Comprehensive test suite for JWT authentication.
Target: 100% coverage for security-critical code.

Boris Cherny Pattern: Security code must have exhaustive tests.
"""

import pytest
import time
from datetime import timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_scope,
    require_tenant,
    revoke_token,
    cleanup_blacklist,
    token_blacklist,
)


# =============================================================================
# TOKEN CREATION TESTS
# =============================================================================

class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Access token is created with correct claims."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read:data", "write:data"],
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode to verify claims
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["tenant_id"] == "tenant-abc"
        assert payload["scopes"] == ["read:data", "write:data"]
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_create_refresh_token(self):
        """Refresh token is created with refresh scope."""
        token = create_refresh_token(
            user_id="user123",
            tenant_id="tenant-abc",
        )

        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["tenant_id"] == "tenant-abc"
        assert payload["scopes"] == ["refresh"]
        assert payload["type"] == "refresh"

    def test_custom_expiry(self):
        """Custom expiry time is respected."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
            expires_delta=timedelta(minutes=30),
        )

        payload = decode_token(token)
        exp_time = payload["exp"]
        iat_time = payload["iat"]

        # Should expire in ~30 minutes (allow 1 min tolerance)
        delta = exp_time - iat_time
        assert 1700 < delta < 1900  # ~1800 seconds = 30 min


# =============================================================================
# TOKEN VALIDATION TESTS
# =============================================================================

class TestTokenValidation:
    """Test JWT token validation."""

    def setup_method(self):
        """Clear blacklist before each test."""
        token_blacklist.clear()

    def test_decode_valid_token(self):
        """Valid tokens are decoded successfully."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
        )

        payload = decode_token(token)
        assert payload["sub"] == "user123"

    def test_decode_expired_token(self):
        """Expired tokens are rejected."""
        # Create token that expires immediately
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        with pytest.raises(HTTPException) as exc:
            decode_token(token)

        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail.lower()

    def test_decode_invalid_token(self):
        """Invalid tokens are rejected."""
        with pytest.raises(HTTPException) as exc:
            decode_token("invalid.token.string")

        assert exc.value.status_code == 401
        assert "invalid" in exc.value.detail.lower()

    def test_decode_revoked_token(self):
        """Revoked tokens are rejected."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
        )

        # Revoke token
        revoke_token(token)

        # Should be rejected
        with pytest.raises(HTTPException) as exc:
            decode_token(token)

        assert exc.value.status_code == 401
        assert "revoked" in exc.value.detail.lower()


# =============================================================================
# DEPENDENCY TESTS
# =============================================================================

class TestDependencies:
    """Test FastAPI dependencies."""

    def setup_method(self):
        """Clear blacklist before each test."""
        token_blacklist.clear()

    @pytest.mark.asyncio
    async def test_get_current_user(self):
        """get_current_user extracts user from valid token."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        user = await get_current_user(credentials)

        assert user["sub"] == "user123"
        assert user["email"] == "test@example.com"
        assert user["tenant_id"] == "tenant-abc"

    @pytest.mark.asyncio
    async def test_get_current_user_refresh_token_rejected(self):
        """Refresh tokens are rejected for API access."""
        token = create_refresh_token("user123", "tenant-abc")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials)

        assert exc.value.status_code == 401
        assert "refresh" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_scope_allowed(self):
        """Users with required scope are allowed."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read:data", "write:data"],
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        # Mock get_current_user
        async def mock_get_current_user():
            return decode_token(token)

        # Create dependency
        dependency = require_scope("read:data")

        # Should pass
        user = await dependency(await mock_get_current_user())
        assert user["sub"] == "user123"

    @pytest.mark.asyncio
    async def test_require_scope_denied(self):
        """Users without required scope are denied."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read:data"],  # Missing write:data
        )

        user_data = decode_token(token)

        dependency = require_scope("write:data")

        with pytest.raises(HTTPException) as exc:
            await dependency(user_data)

        assert exc.value.status_code == 403
        assert "scope" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_scope_wildcard(self):
        """Users with wildcard scope have all permissions."""
        token = create_access_token(
            user_id="admin",
            email="admin@example.com",
            tenant_id="tenant-abc",
            scopes=["*"],  # Wildcard
        )

        user_data = decode_token(token)

        dependency = require_scope("any:permission")
        user = await dependency(user_data)

        assert user["sub"] == "admin"

    @pytest.mark.asyncio
    async def test_require_tenant_allowed(self):
        """Users in correct tenant are allowed."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
        )

        user_data = decode_token(token)

        dependency = require_tenant("tenant-abc")
        user = await dependency(user_data)

        assert user["tenant_id"] == "tenant-abc"

    @pytest.mark.asyncio
    async def test_require_tenant_denied(self):
        """Users from wrong tenant are denied."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
        )

        user_data = decode_token(token)

        dependency = require_tenant("tenant-xyz")

        with pytest.raises(HTTPException) as exc:
            await dependency(user_data)

        assert exc.value.status_code == 403
        assert "tenant" in exc.value.detail.lower()


# =============================================================================
# BLACKLIST TESTS
# =============================================================================

class TestBlacklist:
    """Test token blacklist functionality."""

    def setup_method(self):
        """Clear blacklist before each test."""
        token_blacklist.clear()

    def test_revoke_token(self):
        """Tokens are added to blacklist."""
        token = create_access_token(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant-abc",
            scopes=["read"],
        )

        # Initially valid
        payload = decode_token(token)
        assert payload["sub"] == "user123"

        # Revoke
        revoke_token(token)

        # Now invalid
        with pytest.raises(HTTPException) as exc:
            decode_token(token)

        assert exc.value.status_code == 401

    def test_cleanup_blacklist(self):
        """Expired tokens are removed from blacklist."""
        # Add expired token to blacklist
        token_blacklist["jti-old"] = time.time() - 1000  # Expired
        token_blacklist["jti-new"] = time.time() + 1000  # Not expired

        removed = cleanup_blacklist()

        assert removed == 1
        assert "jti-old" not in token_blacklist
        assert "jti-new" in token_blacklist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
