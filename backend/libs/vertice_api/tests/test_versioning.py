"""Tests for vertice_api.versioning module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from vertice_api.versioning import (
    APIVersionMiddleware,
    get_request_version,
    version,
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


class TestAPIVersionMiddleware:
    """Tests for APIVersionMiddleware."""

    def test_initialization_validates_default_in_supported(self):
        """Test raises ValueError if default_version not in supported_versions."""
        from starlette.types import ASGIApp

        with pytest.raises(ValueError) as exc_info:
            APIVersionMiddleware(
                app=MagicMock(spec=ASGIApp),
                default_version="v99",
                supported_versions=["v1", "v2"],
            )

        assert "default_version" in str(exc_info.value)
        assert "must be in supported_versions" in str(exc_info.value)

    def test_uses_default_when_no_header(self, app, client):
        """Test uses default version when client doesn't specify."""
        app.add_middleware(APIVersionMiddleware, default_version="v1")

        @app.get("/test")
        async def test_route(request: Request):
            return {"version": request.state.api_version}

        response = client.get("/test")
        assert response.json()["version"] == "v1"
        assert response.headers["X-API-Version"] == "v1"

    def test_extracts_version_from_header(self, app, client):
        """Test extracts version from Accept-Version header."""
        app.add_middleware(
            APIVersionMiddleware,
            supported_versions=["v1", "v2", "v3"],
        )

        @app.get("/test")
        async def test_route(request: Request):
            return {"version": request.state.api_version}

        response = client.get("/test", headers={"Accept-Version": "v2"})
        assert response.json()["version"] == "v2"

    def test_extracts_version_from_query_param(self, app, client):
        """Test extracts version from ?version query param."""
        app.add_middleware(
            APIVersionMiddleware,
            supported_versions=["v1", "v2"],
        )

        @app.get("/test")
        async def test_route(request: Request):
            return {"version": request.state.api_version}

        response = client.get("/test?version=v2")
        assert response.json()["version"] == "v2"

    def test_rejects_invalid_format_in_strict_mode(self, app, client):
        """Test raises 400 for invalid version format in strict mode."""
        app.add_middleware(
            APIVersionMiddleware,
            default_version="v1",
            strict=True,
        )

        @app.get("/test")
        async def test_route(request: Request):
            return {"version": request.state.api_version}

        with pytest.raises(HTTPException) as exc_info:
            client.get("/test", headers={"Accept-Version": "invalid"})

        assert exc_info.value.status_code == 400
        assert "Invalid version format" in exc_info.value.detail

    def test_falls_back_to_default_in_non_strict_mode(self, app, client):
        """Test falls back to default for invalid format when not strict."""
        app.add_middleware(
            APIVersionMiddleware,
            default_version="v1",
            strict=False,
        )

        @app.get("/test")
        async def test_route(request: Request):
            return {"version": request.state.api_version}

        response = client.get("/test", headers={"Accept-Version": "invalid"})
        assert response.status_code == 200
        assert response.json()["version"] == "v1"

    def test_rejects_unsupported_version_in_strict_mode(self, app, client):
        """Test raises 400 for unsupported version in strict mode."""
        app.add_middleware(
            APIVersionMiddleware,
            default_version="v1",
            supported_versions=["v1", "v2"],
            strict=True,
        )

        @app.get("/test")
        async def test_route(request: Request):
            return {"version": request.state.api_version}

        with pytest.raises(HTTPException) as exc_info:
            client.get("/test", headers={"Accept-Version": "v99"})

        assert exc_info.value.status_code == 400
        assert "Unsupported version" in exc_info.value.detail

    def test_adds_version_to_response_headers(self, app, client):
        """Test adds X-API-Version to response headers."""
        app.add_middleware(
            APIVersionMiddleware,
            supported_versions=["v1", "v2"],
        )

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        response = client.get("/test", headers={"Accept-Version": "v2"})
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v2"

    def test_fallback_to_default_when_unsupported_in_non_strict_mode(self, app, client):
        """Test falls back to default_version for unsupported version when strict=False."""
        app.add_middleware(
            APIVersionMiddleware,
            default_version="v1",
            supported_versions=["v1", "v2"],
            strict=False,  # Non-strict mode
        )

        @app.get("/test")
        async def test_route(request: Request):
            return {"version": request.state.api_version}

        # Send unsupported version v99
        response = client.get("/test", headers={"Accept-Version": "v99"})
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v1"  # Falls back to default


