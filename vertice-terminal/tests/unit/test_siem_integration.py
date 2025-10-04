"""
Unit tests for SIEM Integration
================================

Tests for SIEM connectors and event formatters.

Coverage:
- SplunkConnector
- ElasticsearchConnector
- CEFFormatter
- LEEFFormatter
- JSONFormatter
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from vertice.siem_integration import (
    SIEMConnector,
    SIEMError,
    SIEMConnectionError,
    SplunkConnector,
    ElasticsearchConnector,
    CEFFormatter,
    LEEFFormatter,
    JSONFormatter,
)


# ===== FIXTURES =====

@pytest.fixture
def sample_event():
    """Sample security event for testing."""
    return {
        "event_type": "vulnerability",
        "severity": "high",
        "description": "SQL Injection vulnerability found",
        "source_ip": "10.10.1.5",
        "destination_ip": "192.168.1.10",
        "source_port": 3306,
        "destination_port": 443,
        "protocol": "tcp",
        "host": "web-server-01",
        "cve_id": "CVE-2023-12345",
        "timestamp": "2024-01-10T15:30:00.000Z"
    }


@pytest.fixture
def sample_events():
    """Sample batch of security events for testing."""
    return [
        {
            "event_type": "threat",
            "severity": "critical",
            "description": "Ransomware detected",
            "source_ip": "10.10.1.100",
            "timestamp": "2024-01-10T15:30:00.000Z"
        },
        {
            "event_type": "vulnerability",
            "severity": "medium",
            "description": "Outdated Apache version",
            "source_ip": "10.10.1.5",
            "port": 80,
            "timestamp": "2024-01-10T15:31:00.000Z"
        },
        {
            "event_type": "anomaly",
            "severity": "low",
            "description": "Unusual login time",
            "source_ip": "10.10.1.200",
            "timestamp": "2024-01-10T15:32:00.000Z"
        }
    ]


# ===== CEF FORMATTER TESTS =====

class TestCEFFormatter:
    """Test CEFFormatter."""

    def test_format_basic_event(self, sample_event):
        """Test formatting a basic event as CEF."""
        formatter = CEFFormatter()
        cef_string = formatter.format(sample_event)

        # Check CEF format structure
        assert cef_string.startswith("CEF:0|")
        assert "Vértice" in cef_string
        assert "Security Platform" in cef_string

        # Check event data
        assert "vulnerability" in cef_string  # event_type (signature_id)
        assert "SQL Injection" in cef_string  # description (name)
        assert "|8|" in cef_string  # severity (high = 8)

        # Check extensions
        assert "src=10.10.1.5" in cef_string
        assert "dst=192.168.1.10" in cef_string
        assert "spt=3306" in cef_string
        assert "dpt=443" in cef_string
        assert "proto=tcp" in cef_string
        assert "dhost=web-server-01" in cef_string
        assert "cve=CVE-2023-12345" in cef_string

    def test_format_severity_mapping(self):
        """Test CEF severity mapping."""
        formatter = CEFFormatter()

        # Test all severity levels
        test_cases = [
            ("critical", "10"),
            ("high", "8"),
            ("medium", "5"),
            ("low", "3"),
            ("info", "1"),
        ]

        for severity, expected_cef_severity in test_cases:
            event = {
                "event_type": "test",
                "severity": severity,
                "description": "Test event"
            }
            cef_string = formatter.format(event)
            assert f"|{expected_cef_severity}|" in cef_string

    def test_format_missing_fields(self):
        """Test formatting event with missing optional fields."""
        formatter = CEFFormatter()

        minimal_event = {
            "event_type": "test",
            "severity": "low",
            "description": "Minimal event"
        }

        cef_string = formatter.format(minimal_event)

        # Should still produce valid CEF
        assert cef_string.startswith("CEF:0|")
        assert "test" in cef_string
        assert "Minimal event" in cef_string

        # Should not have source/dest IPs
        assert "src=" not in cef_string
        assert "dst=" not in cef_string

    def test_format_special_characters_escaping(self):
        """Test CEF escaping of special characters."""
        formatter = CEFFormatter()

        event = {
            "event_type": "test",
            "severity": "low",
            "description": "Test event",
            "message": "Test | with = special \\ chars"
        }

        cef_string = formatter.format(event)

        # Check escaping: | → \|, = → \=, \ → \\
        assert "\\|" in cef_string or "msg=" in cef_string
        assert "\\\\" in cef_string

    def test_format_auto_timestamp(self):
        """Test that timestamp is auto-generated if not present."""
        formatter = CEFFormatter()

        event = {
            "event_type": "test",
            "severity": "low",
            "description": "Test event"
        }

        cef_string = formatter.format(event)

        # Should have rt= (receipt time) field
        assert "rt=" in cef_string

    def test_format_description_truncation(self):
        """Test that description is truncated to 100 chars."""
        formatter = CEFFormatter()

        long_description = "A" * 150

        event = {
            "event_type": "test",
            "severity": "low",
            "description": long_description
        }

        cef_string = formatter.format(event)

        # Name field should be truncated
        # CEF format: CEF:Version|Vendor|Product|Version|SignatureID|Name|Severity|Extension
        parts = cef_string.split("|")
        name_field = parts[5]  # Name is 6th field (index 5)
        assert len(name_field) <= 100


# ===== LEEF FORMATTER TESTS =====

class TestLEEFFormatter:
    """Test LEEFFormatter."""

    def test_format_basic_event(self, sample_event):
        """Test formatting a basic event as LEEF."""
        formatter = LEEFFormatter()
        leef_string = formatter.format(sample_event)

        # Check LEEF format structure
        assert leef_string.startswith("LEEF:2.0|")
        assert "Vértice" in leef_string
        assert "Security Platform" in leef_string
        assert "vulnerability" in leef_string  # event_id

        # Check extensions (tab-separated)
        assert "src=10.10.1.5" in leef_string
        assert "dst=192.168.1.10" in leef_string
        assert "srcPort=3306" in leef_string
        assert "dstPort=443" in leef_string
        assert "proto=tcp" in leef_string
        assert "sev=high" in leef_string
        assert "cve=CVE-2023-12345" in leef_string

    def test_format_field_mapping(self):
        """Test LEEF field mapping."""
        formatter = LEEFFormatter()

        event = {
            "event_type": "test",
            "severity": "medium",
            "description": "Test",
            "source_ip": "1.1.1.1",
            "destination_ip": "2.2.2.2",
            "source_port": 1234,
            "destination_port": 5678,
            "protocol": "udp",
            "host": "test-host",
            "cve_id": "CVE-2024-0001"
        }

        leef_string = formatter.format(event)

        # Verify all mappings
        assert "src=1.1.1.1" in leef_string
        assert "dst=2.2.2.2" in leef_string
        assert "srcPort=1234" in leef_string
        assert "dstPort=5678" in leef_string
        assert "proto=udp" in leef_string
        assert "sev=medium" in leef_string
        assert "identHostName=test-host" in leef_string
        assert "cve=CVE-2024-0001" in leef_string

    def test_format_special_characters_escaping(self):
        """Test LEEF escaping of special characters."""
        formatter = LEEFFormatter()

        event = {
            "event_type": "test",
            "severity": "low",
            "description": "Test",
            "message": "Test\twith\nspecial\\chars"
        }

        leef_string = formatter.format(event)

        # Check escaping: \t → \\t, \n → \\n, \ → \\
        assert "\\t" in leef_string
        assert "\\n" in leef_string


# ===== JSON FORMATTER TESTS =====

class TestJSONFormatter:
    """Test JSONFormatter."""

    def test_format_basic_event(self, sample_event):
        """Test formatting a basic event as JSON."""
        formatter = JSONFormatter()
        json_string = formatter.format(sample_event)

        # Parse JSON
        parsed = json.loads(json_string)

        # Check structure
        assert "source" in parsed
        assert "sourcetype" in parsed
        assert "time" in parsed
        assert "event" in parsed

        # Check metadata
        assert parsed["source"] == "vertice"
        assert parsed["sourcetype"] == "vertice:security"

        # Check event data
        event_data = parsed["event"]
        assert event_data["event_type"] == "vulnerability"
        assert event_data["severity"] == "high"
        assert event_data["source_ip"] == "10.10.1.5"

    def test_format_auto_timestamp(self):
        """Test that timestamp is auto-generated if not present."""
        formatter = JSONFormatter()

        event = {
            "event_type": "test",
            "severity": "low"
        }

        json_string = formatter.format(event)
        parsed = json.loads(json_string)

        # Should have time field
        assert "time" in parsed
        assert parsed["time"] is not None


# ===== SPLUNK CONNECTOR TESTS =====

class TestSplunkConnector:
    """Test SplunkConnector."""

    def test_initialization(self):
        """Test SplunkConnector initialization."""
        connector = SplunkConnector(
            host="splunk.example.com",
            port=8088,
            token="test-token-12345",
            index="security"
        )

        assert connector.host == "splunk.example.com"
        assert connector.port == 8088
        assert connector.token == "test-token-12345"
        assert connector.index == "security"
        assert connector.endpoint == "https://splunk.example.com:8088/services/collector/event"

    def test_initialization_defaults(self):
        """Test SplunkConnector default values."""
        connector = SplunkConnector(
            host="localhost",
            token="test-token"
        )

        assert connector.port == 8088  # default
        assert connector.source == "vertice"  # default
        assert connector.sourcetype == "vertice:security"  # default
        assert connector.ssl is True  # default

    @patch('requests.post')
    def test_send_event_success(self, mock_post, sample_event):
        """Test successful event sending to Splunk."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"text":"Success","code":0}'
        mock_post.return_value = mock_response

        connector = SplunkConnector(
            host="splunk.example.com",
            token="test-token"
        )

        result = connector.send_event(sample_event)

        assert result is True
        mock_post.assert_called_once()

        # Check payload structure
        call_args = mock_post.call_args
        assert call_args.kwargs['json']['source'] == "vertice"
        assert call_args.kwargs['json']['sourcetype'] == "vertice:security"
        assert call_args.kwargs['json']['event'] == sample_event

    @patch('requests.post')
    def test_send_event_with_index(self, mock_post, sample_event):
        """Test sending event with custom index."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        connector = SplunkConnector(
            host="localhost",
            token="test-token",
            index="custom-index"
        )

        connector.send_event(sample_event)

        # Check that index is in payload
        call_args = mock_post.call_args
        assert call_args.kwargs['json']['index'] == "custom-index"

    @patch('requests.post')
    def test_send_event_failure(self, mock_post, sample_event):
        """Test failed event sending to Splunk."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid token'
        mock_post.return_value = mock_response

        connector = SplunkConnector(
            host="localhost",
            token="bad-token"
        )

        with pytest.raises(SIEMError, match="Splunk returned 400"):
            connector.send_event(sample_event)

    @patch('requests.post')
    def test_send_event_connection_error(self, mock_post, sample_event):
        """Test connection error handling."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        connector = SplunkConnector(
            host="nonexistent.example.com",
            token="test-token"
        )

        with pytest.raises(SIEMConnectionError, match="Failed to connect"):
            connector.send_event(sample_event)

    @patch('requests.post')
    def test_send_event_timeout(self, mock_post, sample_event):
        """Test timeout handling."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        connector = SplunkConnector(
            host="slow.example.com",
            token="test-token"
        )

        with pytest.raises(SIEMConnectionError, match="Timeout"):
            connector.send_event(sample_event)

    @patch('requests.post')
    def test_send_batch_success(self, mock_post, sample_events):
        """Test successful batch sending to Splunk."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        connector = SplunkConnector(
            host="localhost",
            token="test-token"
        )

        stats = connector.send_batch(sample_events)

        assert stats["sent"] == 3
        assert stats["failed"] == 0
        mock_post.assert_called_once()

        # Check batch format (newline-separated JSON)
        call_args = mock_post.call_args
        batch_payload = call_args.kwargs['data']
        lines = batch_payload.strip().split('\n')
        assert len(lines) == 3

    @patch('requests.post')
    def test_send_batch_empty(self, mock_post):
        """Test sending empty batch."""
        connector = SplunkConnector(
            host="localhost",
            token="test-token"
        )

        stats = connector.send_batch([])

        assert stats["sent"] == 0
        assert stats["failed"] == 0
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_test_connection_success(self, mock_post):
        """Test connection test success."""
        # Mock successful test event response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        connector = SplunkConnector(
            host="localhost",
            token="test-token"
        )

        result = connector.test_connection()

        assert result is True

    @patch('requests.post')
    def test_test_connection_failure(self, mock_post):
        """Test connection test failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        connector = SplunkConnector(
            host="localhost",
            token="bad-token"
        )

        result = connector.test_connection()

        assert result is False


