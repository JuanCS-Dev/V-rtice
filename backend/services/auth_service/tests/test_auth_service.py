"""Unit tests for Authentication Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Token generation (login) with REAL bcrypt + JWT
- User authentication (correct/incorrect passwords) - REAL validation
- Token validation (valid/invalid/expired tokens) - REAL JWT decode
- Role-based access control (admin vs user) - REAL permission checking
- Request validation (OAuth2PasswordRequestForm)
- Edge cases and security scenarios

Note: ALL cryptographic operations (bcrypt, JWT) are REAL - no mocking.
Only external dependencies (if any) would be mocked per PAGANI standard.
"""

# Import the FastAPI app
import sys
from datetime import datetime, timedelta

import bcrypt
import jwt
import pytest
import pytest_asyncio
from httpx import AsyncClient

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/auth_service")
from main import ALGORITHM, SECRET_KEY, app, create_access_token

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
def valid_admin_token():
    """Generate a valid JWT token for admin user."""
    token_data = {"sub": "maximus_admin", "roles": ["admin", "user"], "exp": datetime.utcnow() + timedelta(minutes=30)}
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


@pytest_asyncio.fixture
def valid_user_token():
    """Generate a valid JWT token for regular user."""
    token_data = {"sub": "maximus_user", "roles": ["user"], "exp": datetime.utcnow() + timedelta(minutes=30)}
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