class TestVersionDecorator:
    """Tests for @version decorator."""

    def test_raises_404_on_version_mismatch(self, app, client):
        """Test raises 404 when request version doesn't match endpoint version."""
        app.add_middleware(APIVersionMiddleware, supported_versions=["v1", "v2"])

        @app.get("/users")
        @version("v1")
        async def list_users_v1(request: Request):
            return {"version": "v1"}

        # Request v2, endpoint is v1
        response = client.get("/users", headers={"Accept-Version": "v2"})
        assert response.status_code == 404

    def test_raises_410_after_sunset_date(self, app, client):
        """Test raises 410 Gone when accessing endpoint after sunset."""
        app.add_middleware(APIVersionMiddleware)

        past_date = (datetime.now() - timedelta(days=1)).date().isoformat()

        @app.get("/old")
        @version("v1", sunset_date=past_date)
        async def old_endpoint(request: Request):
            return {"status": "ok"}

        response = client.get("/old", headers={"Accept-Version": "v1"})
        assert response.status_code == 410
        assert "sunset" in response.json()["detail"].lower()

    @pytest.mark.asyncio()
    async def test_handles_async_functions(self):
        """Test decorator works with async functions."""
        from vertice_api.versioning import version

        @version("v1")
        async def async_func(request: Request):
            return {"status": "ok"}

        # Mock request
        request = MagicMock()
        request.state.api_version = "v1"

        result = await async_func(request=request)
        assert result["status"] == "ok"

    @pytest.mark.asyncio()
    async def test_finds_request_in_args_positional(self):
        """Test decorator can find Request object in positional args."""
        from vertice_api.versioning import version

        @version("v2")
        async def handler_with_positional_request(req: Request, user_id: int):
            return {"user_id": user_id, "version": req.state.api_version}

        # Pass Request as positional arg (not in kwargs)
        mock_request = MagicMock(spec=Request)
        mock_request.state.api_version = "v2"

        result = await handler_with_positional_request(mock_request, 123)
        assert result["user_id"] == 123
        assert result["version"] == "v2"

    @pytest.mark.asyncio()
    async def test_finds_request_among_multiple_args(self):
        """Test decorator finds Request when it's not the first arg."""
        from vertice_api.versioning import version

        @version("v2")
        async def handler_with_mixed_args(user_id: int, name: str, req: Request, extra: str):
            return {"user_id": user_id, "version": req.state.api_version}

        # Request is 3rd positional arg - should iterate through args to find it
        mock_request = MagicMock(spec=Request)
        mock_request.state.api_version = "v2"

        result = await handler_with_mixed_args(123, "test", mock_request, "extra")
        assert result["user_id"] == 123
        assert result["version"] == "v2"

    @pytest.mark.asyncio()
    async def test_passes_through_when_version_matches(self):
        """Test decorator passes through when request and endpoint versions match."""
        from vertice_api.versioning import version

        @version("v2")
        async def handler(request: Request):
            return {"status": "success"}

        mock_request = MagicMock(spec=Request)
        mock_request.state.api_version = "v2"

        result = await handler(request=mock_request)
        assert result == {"status": "success"}

    @pytest.mark.asyncio()
    async def test_handler_without_request_object(self):
        """Test decorator works when no Request object found (edge case)."""
        from vertice_api.versioning import version

        @version("v1")
        async def handler_no_request(user_id: int, name: str):
            # No Request object - should still execute
            return {"user_id": user_id, "name": name}

        result = await handler_no_request(user_id=123, name="test")
        assert result == {"user_id": 123, "name": "test"}

    def test_adds_deprecation_headers_with_response_in_kwargs(self, app, client):
        """Test adds deprecation headers when Response object passed in kwargs."""
        from fastapi import Response

        app.add_middleware(APIVersionMiddleware, supported_versions=["v1", "v2"])

        future_date = (datetime.now() + timedelta(days=90)).date().isoformat()

        @app.get("/legacy")
        @version("v1", deprecated=True, sunset_date=future_date)
        async def legacy_endpoint(request: Request, response: Response):
            return {"status": "deprecated"}

        response = client.get("/legacy", headers={"Accept-Version": "v1"})
        assert response.status_code == 200
        assert "Deprecation" in response.headers
        assert response.headers["Deprecation"] == "true"
        assert "Sunset" in response.headers
        assert "Link" in response.headers
        assert "deprecation" in response.headers["Link"]

    def test_deprecated_without_sunset_date(self, app, client):
        """Test deprecated endpoint without sunset_date (branch coverage)."""
        from fastapi import Response

        app.add_middleware(APIVersionMiddleware, supported_versions=["v1"])

        @app.get("/deprecated")
        @version("v1", deprecated=True)  # No sunset_date
        async def deprecated_endpoint(request: Request, response: Response):
            return {"status": "ok"}

        response = client.get("/deprecated", headers={"Accept-Version": "v1"})
        assert response.status_code == 200
        assert "Deprecation" in response.headers
        # Sunset header should NOT be added when no sunset_date
        assert "Sunset" not in response.headers or response.headers.get("Sunset") == ""

    def test_deprecated_without_response_object(self, app, client):
        """Test deprecated endpoint without Response in kwargs (branch coverage)."""
        app.add_middleware(APIVersionMiddleware, supported_versions=["v1"])

        @app.get("/deprecated-noresponse")
        @version("v1", deprecated=True, sunset_date="2025-12-31")
        async def deprecated_no_response(request: Request):  # No Response param
            return {"status": "ok"}

        response = client.get("/deprecated-noresponse", headers={"Accept-Version": "v1"})
        assert response.status_code == 200
        # Headers won't be added since Response object not in kwargs
        assert "Deprecation" not in response.headers or response.headers.get("Deprecation") != "true"

    @pytest.mark.asyncio()
    async def test_handles_sync_functions(self):
        """Test decorator works with sync functions."""
        from vertice_api.versioning import version

        @version("v1")
        def sync_func(request: Request):
            return {"status": "ok"}

        # Mock request
        request = MagicMock()
        request.state.api_version = "v1"

        result = await sync_func(request=request)
        assert result["status"] == "ok"

    def test_stores_metadata_on_function(self):
        """Test decorator stores version metadata on function."""
        from vertice_api.versioning import version

        @version("v2", deprecated=True, sunset_date="2025-12-31")
        async def func() -> None:
            pass

        assert func.__api_version__ == "v2"
        assert func.__deprecated__ is True
        assert func.__sunset_date__ == "2025-12-31"


