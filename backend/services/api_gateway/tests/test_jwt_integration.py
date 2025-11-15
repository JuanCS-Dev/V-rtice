"""
JWT Authentication Integration Tests
=====================================

Integration tests for JWT authentication endpoints in API Gateway.
Validates the complete authentication flow from login to protected endpoints.

Boris Cherny Pattern: Integration tests for critical security flows.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))

# Mock redis before importing main
with patch('redis.asyncio.from_url'):
    from main import app

client = TestClient(app)


# =============================================================================
# AUTHENTICATION FLOW TESTS
# =============================================================================

class TestAuthenticationFlow:
    """Test complete authentication flow."""

    def test_login_success(self):
        """User can login with valid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "user@example.com",
                "password": "user123",
                "tenant_id": "tenant-abc",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 3600

        # Verify user data
        assert data["user"]["user_id"] == "user-001"
        assert data["user"]["email"] == "user@example.com"
        assert data["user"]["tenant_id"] == "tenant-abc"
        assert "read:data" in data["user"]["scopes"]
        assert "write:data" in data["user"]["scopes"]

    def test_login_admin_user(self):
        """Admin user gets wildcard scope."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin@example.com",
                "password": "admin123",
                "tenant_id": "tenant-admin",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user"]["scopes"] == ["*"]

    def test_login_readonly_user(self):
        """Read-only user gets limited scope."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "readonly@example.com",
                "password": "readonly123",
                "tenant_id": "tenant-readonly",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user"]["scopes"] == ["read:data"]

    def test_login_invalid_credentials(self):
        """Invalid credentials are rejected."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "invalid@example.com",
                "password": "wrong",
                "tenant_id": "tenant-abc",
            },
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_missing_fields(self):
        """Missing required fields are rejected."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "user@example.com",
                # Missing password and tenant_id
            },
        )

        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]

    def test_complete_flow_login_access_refresh(self):
        """Complete flow: login → access protected endpoint → refresh token."""
        # Step 1: Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "user@example.com",
                "password": "user123",
                "tenant_id": "tenant-abc",
            },
        )

        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # Step 2: Access /api/auth/me with access token
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["user_id"] == "user-001"
        assert me_data["email"] == "user@example.com"
        assert me_data["tenant_id"] == "tenant-abc"

        # Step 3: Refresh access token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert refresh_data["token_type"] == "Bearer"

        # Step 4: Use new access token
        new_access_token = refresh_data["access_token"]
        me_response2 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )

        assert me_response2.status_code == 200


# =============================================================================
# PROTECTED ENDPOINT TESTS
# =============================================================================

class TestProtectedEndpoints:
    """Test protected endpoints with JWT authentication."""

    def setup_method(self):
        """Login before each test."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "user@example.com",
                "password": "user123",
                "tenant_id": "tenant-abc",
            },
        )
        self.access_token = response.json()["access_token"]

    def test_protected_endpoint_without_token(self):
        """Protected endpoint rejects requests without token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 403  # FastAPI HTTPBearer default

    def test_protected_endpoint_with_invalid_token(self):
        """Protected endpoint rejects invalid tokens."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self):
        """Protected endpoint allows valid tokens."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-001"

    def test_tenant_isolated_endpoint_correct_tenant(self):
        """Tenant-isolated endpoint allows same tenant."""
        response = client.get(
            "/api/auth/protected/tenant/tenant-abc/data",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "tenant-abc"
        assert "Sensitive data" in data["data"]

    def test_tenant_isolated_endpoint_wrong_tenant(self):
        """Tenant-isolated endpoint denies cross-tenant access."""
        response = client.get(
            "/api/auth/protected/tenant/tenant-xyz/data",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
        assert "tenant-abc" in response.json()["detail"]


# =============================================================================
# SCOPE AUTHORIZATION TESTS
# =============================================================================

class TestScopeAuthorization:
    """Test scope-based authorization."""

    def test_admin_endpoint_with_wildcard_scope(self):
        """Admin endpoint allows wildcard scope."""
        # Login as admin (has wildcard scope)
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin@example.com",
                "password": "admin123",
                "tenant_id": "tenant-admin",
            },
        )

        access_token = login_response.json()["access_token"]

        # Access admin endpoint
        response = client.get(
            "/api/auth/protected/admin",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "Welcome to admin area" in data["message"]

    def test_admin_endpoint_without_required_scope(self):
        """Admin endpoint denies users without admin scope."""
        # Login as regular user (no admin:access scope)
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "user@example.com",
                "password": "user123",
                "tenant_id": "tenant-abc",
            },
        )

        access_token = login_response.json()["access_token"]

        # Try to access admin endpoint
        response = client.get(
            "/api/auth/protected/admin",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 403
        assert "Missing required scope" in response.json()["detail"]
        assert "admin:access" in response.json()["detail"]


# =============================================================================
# TOKEN REFRESH TESTS
# =============================================================================

class TestTokenRefresh:
    """Test token refresh functionality."""

    def test_refresh_token_success(self):
        """Refresh token creates new access token."""
        # Login to get refresh token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "user@example.com",
                "password": "user123",
                "tenant_id": "tenant-abc",
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 3600

    def test_refresh_with_invalid_token(self):
        """Invalid refresh token is rejected."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]

    def test_refresh_with_missing_token(self):
        """Missing refresh token is rejected."""
        response = client.post(
            "/api/auth/refresh",
            json={},
        )

        assert response.status_code == 400
        assert "Missing refresh_token" in response.json()["detail"]

    def test_refresh_token_cannot_access_api(self):
        """Refresh tokens cannot be used for API access."""
        # Get refresh token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "user@example.com",
                "password": "user123",
                "tenant_id": "tenant-abc",
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Try to use refresh token for API access
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        assert response.status_code == 401
        assert "Refresh tokens cannot be used for API access" in response.json()["detail"]


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_authorization_header(self):
        """Malformed authorization header is rejected."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "NotBearer token"},
        )

        # FastAPI HTTPBearer expects "Bearer <token>" format
        assert response.status_code == 403

    def test_empty_authorization_header(self):
        """Empty authorization header is rejected."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": ""},
        )

        assert response.status_code == 403

    def test_login_with_empty_strings(self):
        """Empty string credentials are rejected."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "",
                "password": "",
                "tenant_id": "",
            },
        )

        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
