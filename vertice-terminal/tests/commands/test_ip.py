
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, mock_open

from vertice.commands.ip import app as ip_app

runner = CliRunner()

# Unify testing strategy to match integration tests, which is a proven pattern.
# This uses httpx_mock to simulate the backend, providing more realistic tests.

@patch('vertice.utils.decorators.require_auth', lambda: None)
def test_analyze_ip_success(httpx_mock):
    """Test the 'ip analyze' command with a mocked backend."""
    # Arrange
    httpx_mock.add_response(url="http://test-ip-service.com/", json={"status": "operational"})
    httpx_mock.add_response(
        url="http://test-ip-service.com/api/ip/analyze",
        method="POST",
        json={"ip": "8.8.8.8", "reputation": {"threat_level": "CLEAN"}},
        match_json={"ip": "8.8.8.8"}
    )

    with patch('vertice.connectors.ip_intel.config.get', return_value="http://test-ip-service.com"):
        # Act
        result = runner.invoke(ip_app, ["analyze", "8.8.8.8"])

    # Assert
    assert result.exit_code == 0, result.stdout
    assert "CLEAN" in result.stdout

@patch('vertice.utils.decorators.require_auth', lambda: None)
def test_analyze_ip_json(httpx_mock):
    """Test the 'ip analyze' command with the --json flag."""
    # Arrange
    mock_result = {"ip": "8.8.8.8", "reputation": "test"}
    httpx_mock.add_response(url="http://test-ip-service.com/", json={"status": "operational"})
    httpx_mock.add_response(
        url="http://test-ip-service.com/api/ip/analyze",
        method="POST",
        json=mock_result,
        match_json={"ip": "8.8.8.8"}
    )

    with patch('vertice.connectors.ip_intel.config.get', return_value="http://test-ip-service.com"):
        # Act
        result = runner.invoke(ip_app, ["analyze", "8.8.8.8", "--json"])

    # Assert
    assert result.exit_code == 0, result.stdout
    # The output is pretty-printed, so we can't load it as JSON directly.
    # Instead, we check for key substrings.
    assert '"ip": "8.8.8.8"' in result.stdout
    assert '"reputation": "test"' in result.stdout

@patch('vertice.utils.decorators.require_auth', lambda: None)
def test_analyze_ip_service_offline(httpx_mock):
    """Test the 'ip analyze' command when the service is offline."""
    # Arrange
    httpx_mock.add_response(url="http://test-ip-service.com/", status_code=500)

    with patch('vertice.connectors.ip_intel.config.get', return_value="http://test-ip-service.com"):
        # Act
        result = runner.invoke(ip_app, ["analyze", "8.8.8.8"])

    # Assert
    assert result.exit_code == 0, result.stdout
    assert "is not available" in result.stdout

@patch('vertice.utils.decorators.require_auth', lambda: None)
@patch('builtins.open', new_callable=mock_open, read_data="8.8.8.8\n1.1.1.1")
def test_bulk_command(mock_file, httpx_mock):
    """Test the 'ip bulk' command."""
    # Arrange
    httpx_mock.add_response(url="http://test-ip-service.com/", json={"status": "operational"})
    httpx_mock.add_response(url="http://test-ip-service.com/api/ip/analyze", method="POST", json={"ip": "8.8.8.8"})
    httpx_mock.add_response(url="http://test-ip-service.com/api/ip/analyze", method="POST", json={"ip": "1.1.1.1"})

    with patch('vertice.connectors.ip_intel.config.get', return_value="http://test-ip-service.com"):
        # Act
        result = runner.invoke(ip_app, ["bulk", "fake_ips.txt"])

    # Assert
    assert result.exit_code == 0, result.stdout
    mock_file.assert_called_once_with("fake_ips.txt", "r")
    # httpx_mock keeps track of calls
    assert len(httpx_mock.get_requests()) == 3 # 1 health check + 2 analyze calls