class TestGetRequestVersion:
    """Tests for get_request_version helper."""

    def test_returns_version_from_state(self):
        """Test returns api_version from request.state."""
        request = MagicMock()
        request.state.api_version = "v3"

        version = get_request_version(request)
        assert version == "v3"

    def test_raises_when_version_not_set(self):
        """Test raises ValueError when middleware not installed."""
        request = MagicMock()
        request.state = MagicMock(spec=[])  # No api_version

        with pytest.raises(ValueError) as exc_info:
            get_request_version(request)

        assert "not set" in str(exc_info.value)
        assert "Middleware" in str(exc_info.value)


class TestVersionRange:
    """Tests for @version_range decorator."""

    @pytest.mark.asyncio()
    async def test_allows_version_in_range(self):
        """Test allows request when version is within range."""
        from vertice_api.versioning import version_range

        @version_range("v2", "v4")
        async def func(request: Request):
            return {"status": "ok"}

        # Mock request with v3
        request = MagicMock()
        request.state.api_version = "v3"

        result = await func(request)
        assert result["status"] == "ok"

    @pytest.mark.asyncio()
    async def test_raises_404_below_min_version(self):
        """Test raises 404 when version below minimum."""
        from starlette.datastructures import State
        from vertice_api.versioning import version_range

        @version_range("v2", "v4")
        async def func(request: Request):
            return {"status": "ok"}

        # Create mock without spec to allow dynamic attributes
        request = MagicMock()
        request.state = State()
        request.state.api_version = "v1"

        with pytest.raises(HTTPException) as exc_info:
            await func(request)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio()
    async def test_raises_404_above_max_version(self):
        """Test raises 404 when version above maximum."""
        from starlette.datastructures import State
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        async def func(request: Request):
            return {"status": "ok"}

        # Create mock without spec to allow dynamic attributes
        request = MagicMock()
        request.state = State()
        request.state.api_version = "v5"

        with pytest.raises(HTTPException) as exc_info:
            await func(request)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio()
    async def test_allows_no_max_version(self):
        """Test allows any version >= min when max_version is None."""
        from vertice_api.versioning import version_range

        @version_range("v3")
        async def func(request: Request):
            return {"status": "ok"}

        # Mock request with v99
        request = MagicMock()
        request.state.api_version = "v99"

        result = await func(request)
        assert result["status"] == "ok"

    @pytest.mark.asyncio()
    async def test_handles_sync_functions(self):
        """Test version_range works with sync functions."""
        from vertice_api.versioning import version_range

        @version_range("v1", "v2")
        def sync_func(request: Request):
            return {"status": "sync"}

        request = MagicMock()
        request.state.api_version = "v2"

        result = await sync_func(request)
        assert result["status"] == "sync"

    @pytest.mark.asyncio()
    async def test_works_without_request_object(self):
        """Test version_range passes through when no Request found."""
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        def handler_no_request(user_id: int, name: str):
            # No Request - should execute without version checks
            return {"user_id": user_id, "name": name}

        # Call without Request object
        result = await handler_no_request(user_id=123, name="test")
        assert result == {"user_id": 123, "name": "test"}

    @pytest.mark.asyncio()
    async def test_loops_through_non_request_args_without_finding_request(self):
        """Test version_range loops through all args when Request not found (branch 341->349)."""
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        async def handler_with_only_primitives(num: int, text: str, flag: bool):
            # Only primitive args, no Request - loop executes but finds nothing
            return {"num": num, "text": text, "flag": flag}

        # Call with multiple non-Request args - will loop through all without finding Request
        result = await handler_with_only_primitives(42, "test", True)
        assert result == {"num": 42, "text": "test", "flag": True}

    @pytest.mark.asyncio()
    async def test_finds_request_in_positional_args(self):
        """Test version_range finds Request in positional args."""
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        async def handler_mixed_args(user_id: int, req: Request, name: str):
            # Request is 2nd positional arg
            return {"version": req.state.api_version, "name": name}

        mock_request = MagicMock(spec=Request)
        mock_request.state.api_version = "v2"

        result = await handler_mixed_args(123, mock_request, "test")
        assert result["version"] == "v2"
        assert result["name"] == "test"

    @pytest.mark.asyncio()
    async def test_skips_non_request_args(self):
        """Test version_range loops through args to find Request."""
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        async def handler(num: int, text: str, req: Request, flag: bool):
            # Request is 3rd arg - should iterate through int and str first
            return {"version": req.state.api_version}

        mock_request = MagicMock(spec=Request)
        mock_request.state.api_version = "v2"

        # Pass non-Request args before Request
        result = await handler(42, "text", mock_request, True)
        assert result["version"] == "v2"

    @pytest.mark.asyncio()
    async def test_request_without_state_attribute(self):
        """Test version_range handles Request without state (edge case)."""
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        async def handler(req: Request):
            return {"status": "ok"}

        # Mock Request without state attribute
        mock_request = MagicMock()
        # Deliberately omit 'state' attribute

        # Should pass through without version checks
        result = await handler(req=mock_request)
        assert result["status"] == "ok"

    @pytest.mark.asyncio()
    async def test_request_state_without_api_version(self):
        """Test version_range handles Request.state without api_version."""
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        async def handler(req: Request):
            return {"status": "ok"}

        # Mock Request with state but no api_version
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        # Deliberately omit 'api_version' attribute

        # Should pass through without version checks
        result = await handler(req=mock_request)
        assert result["status"] == "ok"

    @pytest.mark.asyncio()
    async def test_finds_request_in_kwargs(self):
        """Test version_range finds Request in kwargs (branch 341->349)."""
        from starlette.datastructures import State
        from vertice_api.versioning import version_range

        @version_range("v1", "v3")
        async def handler_kwargs_request(user_id: int, *, request: Request):
            # Request in kwargs only
            return {"version": request.state.api_version, "user_id": user_id}

        # Create proper mock with real State object
        mock_request = MagicMock()
        mock_request.state = State()
        mock_request.state.api_version = "v2"
        mock_request.method = "GET"  # hasattr checks

        # Pass request as kwarg - triggers line 341 False, skips loop 342-347, goes to 349
        result = await handler_kwargs_request(123, request=mock_request)
        assert result["version"] == "v2"
        assert result["user_id"] == 123