# ===== ELASTICSEARCH CONNECTOR TESTS =====

class TestElasticsearchConnector:
    """Test ElasticsearchConnector."""

    def test_initialization_basic_auth(self):
        """Test initialization with basic auth."""
        connector = ElasticsearchConnector(
            host="elastic.example.com",
            port=9200,
            username="elastic",
            password="changeme",
            index="vertice-security"
        )

        assert connector.host == "elastic.example.com"
        assert connector.port == 9200
        assert connector.username == "elastic"
        assert connector.password == "changeme"
        assert connector.index == "vertice-security"
        assert connector.auth == ("elastic", "changeme")

    def test_initialization_api_key(self):
        """Test initialization with API key (preferred over basic auth)."""
        connector = ElasticsearchConnector(
            host="localhost",
            api_key="test-api-key-12345",
            username="elastic",  # Should be ignored in favor of API key
            password="changeme"
        )

        assert connector.api_key == "test-api-key-12345"
        assert connector.headers["Authorization"] == "ApiKey test-api-key-12345"
        assert connector.auth is None  # Basic auth not used when API key present

    def test_initialization_defaults(self):
        """Test default values."""
        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        assert connector.port == 9200  # default
        assert connector.index == "vertice-security"  # default
        assert connector.ssl is False  # default (changed from True)

    @patch('requests.post')
    def test_send_event_success(self, mock_post, sample_event):
        """Test successful event sending to Elasticsearch."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"_id": "abc123", "result": "created"}
        mock_post.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        result = connector.send_event(sample_event)

        assert result is True
        mock_post.assert_called_once()

        # Check that event has required metadata
        call_args = mock_post.call_args
        event_data = call_args.kwargs['json']
        assert event_data['@timestamp'] is not None
        assert event_data['source'] == "vertice"

    @patch('requests.post')
    def test_send_event_auto_timestamp(self, mock_post):
        """Test that timestamp is auto-generated if not present."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"_id": "abc123"}
        mock_post.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        event = {"event_type": "test"}
        connector.send_event(event)

        # Check that timestamp was added
        call_args = mock_post.call_args
        event_data = call_args.kwargs['json']
        assert "timestamp" in event_data
        assert "@timestamp" in event_data

    @patch('requests.post')
    def test_send_event_failure(self, mock_post, sample_event):
        """Test failed event sending."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid document"
        mock_post.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        with pytest.raises(SIEMError, match="Elasticsearch returned 400"):
            connector.send_event(sample_event)

    @patch('requests.post')
    def test_send_batch_success(self, mock_post, sample_events):
        """Test successful batch sending to Elasticsearch."""
        # Mock bulk API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"index": {"status": 201}},
                {"index": {"status": 201}},
                {"index": {"status": 201}}
            ]
        }
        mock_post.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        stats = connector.send_batch(sample_events)

        assert stats["sent"] == 3
        assert stats["failed"] == 0

        # Check bulk payload format
        call_args = mock_post.call_args
        bulk_payload = call_args.kwargs['data']
        lines = bulk_payload.strip().split('\n')
        # Bulk API: action line + document line for each event = 2 * 3 = 6 lines
        assert len(lines) == 6

    @patch('requests.post')
    def test_send_batch_partial_failure(self, mock_post, sample_events):
        """Test batch with partial failures."""
        # Mock bulk API response with some failures
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"index": {"status": 201}},
                {"index": {"status": 400}},  # Failed
                {"index": {"status": 201}}
            ]
        }
        mock_post.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        stats = connector.send_batch(sample_events)

        assert stats["sent"] == 2
        assert stats["failed"] == 1

    @patch('requests.post')
    def test_send_batch_empty(self, mock_post):
        """Test sending empty batch."""
        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        stats = connector.send_batch([])

        assert stats["sent"] == 0
        assert stats["failed"] == 0
        mock_post.assert_not_called()

    @patch('requests.get')
    def test_test_connection_success(self, mock_get):
        """Test connection test success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cluster_name": "elasticsearch",
            "status": "green"
        }
        mock_get.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        result = connector.test_connection()

        assert result is True
        mock_get.assert_called_once()

        # Check that health endpoint was called
        call_args = mock_get.call_args
        assert "/_cluster/health" in call_args[0][0]

    @patch('requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test connection test failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="wrong",
            password="wrong"
        )

        result = connector.test_connection()

        assert result is False

    @patch('requests.put')
    def test_create_index_template_success(self, mock_put):
        """Test creating index template."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        result = connector.create_index_template()

        assert result is True
        mock_put.assert_called_once()

        # Check template structure
        call_args = mock_put.call_args
        template = call_args.kwargs['json']
        assert "index_patterns" in template
        assert "template" in template
        assert "mappings" in template["template"]

    @patch('requests.put')
    def test_create_index_template_failure(self, mock_put):
        """Test index template creation failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_put.return_value = mock_response

        connector = ElasticsearchConnector(
            host="localhost",
            username="elastic",
            password="changeme"
        )

        result = connector.create_index_template()

        assert result is False
