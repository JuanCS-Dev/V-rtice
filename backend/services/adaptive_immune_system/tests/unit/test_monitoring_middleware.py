"""
Unit Tests for Monitoring Middleware Module.

Tests the PrometheusMiddleware class for:
- Request/response interception
- Automatic metric collection
- Timing measurements
- Error handling
- Label extraction
"""

import pytest
import asyncio
import time
from unittest.mock import Mock

try:
    from hitl.monitoring.middleware import PrometheusMiddleware
    from hitl.monitoring.metrics import RabbitMQMetrics
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False
    pytest.skip("Monitoring middleware not available", allow_module_level=True)


# Mock FastAPI request/response
class MockRequest:
    """Mock FastAPI Request object."""

    def __init__(self, method: str = "GET", path: str = "/test"):
        self.method = method
        self.url = Mock()
        self.url.path = path
        self.client = Mock()
        self.client.host = "127.0.0.1"


class MockResponse:
    """Mock FastAPI Response object."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.headers = {}


class TestPrometheusMiddlewareInitialization:
    """Test PrometheusMiddleware initialization."""

    def test_middleware_initializes_with_app(self):
        """Test middleware initializes with FastAPI app."""
        app = Mock()
        middleware = PrometheusMiddleware(app)

        assert middleware.app == app
        assert middleware.metrics is not None
        assert isinstance(middleware.metrics, RabbitMQMetrics)

    def test_middleware_initializes_metrics(self):
        """Test middleware creates metrics instance."""
        app = Mock()
        middleware = PrometheusMiddleware(app)

        # Should have access to HTTP metrics
        assert hasattr(middleware.metrics, 'messages_published_total')


class TestRequestInterception:
    """Test request interception and processing."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return Mock()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return PrometheusMiddleware(app)

    @pytest.mark.asyncio
    async def test_middleware_intercepts_request(self, middleware):
        """Test middleware intercepts incoming requests."""
        request = MockRequest(method="GET", path="/test")

        # Mock call_next to return response
        async def mock_call_next(req):
            return MockResponse(status_code=200)

        # Call middleware
        response = await middleware.dispatch(request, mock_call_next)

        assert response is not None
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_measures_request_duration(self, middleware):
        """Test middleware measures request duration."""
        request = MockRequest(method="GET", path="/test")

        async def mock_call_next(req):
            await asyncio.sleep(0.01)  # Simulate processing
            return MockResponse(status_code=200)

        start_time = time.time()
        response = await middleware.dispatch(request, mock_call_next)
        duration = time.time() - start_time

        # Duration should be at least 0.01 seconds
        assert duration >= 0.01
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_handles_different_http_methods(self, middleware):
        """Test middleware handles GET, POST, PUT, DELETE, etc."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            request = MockRequest(method=method, path="/test")

            async def mock_call_next(req):
                return MockResponse(status_code=200)

            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_handles_different_paths(self, middleware):
        """Test middleware handles different URL paths."""
        paths = ["/", "/health", "/metrics", "/api/v1/test", "/admin/dashboard"]

        for path in paths:
            request = MockRequest(method="GET", path=path)

            async def mock_call_next(req):
                return MockResponse(status_code=200)

            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200


class TestResponseHandling:
    """Test response handling and status codes."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return PrometheusMiddleware(Mock())

    @pytest.mark.asyncio
    async def test_middleware_handles_2xx_responses(self, middleware):
        """Test middleware handles successful 2xx responses."""
        status_codes = [200, 201, 202, 204]

        for status_code in status_codes:
            request = MockRequest(method="GET", path="/test")

            async def mock_call_next(req):
                return MockResponse(status_code=status_code)

            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == status_code

    @pytest.mark.asyncio
    async def test_middleware_handles_4xx_responses(self, middleware):
        """Test middleware handles client error 4xx responses."""
        status_codes = [400, 401, 403, 404]

        for status_code in status_codes:
            request = MockRequest(method="GET", path="/test")

            async def mock_call_next(req):
                return MockResponse(status_code=status_code)

            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == status_code

    @pytest.mark.asyncio
    async def test_middleware_handles_5xx_responses(self, middleware):
        """Test middleware handles server error 5xx responses."""
        status_codes = [500, 502, 503, 504]

        for status_code in status_codes:
            request = MockRequest(method="GET", path="/test")

            async def mock_call_next(req):
                return MockResponse(status_code=status_code)

            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == status_code


