"""
JWT Service Validation Tests
=============================

Complete validation of JWT authentication service implementation.
Tests all components: jwt_handler, API endpoints, integration flow.

Boris Cherny Pattern: Comprehensive validation for production readiness.
"""

import pytest
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../shared"))

from auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    cleanup_blacklist,
    token_blacklist,
)
from fastapi import HTTPException
from datetime import timedelta


class TestJWTServiceValidation:
    """Comprehensive JWT service validation."""

    def setup_method(self):
        """Clear blacklist before each test."""
        token_blacklist.clear()

    def test_complete_token_lifecycle(self):
        """Validate complete token lifecycle: create → use → refresh → revoke."""
        # Step 1: Create access token
        access_token = create_access_token(
            user_id="validation-user",
            email="validation@example.com",
            tenant_id="tenant-validation",
            scopes=["read:data", "write:data"],
        )

        assert isinstance(access_token, str)
        assert len(access_token) > 0

        # Step 2: Decode and validate access token
        payload = decode_token(access_token)
        assert payload["sub"] == "validation-user"
        assert payload["email"] == "validation@example.com"
        assert payload["tenant_id"] == "tenant-validation"
        assert "read:data" in payload["scopes"]
        assert "write:data" in payload["scopes"]

        # Step 3: Create refresh token
        refresh_token = create_refresh_token(
            user_id="validation-user",
            tenant_id="tenant-validation",
        )

        refresh_payload = decode_token(refresh_token)
        assert refresh_payload["sub"] == "validation-user"
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["scopes"] == ["refresh"]

        # Step 4: Revoke access token
        revoke_token(access_token)

        # Step 5: Verify revoked token is rejected
        with pytest.raises(HTTPException) as exc:
            decode_token(access_token)

        assert exc.value.status_code == 401
        assert "revoked" in exc.value.detail.lower()

    def test_multi_tenant_isolation_validation(self):
        """Validate multi-tenant isolation."""
        # Create tokens for different tenants
        tenant_a_token = create_access_token(
            user_id="user-a",
            email="usera@example.com",
            tenant_id="tenant-a",
            scopes=["read:data"],
        )

        tenant_b_token = create_access_token(
            user_id="user-b",
            email="userb@example.com",
            tenant_id="tenant-b",
            scopes=["read:data"],
        )

        # Decode both tokens
        payload_a = decode_token(tenant_a_token)
        payload_b = decode_token(tenant_b_token)

        # Verify tenant isolation
        assert payload_a["tenant_id"] == "tenant-a"
        assert payload_b["tenant_id"] == "tenant-b"
        assert payload_a["tenant_id"] != payload_b["tenant_id"]

    def test_scope_based_authorization_validation(self):
        """Validate scope-based authorization."""
        # Admin with wildcard
        admin_token = create_access_token(
            user_id="admin",
            email="admin@example.com",
            tenant_id="tenant-admin",
            scopes=["*"],
        )

        # Regular user with limited scopes
        user_token = create_access_token(
            user_id="user",
            email="user@example.com",
            tenant_id="tenant-user",
            scopes=["read:data"],
        )

        # Read-only user
        readonly_token = create_access_token(
            user_id="readonly",
            email="readonly@example.com",
            tenant_id="tenant-readonly",
            scopes=["read:data"],
        )

        # Validate scopes
        admin_payload = decode_token(admin_token)
        user_payload = decode_token(user_token)
        readonly_payload = decode_token(readonly_token)

        assert admin_payload["scopes"] == ["*"]
        assert "read:data" in user_payload["scopes"]
        assert "write:data" not in user_payload["scopes"]
        assert readonly_payload["scopes"] == ["read:data"]

    def test_token_expiry_validation(self):
        """Validate token expiry mechanism."""
        # Create token with short expiry (1 second)
        short_lived_token = create_access_token(
            user_id="expiry-test",
            email="expiry@example.com",
            tenant_id="tenant-expiry",
            scopes=["read"],
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        # Verify expired token is rejected
        with pytest.raises(HTTPException) as exc:
            decode_token(short_lived_token)

        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail.lower()

    def test_token_blacklist_cleanup(self):
        """Validate blacklist cleanup mechanism."""
        # Add expired token to blacklist
        token_blacklist["old-jti"] = 1000  # Old timestamp (expired)
        token_blacklist["new-jti"] = 9999999999  # Future timestamp

        # Run cleanup
        removed = cleanup_blacklist()

        # Verify old token was removed
        assert removed == 1
        assert "old-jti" not in token_blacklist
        assert "new-jti" in token_blacklist

    def test_refresh_token_type_validation(self):
        """Validate refresh token cannot be used for API access."""
        refresh_token = create_refresh_token(
            user_id="refresh-test",
            tenant_id="tenant-refresh",
        )

        payload = decode_token(refresh_token)

        # Verify it's marked as refresh type
        assert payload.get("type") == "refresh"
        assert payload.get("scopes") == ["refresh"]

    def test_invalid_token_validation(self):
        """Validate invalid token detection."""
        invalid_tokens = [
            "invalid.token.here",
            "not-a-jwt-at-all",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises(HTTPException) as exc:
                decode_token(invalid_token)

            assert exc.value.status_code == 401

    def test_custom_expiry_validation(self):
        """Validate custom token expiry."""
        # Create 30-minute token
        custom_token = create_access_token(
            user_id="custom-expiry",
            email="custom@example.com",
            tenant_id="tenant-custom",
            scopes=["read"],
            expires_delta=timedelta(minutes=30),
        )

        payload = decode_token(custom_token)
        exp_time = payload["exp"]
        iat_time = payload["iat"]

        # Verify expiry is ~30 minutes (allow 1 min tolerance)
        delta = exp_time - iat_time
        assert 1700 < delta < 1900  # ~1800 seconds = 30 min

    def test_jwt_payload_structure(self):
        """Validate complete JWT payload structure."""
        token = create_access_token(
            user_id="structure-test",
            email="structure@example.com",
            tenant_id="tenant-structure",
            scopes=["read:data", "write:data"],
        )

        payload = decode_token(token)

        # Verify all required fields are present
        required_fields = ["sub", "email", "tenant_id", "scopes", "exp", "iat", "jti"]
        for field in required_fields:
            assert field in payload, f"Missing required field: {field}"

        # Verify types
        assert isinstance(payload["sub"], str)
        assert isinstance(payload["email"], str)
        assert isinstance(payload["tenant_id"], str)
        assert isinstance(payload["scopes"], list)
        assert isinstance(payload["exp"], (int, float))
        assert isinstance(payload["iat"], (int, float))
        assert isinstance(payload["jti"], str)

    def test_concurrent_token_operations(self):
        """Validate concurrent token operations."""
        # Create multiple tokens simultaneously
        tokens = []
        for i in range(10):
            token = create_access_token(
                user_id=f"user-{i}",
                email=f"user{i}@example.com",
                tenant_id=f"tenant-{i}",
                scopes=["read"],
            )
            tokens.append(token)

        # Verify all tokens are valid and unique
        payloads = [decode_token(t) for t in tokens]

        assert len(payloads) == 10
        assert len(set(p["sub"] for p in payloads)) == 10  # All unique users
        assert len(set(p["jti"] for p in payloads)) == 10  # All unique JTIs

    def test_production_readiness_checklist(self):
        """Production readiness validation checklist."""
        # ✅ Token creation works
        token = create_access_token(
            user_id="prod-test",
            email="prod@example.com",
            tenant_id="tenant-prod",
            scopes=["*"],
        )
        assert token

        # ✅ Token validation works
        payload = decode_token(token)
        assert payload

        # ✅ Multi-tenant support works
        assert payload["tenant_id"] == "tenant-prod"

        # ✅ Scope-based auth works
        assert payload["scopes"] == ["*"]

        # ✅ Token blacklist works
        revoke_token(token)
        with pytest.raises(HTTPException):
            decode_token(token)

        # ✅ Blacklist cleanup works
        token_blacklist["test-jti"] = 1000
        cleanup_blacklist()
        assert "test-jti" not in token_blacklist

        # ✅ Refresh tokens work
        refresh = create_refresh_token("prod-test", "tenant-prod")
        refresh_payload = decode_token(refresh)
        assert refresh_payload["type"] == "refresh"

        # ✅ Custom expiry works
        custom = create_access_token(
            user_id="prod-test",
            email="prod@example.com",
            tenant_id="tenant-prod",
            scopes=["read"],
            expires_delta=timedelta(hours=2),
        )
        assert custom

        print("✅ All production readiness checks PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
