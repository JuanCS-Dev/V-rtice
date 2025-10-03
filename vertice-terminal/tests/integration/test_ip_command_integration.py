
import pytest
from typer.testing import CliRunner

from vertice.commands.ip import app as ip_app
from unittest.mock import patch

runner = CliRunner()

# This integration test uses httpx_mock to simulate the backend service.
# It tests the command, the connector, and the HTTP layer together.
@pytest.mark.asyncio
@patch('vertice.commands.ip.require_auth', lambda: None)
async def test_ip_analyze_integration_success(httpx_mock):
    """Test the full flow of 'ip analyze' with a mocked backend."""
    # Arrange
    # Mock the two HTTP calls that will be made: health check and analyze
    httpx_mock.add_response(
        url="http://test-ip-service.com/",
        method="GET",
        json={"status": "operational"}
    )
    httpx_mock.add_response(
        url="http://test-ip-service.com/api/ip/analyze",
        method="POST",
        json={"ip": "1.2.3.4", "reputation": {"threat_level": "SUSPICIOUS"}},
        match_json={"ip": "1.2.3.4"}
    )

    # We need to override the config to point our connector to the test service
    with patch('vertice.connectors.ip_intel.config.get', return_value="http://test-ip-service.com"):
        # Act
        result = runner.invoke(ip_app, ["analyze", "1.2.3.4"])

    # Assert
    assert result.exit_code == 0
    assert "IP Analysis: 1.2.3.4" in result.stdout
    assert "SUSPICIOUS" in result.stdout

@pytest.mark.asyncio
@patch('vertice.commands.ip.require_auth', lambda: None)
async def test_ip_analyze_integration_service_down(httpx_mock):
    """Test the full flow of 'ip analyze' when the backend health check fails."""
    # Arrange
    # Mock the health check to return a server error
    httpx_mock.add_response(
        url="http://test-ip-service.com/",
        method="GET",
        status_code=500
    )

    with patch('vertice.connectors.ip_intel.config.get', return_value="http://test-ip-service.com"):
        # Act
        result = runner.invoke(ip_app, ["analyze", "1.2.3.4"])

    # Assert
    assert result.exit_code == 0 # Graceful exit
    assert "IP Intelligence service is offline" in result.stdout

@pytest.mark.asyncio
@patch('vertice.commands.ip.require_auth', lambda: None)
async def test_ip_analyze_integration_timeout(httpx_mock):
    """Test the full flow of 'ip analyze' when the request times out."""
    # Arrange
    # httpx_mock can simulate timeouts
    def timeout(request, ext):
        raise pytest.httpx.TimeoutException("Timeout!", request=request)

    httpx_mock.add_callback(timeout)

    with patch('vertice.connectors.ip_intel.config.get', return_value="http://test-ip-service.com"):
        # Act
        result = runner.invoke(ip_app, ["analyze", "1.2.3.4"])

    # Assert
    assert result.exit_code == 0 # Graceful exit
    assert "An error occurred" in result.stdout
    assert "Timeout" in result.stdout