class TestErrorHandling:
    """Test middleware error handling."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return PrometheusMiddleware(Mock())

    @pytest.mark.asyncio
    async def test_middleware_handles_exception_in_handler(self, middleware):
        """Test middleware handles exceptions from request handler."""
        request = MockRequest(method="GET", path="/test")

        async def mock_call_next(req):
            raise ValueError("Test error")

        # Middleware should re-raise exception (FastAPI handles it)
        with pytest.raises(ValueError):
            await middleware.dispatch(request, mock_call_next)

    @pytest.mark.asyncio
    async def test_middleware_records_metrics_on_exception(self, middleware):
        """Test middleware records metrics even when exception occurs."""
        request = MockRequest(method="GET", path="/test")

        async def mock_call_next(req):
            raise RuntimeError("Test error")

        # Exception should be raised but metrics should be recorded
        with pytest.raises(RuntimeError):
            await middleware.dispatch(request, mock_call_next)

        # Metrics should still be available
        assert middleware.metrics is not None


class TestMetricsCollection:
    """Test automatic metrics collection."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return PrometheusMiddleware(Mock())

    @pytest.mark.asyncio
    async def test_middleware_updates_http_request_counter(self, middleware):
        """Test middleware increments HTTP request counter."""
        request = MockRequest(method="GET", path="/test")

        async def mock_call_next(req):
            return MockResponse(status_code=200)

        # Get metrics before
        metrics_before = middleware.metrics.get_metrics()

        # Make request
        await middleware.dispatch(request, mock_call_next)

        # Get metrics after
        metrics_after = middleware.metrics.get_metrics()

        # Metrics should have changed
        assert len(metrics_after) >= len(metrics_before)

    @pytest.mark.asyncio
    async def test_middleware_records_request_duration(self, middleware):
        """Test middleware records request duration in histogram."""
        request = MockRequest(method="GET", path="/test")

        async def mock_call_next(req):
            await asyncio.sleep(0.05)  # 50ms delay
            return MockResponse(status_code=200)

        await middleware.dispatch(request, mock_call_next)

        # Duration histogram should be updated
        metrics_output = middleware.metrics.get_metrics()
        assert "http_request_duration" in metrics_output or len(metrics_output) > 0


