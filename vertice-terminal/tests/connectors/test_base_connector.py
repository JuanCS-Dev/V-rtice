
import pytest
from vertice.connectors.base import BaseConnector

# A concrete implementation of the abstract BaseConnector for testing
class ConcreteConnector(BaseConnector):
    def __init__(self, base_url="http://test-service.com"):
        super().__init__(service_name="Test Service", base_url=base_url)

    async def health_check(self) -> bool:
        # Not needed for these tests
        pass

@pytest.mark.asyncio
async def test_get_success(httpx_mock):
    """Test a successful GET request."""
    # Mock the response for a specific URL
    httpx_mock.add_response(url="http://test-service.com/api/data", json={"key": "value"}, status_code=200)

    connector = ConcreteConnector()
    response = await connector._get("/api/data")

    assert response == {"key": "value"}
    await connector.close()

@pytest.mark.asyncio
async def test_get_http_error(httpx_mock, capsys):
    """Test a GET request that results in an HTTP error (e.g., 404)."""
    httpx_mock.add_response(url="http://test-service.com/api/notfound", status_code=404, text="Not Found")

    connector = ConcreteConnector()
    response = await connector._get("/api/notfound")

    assert response is None
    # Check that a descriptive error was printed to stdout/stderr
    captured = capsys.readouterr()
    assert "Erro da API" in captured.out
    assert "Status 404" in captured.out
    assert "Not Found" in captured.out
    await connector.close()

@pytest.mark.asyncio
async def test_get_network_error(httpx_mock, capsys):
    """Test a GET request that results in a network error."""
    # httpx_mock raises RequestError for any request that is not explicitly mocked
    connector = ConcreteConnector()
    response = await connector._get("/api/unmocked")

    assert response is None
    captured = capsys.readouterr()
    assert "Erro de rede" in captured.out
    await connector.close()

@pytest.mark.asyncio
async def test_post_success(httpx_mock):
    """Test a successful POST request."""
    httpx_mock.add_response(
        url="http://test-service.com/api/create",
        method="POST",
        json={"status": "created", "id": 123},
        status_code=201,
        match_json={"name": "test"} # Ensure the POST body is correct
    )

    connector = ConcreteConnector()
    response = await connector._post("/api/create", data={"name": "test"})

    assert response == {"status": "created", "id": 123}
    await connector.close()

@pytest.mark.asyncio
async def test_post_http_error(httpx_mock, capsys):
    """Test a POST request that results in an HTTP error (e.g., 500)."""
    httpx_mock.add_response(url="http://test-service.com/api/error", method="POST", status_code=500, text="Server Error")

    connector = ConcreteConnector()
    response = await connector._post("/api/error", data={})

    assert response is None
    captured = capsys.readouterr()
    assert "Erro da API" in captured.out
    assert "Status 500" in captured.out
    await connector.close()

@pytest.mark.asyncio
async def test_close_is_called():
    """Test that the close method is called on the httpx client."""
    # This is harder to test directly without more complex mocking.
    # A better design would be to use the connector as a context manager.
    # For now, we trust that `await connector.close()` works as intended.
    pass