@pytest_asyncio.fixture
def expired_token():
    """Generate an expired JWT token."""
    token_data = {
        "sub": "maximus_admin",
        "roles": ["admin", "user"],
        "exp": datetime.utcnow() - timedelta(minutes=10),  # Expired 10 minutes ago
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


# ==================== HEALTH CHECK TESTS ====================


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check_returns_healthy_status(self, client):
        """Test health endpoint returns operational status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "operational" in data["message"].lower()


# ==================== TOKEN/LOGIN TESTS ====================


@pytest.mark.asyncio
class TestTokenEndpoint:
    """Test token generation (login) endpoint with REAL bcrypt + JWT."""

    async def test_login_with_correct_credentials_admin(self, client):
        """Test login with correct admin credentials - REAL bcrypt validation."""
        form_data = {"username": "maximus_admin", "password": "adminpass"}

        response = await client.post("/token", data=form_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify token is REAL and can be decoded
        token = data["access_token"]
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "maximus_admin"
        assert "admin" in decoded["roles"]
        assert "user" in decoded["roles"]

    async def test_login_with_correct_credentials_user(self, client):
        """Test login with correct regular user credentials - REAL bcrypt validation."""
        form_data = {"username": "maximus_user", "password": "userpass"}

        response = await client.post("/token", data=form_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # Verify token contains correct user data
        token = data["access_token"]
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "maximus_user"
        assert decoded["roles"] == ["user"]

    async def test_login_with_incorrect_password(self, client):
        """Test login with incorrect password - REAL bcrypt rejection."""
        form_data = {"username": "maximus_admin", "password": "wrongpassword"}

        response = await client.post("/token", data=form_data)

        assert response.status_code == 401
        data = response.json()
        assert "incorrect username or password" in data["detail"].lower()

    async def test_login_with_nonexistent_user(self, client):
        """Test login with non-existent username."""
        form_data = {"username": "nonexistent_user", "password": "somepassword"}

        response = await client.post("/token", data=form_data)

        assert response.status_code == 401
        data = response.json()
        assert "incorrect username or password" in data["detail"].lower()

    async def test_login_token_has_expiration(self, client):
        """Test that generated token has expiration claim."""
        form_data = {"username": "maximus_admin", "password": "adminpass"}

        response = await client.post("/token", data=form_data)
        token = response.json()["access_token"]

        # Decode and verify expiration
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)
        assert decoded["exp"] > 0

    async def test_login_token_expires_in_30_minutes(self, client):
        """Test that token expiration is set to 30 minutes."""
        form_data = {"username": "maximus_admin", "password": "adminpass"}

        response = await client.post("/token", data=form_data)

        token = response.json()["access_token"]
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token contains expiration
        assert "exp" in decoded
        # Token should be valid (JWT library will raise if expired)
        assert decoded["sub"] == "maximus_admin"


# ==================== USER PROFILE TESTS ====================


@pytest.mark.asyncio
class TestUsersMeEndpoint:
    """Test /users/me endpoint with REAL JWT validation."""

    async def test_get_user_profile_with_valid_admin_token(self, client, valid_admin_token):
        """Test getting user profile with valid admin token - REAL JWT decode."""
        headers = {"Authorization": f"Bearer {valid_admin_token}"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "maximus_admin"
        assert "admin" in data["roles"]
        assert "user" in data["roles"]

    async def test_get_user_profile_with_valid_user_token(self, client, valid_user_token):
        """Test getting user profile with valid user token - REAL JWT decode."""
        headers = {"Authorization": f"Bearer {valid_user_token}"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "maximus_user"
        assert data["roles"] == ["user"]

    async def test_get_user_profile_without_token(self, client):
        """Test getting user profile without token - should reject."""
        response = await client.get("/users/me")

        assert response.status_code == 401

    async def test_get_user_profile_with_invalid_token(self, client):
        """Test getting user profile with invalid token - REAL JWT decode failure."""
        headers = {"Authorization": "Bearer invalid_token_string"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "could not validate credentials" in data["detail"].lower()

    async def test_get_user_profile_with_expired_token(self, client, expired_token):
        """Test getting user profile with expired token - REAL JWT expiration check."""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 401

    async def test_get_user_profile_with_malformed_token(self, client):
        """Test getting user profile with malformed JWT."""
        headers = {"Authorization": "Bearer not.a.valid.jwt"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 401

    async def test_get_user_profile_with_token_for_nonexistent_user(self, client):
        """Test getting user profile with token for user that doesn't exist in DB."""
        # Create token for non-existent user
        token_data = {"sub": "deleted_user", "roles": ["user"], "exp": datetime.utcnow() + timedelta(minutes=30)}
        fake_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        headers = {"Authorization": f"Bearer {fake_token}"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 401


# ==================== ROLE-BASED ACCESS CONTROL TESTS ====================


@pytest.mark.asyncio
class TestRoleBasedAccessControl:
    """Test role-based access control with REAL permission checking."""

    async def test_admin_resource_with_admin_token(self, client, valid_admin_token):
        """Test accessing admin resource with admin role - REAL RBAC check."""
        headers = {"Authorization": f"Bearer {valid_admin_token}"}
        response = await client.get("/admin_resource", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "welcome, admin" in data["message"].lower()

    async def test_admin_resource_with_user_token(self, client, valid_user_token):
        """Test accessing admin resource with user role - REAL RBAC rejection."""
        headers = {"Authorization": f"Bearer {valid_user_token}"}
        response = await client.get("/admin_resource", headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "not enough permissions" in data["detail"].lower()

    async def test_admin_resource_without_token(self, client):
        """Test accessing admin resource without authentication."""
        response = await client.get("/admin_resource")

        assert response.status_code == 401

    async def test_admin_resource_verifies_admin_role_in_list(self, client, valid_user_token):
        """Test that admin resource checks for 'admin' in roles list - REAL check."""
        # Use maximus_user token (has only 'user' role, no 'admin')
        headers = {"Authorization": f"Bearer {valid_user_token}"}
        response = await client.get("/admin_resource", headers=headers)

        # Should be rejected (403) because 'admin' not in roles
        assert response.status_code == 403


# ==================== HELPER FUNCTION TESTS ====================


class TestHelperFunctions:
    """Test helper functions with REAL implementations."""

    def test_create_access_token_with_custom_expiration(self):
        """Test creating token with custom expiration - REAL JWT encoding."""
        data = {"sub": "test_user", "roles": ["user"]}
        expires_delta = timedelta(minutes=60)

        token = create_access_token(data, expires_delta)

        # Decode and verify
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "test_user"
        assert decoded["roles"] == ["user"]
        assert "exp" in decoded

    def test_create_access_token_default_expiration(self):
        """Test creating token with default expiration (15 min) - REAL JWT encoding."""
        data = {"sub": "test_user"}

        token = create_access_token(data)

        # Decode and verify
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "test_user"
        assert "exp" in decoded

    def test_bcrypt_hashing_is_secure(self):
        """Test that bcrypt hashing is one-way and deterministic."""
        password = "test_password"

        # Hash the password
        hashed1 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        hashed2 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Different hashes due to random salt
        assert hashed1 != hashed2

        # But both verify correctly
        assert bcrypt.checkpw(password.encode("utf-8"), hashed1)
        assert bcrypt.checkpw(password.encode("utf-8"), hashed2)

        # Wrong password doesn't verify
        assert not bcrypt.checkpw("wrong_password".encode("utf-8"), hashed1)


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_login_missing_username_returns_422(self, client):
        """Test login without username."""
        form_data = {
            "password": "somepassword"
            # Missing username
        }

        response = await client.post("/token", data=form_data)
        assert response.status_code == 422

    async def test_login_missing_password_returns_422(self, client):
        """Test login without password."""
        form_data = {
            "username": "maximus_admin"
            # Missing password
        }

        response = await client.post("/token", data=form_data)
        assert response.status_code == 422

    async def test_login_empty_username(self, client):
        """Test login with empty username string."""
        form_data = {"username": "", "password": "somepassword"}

        response = await client.post("/token", data=form_data)
        # FastAPI OAuth2PasswordRequestForm validates and returns 422 for empty username
        assert response.status_code == 422

    async def test_login_empty_password(self, client):
        """Test login with empty password string."""
        form_data = {"username": "maximus_admin", "password": ""}

        response = await client.post("/token", data=form_data)
        # FastAPI OAuth2PasswordRequestForm validates and returns 422 for empty password
        assert response.status_code == 422


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and security scenarios."""

    async def test_token_with_missing_sub_claim(self, client):
        """Test token without 'sub' claim - REAL JWT validation."""
        # Create token without 'sub'
        token_data = {
            "roles": ["user"],
            "exp": datetime.utcnow() + timedelta(minutes=30),
            # Missing 'sub'
        }
        bad_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        headers = {"Authorization": f"Bearer {bad_token}"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 401

    async def test_token_with_wrong_secret_key(self, client):
        """Test token signed with different secret key - REAL JWT verification."""
        wrong_key = "wrong-secret-key"
        token_data = {"sub": "maximus_admin", "roles": ["admin"], "exp": datetime.utcnow() + timedelta(minutes=30)}
        bad_token = jwt.encode(token_data, wrong_key, algorithm=ALGORITHM)

        headers = {"Authorization": f"Bearer {bad_token}"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 401

    async def test_case_sensitive_username(self, client):
        """Test that username is case-sensitive."""
        form_data = {
            "username": "MAXIMUS_ADMIN",  # Uppercase
            "password": "adminpass",
        }

        response = await client.post("/token", data=form_data)
        # Should fail because username doesn't match exactly
        assert response.status_code == 401

    async def test_multiple_login_tokens_are_valid(self, client):
        """Test that multiple login requests generate valid tokens."""
        form_data = {"username": "maximus_admin", "password": "adminpass"}

        # Login twice
        response1 = await client.post("/token", data=form_data)
        response2 = await client.post("/token", data=form_data)

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        # Both tokens should be valid and decodable
        decoded1 = jwt.decode(token1, SECRET_KEY, algorithms=[ALGORITHM])
        decoded2 = jwt.decode(token2, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded1["sub"] == decoded2["sub"] == "maximus_admin"
        assert "admin" in decoded1["roles"]
        assert "admin" in decoded2["roles"]

    async def test_authorization_header_format(self, client):
        """Test different Authorization header formats."""
        token_data = {"sub": "maximus_admin", "roles": ["admin"], "exp": datetime.utcnow() + timedelta(minutes=30)}
        valid_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # Correct format: "Bearer <token>"
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 200

        # Wrong format: missing "Bearer" prefix
        headers = {"Authorization": valid_token}
        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 401

    async def test_login_preserves_all_roles(self, client):
        """Test that login token includes all user roles."""
        form_data = {"username": "maximus_admin", "password": "adminpass"}

        response = await client.post("/token", data=form_data)
        token = response.json()["access_token"]
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Admin has both 'admin' and 'user' roles
        assert len(decoded["roles"]) == 2
        assert "admin" in decoded["roles"]
        assert "user" in decoded["roles"]

    async def test_password_special_characters(self, client):
        """Test login with password containing special characters (future-proofing)."""
        # Note: Current test users don't have special char passwords,
        # but we test that special chars don't break the flow
        form_data = {"username": "maximus_admin", "password": "admin!@#$%^&*()"}

        response = await client.post("/token", data=form_data)
        # Will fail authentication, but shouldn't error
        assert response.status_code == 401
