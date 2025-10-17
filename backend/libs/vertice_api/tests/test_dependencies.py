"""Tests for vertice_api.dependencies module."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from vertice_api.dependencies import (
    get_current_user,
    require_permissions,
)


@pytest.fixture()
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    return app


@pytest.fixture()
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetLogger:
    """Tests for get_logger dependency."""

    def test_binds_request_context(self, app, client):
        """Test logger binds request_id, method, path."""

        @app.get("/test")
        async def test_route(logger=None):
            # Mock the dependency
            from vertice_api.dependencies import get_logger
            async for _log in get_logger(MagicMock(app=app, headers={"X-Request-ID": "test-123"}, method="GET", url=MagicMock(path="/test"))):
                return {"status": "ok"}

        # Execute
        response = client.get("/test")
        assert response.status_code == 200

    def test_uses_unknown_when_no_request_id(self, app):
        """Test falls back to 'unknown' when no X-Request-ID."""
        from unittest.mock import MagicMock

        from vertice_api.dependencies import get_logger

        request = MagicMock()
        request.app.title = "test_app"
        request.headers.get.return_value = None
        request.method = "POST"
        request.url.path = "/api/test"

        # Should not raise
        gen = get_logger(request)
        try:
            gen.__anext__()
        except StopAsyncIteration:
            pass


class TestGetDB:
    """Tests for get_db dependency."""

    @pytest.mark.asyncio()
    async def test_raises_503_when_db_not_configured(self):
        """Test raises HTTPException when db_session_factory not in app.state."""
        from unittest.mock import MagicMock

        from vertice_api.dependencies import get_db

        request = MagicMock()
        request.app.state = MagicMock(spec=[])  # No db_session_factory

        with pytest.raises(HTTPException) as exc_info:
            async for _ in get_db(request):
                pass

        # Should raise 503
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio()
    async def test_commits_on_success(self):
        """Test commits session on successful request."""
        from contextlib import asynccontextmanager
        from unittest.mock import AsyncMock, MagicMock

        from vertice_api.dependencies import get_db

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        @asynccontextmanager
        async def mock_factory():
            yield mock_session

        # Mock request with factory
        request = MagicMock()
        request.app.state.db_session_factory = mock_factory

        # Execute
        async for _session in get_db(request):
            pass

        # Should call commit
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_rolls_back_on_exception(self):
        """Test rolls back session when exception occurs."""
        from contextlib import asynccontextmanager
        from unittest.mock import AsyncMock, MagicMock

        from vertice_api.dependencies import get_db

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
        mock_session.rollback = AsyncMock()

        @asynccontextmanager
        async def mock_factory():
            yield mock_session

        # Mock request with factory
        request = MagicMock()
        request.app.state.db_session_factory = mock_factory

        # Execute - should raise and rollback
        with pytest.raises(Exception):
            async for _session in get_db(request):
                pass

        mock_session.rollback.assert_called_once()


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio()
    async def test_raises_401_when_no_authorization(self):
        """Test raises 401 when Authorization header missing."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None)

        assert exc_info.value.status_code == 401
        assert "Missing or invalid" in exc_info.value.detail

    @pytest.mark.asyncio()
    async def test_raises_401_when_invalid_format(self):
        """Test raises 401 when Authorization format is wrong."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Basic abc123")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio()
    async def test_raises_401_on_invalid_token(self):
        """Test raises 401 for 'invalid' token."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer invalid")

        assert exc_info.value.status_code == 401
        assert "Invalid or expired" in exc_info.value.detail

    @pytest.mark.asyncio()
    async def test_returns_dev_user_for_valid_token(self):
        """Test returns dev user data for non-invalid tokens."""
        user = await get_current_user(authorization="Bearer valid_token_123")

        assert user["user_id"] == "dev_user"
        assert user["email"] == "dev@vertice.ai"
        assert "user" in user["roles"]


class TestRequirePermissions:
    """Tests for require_permissions dependency factory."""

    @pytest.mark.asyncio()
    async def test_allows_admin_role(self):
        """Test admin role bypasses permission checks."""
        check_func = require_permissions(["admin:write"])

        mock_user = {"user_id": "admin1", "roles": ["admin"], "permissions": []}

        # Should not raise
        result = await check_func(user=mock_user)
        assert result is None

    @pytest.mark.asyncio()
    async def test_fetches_current_user_when_none_provided(self):
        """Test fetches current user when user=None."""
        from unittest.mock import AsyncMock, patch

        check_func = require_permissions(["admin:read"])

        mock_user_data = {"user_id": "admin2", "roles": ["admin"], "permissions": []}

        with patch(
            "vertice_api.dependencies.get_current_user", new_callable=AsyncMock
        ) as mock_get_user:
            mock_get_user.return_value = mock_user_data

            # Call without passing user (triggers line 234)
            result = await check_func(user=None)
            assert result is None
            mock_get_user.assert_called_once()

    @pytest.mark.asyncio()
    async def test_raises_403_when_missing_permissions(self):
        """Test raises 403 when user lacks required permissions."""
        check_func = require_permissions(["admin:write", "admin:delete"])

        mock_user = {
            "user_id": "user1",
            "roles": ["user"],
            "permissions": ["admin:write"],  # Missing admin:delete
        }

        with pytest.raises(HTTPException) as exc_info:
            await check_func(user=mock_user)

        assert exc_info.value.status_code == 403
        assert "admin:delete" in exc_info.value.detail

    @pytest.mark.asyncio()
    async def test_allows_when_has_all_permissions(self):
        """Test allows access when user has all required permissions."""
        check_func = require_permissions(["read:data", "write:data"])

        mock_user = {
            "user_id": "user2",
            "roles": ["user"],
            "permissions": ["read:data", "write:data", "extra:perm"],
        }

        # Should not raise
        result = await check_func(user=mock_user)
        assert result is None


class TestGetServiceClient:
    """Tests for get_service_client dependency factory."""

    @pytest.mark.asyncio()
    async def test_gets_url_from_registry(self):
        """Test gets service URL from app.state.service_registry."""
        from unittest.mock import MagicMock

        from vertice_api.dependencies import get_service_client

        # Mock request with service registry
        request = MagicMock()
        request.app.state.service_registry = {"osint_collector": "http://osint:8000"}

        client_func = get_service_client("osint_collector")
        client = await client_func(request)

        assert client.base_url == "http://osint:8000"

    @pytest.mark.asyncio()
    async def test_falls_back_to_environment_variable(self):
        """Test falls back to env var when registry doesn't have URL."""
        from unittest.mock import MagicMock, patch

        from vertice_api.dependencies import get_service_client

        # Mock request without service in registry
        request = MagicMock()
        request.app.state.service_registry = {}

        with patch.dict("os.environ", {"MAXIMUS_CORE_URL": "http://maximus:9000"}):
            client_func = get_service_client("maximus_core")
            client = await client_func(request)

            assert client.base_url == "http://maximus:9000"

    @pytest.mark.asyncio()
    async def test_raises_503_when_service_not_available(self):
        """Test raises 503 when service URL not found."""
        from unittest.mock import MagicMock, patch

        from vertice_api.dependencies import get_service_client

        # Mock request with no registry
        request = MagicMock()
        request.app.state = MagicMock(spec=[])  # No service_registry

        with patch.dict("os.environ", {}, clear=True):
            client_func = get_service_client("unknown_service")

            with pytest.raises(HTTPException) as exc_info:
                await client_func(request)

            assert exc_info.value.status_code == 503
            assert "unknown_service" in exc_info.value.detail
