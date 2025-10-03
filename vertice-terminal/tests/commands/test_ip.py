
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, mock_open

# Since the commands module imports other local modules, we need to set up the path
# This is often a sign that the project structure could be improved to be more test-friendly
from vertice.commands.ip import app as ip_app

runner = CliRunner()

# Mock the auth decorator to always pass
@patch('vertice.commands.ip.require_auth', lambda: None)
@patch('vertice.connectors.ip_intel.IPIntelConnector')
def test_analyze_ip_success(MockIPIntelConnector):
    """Test the 'ip analyze' command with a successful API call."""
    # Arrange
    mock_connector_instance = MagicMock()
    # Mock the async method
    mock_connector_instance.analyze_ip = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.analyze_ip.return_value.set_result({
        'ip': '8.8.8.8',
        'reputation': {'threat_level': 'CLEAN'}
    })
    mock_connector_instance.health_check = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.health_check.return_value.set_result(True)
    mock_connector_instance.close = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.close.return_value.set_result(None)
    MockIPIntelConnector.return_value = mock_connector_instance

    # Act
    result = runner.invoke(ip_app, ["analyze", "8.8.8.8"])

    # Assert
    assert result.exit_code == 0
    assert "IP Analysis: 8.8.8.8" in result.stdout
    assert "CLEAN" in result.stdout
    mock_connector_instance.analyze_ip.assert_called_once_with("8.8.8.8")

@patch('vertice.commands.ip.require_auth', lambda: None)
@patch('vertice.connectors.ip_intel.IPIntelConnector')
def test_analyze_ip_json(MockIPIntelConnector):
    """Test the 'ip analyze' command with the --json flag."""
    # Arrange
    mock_result = {"ip": "8.8.8.8", "reputation": "test"}
    mock_connector_instance = MagicMock()
    mock_connector_instance.analyze_ip = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.analyze_ip.return_value.set_result(mock_result)
    mock_connector_instance.health_check = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.health_check.return_value.set_result(True)
    mock_connector_instance.close = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.close.return_value.set_result(None)
    MockIPIntelConnector.return_value = mock_connector_instance

    # Act
    result = runner.invoke(ip_app, ["analyze", "8.8.8.8", "--json"])

    # Assert
    assert result.exit_code == 0
    # The output should be a JSON string
    import json
    assert json.loads(result.stdout) == mock_result

@patch('vertice.commands.ip.require_auth', lambda: None)
@patch('vertice.connectors.ip_intel.IPIntelConnector')
def test_analyze_ip_service_offline(MockIPIntelConnector):
    """Test the 'ip analyze' command when the service is offline."""
    # Arrange
    mock_connector_instance = MagicMock()
    mock_connector_instance.health_check = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.health_check.return_value.set_result(False)
    mock_connector_instance.close = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.close.return_value.set_result(None)
    MockIPIntelConnector.return_value = mock_connector_instance

    # Act
    result = runner.invoke(ip_app, ["analyze", "8.8.8.8"])

    # Assert
    assert result.exit_code == 0 # The command handles the error gracefully
    assert "IP Intelligence service is offline" in result.stdout

@patch('vertice.commands.ip.require_auth', lambda: None)
@patch('builtins.open', new_callable=mock_open, read_data="8.8.8.8\n1.1.1.1")
@patch('vertice.connectors.ip_intel.IPIntelConnector')
def test_bulk_command(MockIPIntelConnector, mock_file):
    """Test the 'ip bulk' command."""
    # Arrange
    mock_connector_instance = MagicMock()
    # Make analyze_ip return different results for different calls
    mock_connector_instance.analyze_ip.side_effect = [
        asyncio.Future(), asyncio.Future()
    ]
    mock_connector_instance.analyze_ip.side_effect[0].set_result({'ip': '8.8.8.8'})
    mock_connector_instance.analyze_ip.side_effect[1].set_result({'ip': '1.1.1.1'})
    mock_connector_instance.health_check = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.health_check.return_value.set_result(True)
    mock_connector_instance.close = MagicMock(return_value=asyncio.Future())
    mock_connector_instance.close.return_value.set_result(None)
    MockIPIntelConnector.return_value = mock_connector_instance

    # Act
    result = runner.invoke(ip_app, ["bulk", "fake_ips.txt"])

    # Assert
    assert result.exit_code == 0
    mock_file.assert_called_once_with("fake_ips.txt", "r")
    # Check that analyze_ip was called twice
    assert mock_connector_instance.analyze_ip.call_count == 2
    assert "IP Analysis: 8.8.8.8" in result.stdout
    assert "IP Analysis: 1.1.1.1" in result.stdout

# Need to import asyncio to use in the test functions for mocking async returns
import asyncio