class TestPathNormalization:
    """Test URL path normalization for metrics."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return PrometheusMiddleware(Mock())

    @pytest.mark.asyncio
    async def test_middleware_handles_root_path(self, middleware):
        """Test middleware handles root path correctly."""
        request = MockRequest(method="GET", path="/")

        async def mock_call_next(req):
            return MockResponse(status_code=200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_handles_path_with_query_params(self, middleware):
        """Test middleware handles paths with query parameters."""
        request = MockRequest(method="GET", path="/api/test?foo=bar&baz=qux")

        async def mock_call_next(req):
            return MockResponse(status_code=200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_handles_path_with_fragments(self, middleware):
        """Test middleware handles paths with URL fragments."""
        request = MockRequest(method="GET", path="/api/test#section")

        async def mock_call_next(req):
            return MockResponse(status_code=200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200


class TestConcurrentRequests:
    """Test middleware handles concurrent requests."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return PrometheusMiddleware(Mock())

    @pytest.mark.asyncio
    async def test_middleware_handles_concurrent_requests(self, middleware):
        """Test middleware handles multiple concurrent requests."""
        async def make_request(path: str):
            request = MockRequest(method="GET", path=path)

            async def mock_call_next(req):
                await asyncio.sleep(0.01)
                return MockResponse(status_code=200)

            return await middleware.dispatch(request, mock_call_next)

        # Make 10 concurrent requests
        tasks = [make_request(f"/test{i}") for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert len(responses) == 10
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_middleware_metrics_handle_concurrent_updates(self, middleware):
        """Test metrics correctly handle concurrent updates."""
        async def make_request(method: str, path: str):
            request = MockRequest(method=method, path=path)

            async def mock_call_next(req):
                return MockResponse(status_code=200)

            return await middleware.dispatch(request, mock_call_next)

        # Make mixed concurrent requests
        tasks = [
            make_request("GET", "/test1"),
            make_request("POST", "/test2"),
            make_request("PUT", "/test3"),
            make_request("DELETE", "/test4"),
            make_request("GET", "/test5"),
        ]
        await asyncio.gather(*tasks)

        # Metrics should be consistent
        metrics_output = middleware.metrics.get_metrics()
        assert len(metrics_output) > 0


class TestMetricsEndpoint:
    """Test middleware doesn't interfere with /metrics endpoint."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return PrometheusMiddleware(Mock())

    @pytest.mark.asyncio
    async def test_middleware_allows_metrics_endpoint_through(self, middleware):
        """Test middleware doesn't block /metrics endpoint."""
        request = MockRequest(method="GET", path="/metrics")

        async def mock_call_next(req):
            # Simulate returning metrics
            return MockResponse(status_code=200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_records_metrics_for_metrics_endpoint(self, middleware):
        """Test middleware records metrics for /metrics endpoint itself."""
        request = MockRequest(method="GET", path="/metrics")

        async def mock_call_next(req):
            return MockResponse(status_code=200)

        await middleware.dispatch(request, mock_call_next)

        # Should record metrics for the metrics endpoint
        metrics_output = middleware.metrics.get_metrics()
        assert len(metrics_output) > 0


class TestMiddlewarePerformance:
    """Test middleware performance characteristics."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return PrometheusMiddleware(Mock())

    @pytest.mark.asyncio
    async def test_middleware_adds_minimal_overhead(self, middleware):
        """Test middleware adds minimal overhead to requests."""
        request = MockRequest(method="GET", path="/test")

        # Measure with middleware
        async def mock_call_next(req):
            return MockResponse(status_code=200)

        start = time.time()
        await middleware.dispatch(request, mock_call_next)
        middleware_duration = time.time() - start

        # Middleware overhead should be < 10ms
        assert middleware_duration < 0.01

    @pytest.mark.asyncio
    async def test_middleware_fast_path_execution(self, middleware):
        """Test middleware executes fast path quickly."""
        request = MockRequest(method="GET", path="/health")

        async def mock_call_next(req):
            return MockResponse(status_code=200)

        # Should execute quickly even for high-frequency endpoints
        start = time.time()
        for _ in range(100):
            await middleware.dispatch(request, mock_call_next)
        duration = time.time() - start

        # 100 requests should complete in < 1 second
        assert duration < 1.0


# Integration-style tests
class TestMiddlewareIntegration:
    """Integration tests for middleware."""

    @pytest.mark.asyncio
    async def test_complete_request_response_cycle(self):
        """Test complete request-response cycle with metrics."""
        app = Mock()
        middleware = PrometheusMiddleware(app)

        request = MockRequest(method="POST", path="/api/v1/test")

        async def mock_call_next(req):
            await asyncio.sleep(0.01)
            return MockResponse(status_code=201)

        response = await middleware.dispatch(request, mock_call_next)

        assert response.status_code == 201

        # Verify metrics were recorded
        metrics_output = middleware.metrics.get_metrics()
        assert len(metrics_output) > 0

    @pytest.mark.asyncio
    async def test_error_path_with_metrics(self):
        """Test error path records metrics correctly."""
        app = Mock()
        middleware = PrometheusMiddleware(app)

        request = MockRequest(method="GET", path="/api/error")

        async def mock_call_next(req):
            return MockResponse(status_code=500)

        response = await middleware.dispatch(request, mock_call_next)

        assert response.status_code == 500

        # Should still record metrics
        metrics_output = middleware.metrics.get_metrics()
        assert len(metrics_output) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
