"""Comprehensive unit tests for NarrativeEngine.

Tests cover initialization, narrative generation, anomaly detection, and error handling
to achieve 90%+ code coverage.

Author: Vértice Platform Team
License: Proprietary
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core.narrative_engine import NarrativeEngine


class TestNarrativeEngineInitialization:
    """Test NarrativeEngine initialization."""

    def test_initialization_valid_api_key(self):
        """Test narrative engine initializes with valid API key."""
        engine = NarrativeEngine(
            anthropic_api_key="sk-ant-test-key-123", model="claude-sonnet-4-5-20250929"
        )

        assert engine.anthropic_api_key == "sk-ant-test-key-123"
        assert engine.model == "claude-sonnet-4-5-20250929"
        assert engine.client is None
        assert engine._initialized is False

    def test_initialization_default_model(self):
        """Test initialization with default model."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        assert engine.model == "claude-sonnet-4-5-20250929"

    def test_initialization_custom_model(self):
        """Test initialization with custom model."""
        engine = NarrativeEngine(
            anthropic_api_key="sk-ant-test-key-123", model="claude-opus-4-20250514"
        )

        assert engine.model == "claude-opus-4-20250514"

    def test_initialization_empty_api_key_raises_error(self):
        """Test initialization with empty API key raises ValueError."""
        with pytest.raises(ValueError, match="Valid ANTHROPIC_API_KEY required"):
            NarrativeEngine(anthropic_api_key="")

    def test_initialization_placeholder_api_key_raises_error(self):
        """Test initialization with placeholder API key raises ValueError."""
        with pytest.raises(ValueError, match="Valid ANTHROPIC_API_KEY required"):
            NarrativeEngine(anthropic_api_key="PLACEHOLDER")

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful engine initialization."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        with patch(
            "core.narrative_engine.AsyncAnthropic"
        ) as mock_anthropic:
            # Mock client
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock()
            mock_anthropic.return_value = mock_client

            result = await engine.initialize()

            assert result is True
            assert engine._initialized is True
            assert engine.client is not None
            mock_anthropic.assert_called_once_with(api_key="sk-ant-test-key-123")
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_api_validation_fails(self):
        """Test initialization handles API validation failure."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-invalid-key")

        with patch(
            "core.narrative_engine.AsyncAnthropic"
        ) as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock(
                side_effect=Exception("Invalid API key")
            )
            mock_anthropic.return_value = mock_client

            result = await engine.initialize()

            assert result is False
            assert engine._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_client_creation_fails(self):
        """Test initialization handles client creation failure."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        with patch(
            "core.narrative_engine.AsyncAnthropic"
        ) as mock_anthropic:
            mock_anthropic.side_effect = Exception("Client creation failed")

            result = await engine.initialize()

            assert result is False
            assert engine._initialized is False


class TestGenerateNarrative:
    """Test generate_narrative method."""

    @pytest.mark.asyncio
    async def test_generate_narrative_not_initialized_raises_error(self):
        """Test generate_narrative raises error when not initialized."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = False

        with pytest.raises(RuntimeError, match="NarrativeEngine not initialized"):
            await engine.generate_narrative(
                narrative_type="realtime", metrics_data={"metrics": []}
            )

    @pytest.mark.asyncio
    async def test_generate_narrative_no_client_raises_error(self):
        """Test generate_narrative raises error when client is None."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True
        engine.client = None

        with pytest.raises(RuntimeError, match="NarrativeEngine not initialized"):
            await engine.generate_narrative(
                narrative_type="realtime", metrics_data={"metrics": []}
            )

    @pytest.mark.asyncio
    async def test_generate_narrative_realtime_success(self):
        """Test successful realtime narrative generation."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        # Mock Anthropic client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(
                text="System is running smoothly with normal CPU and memory usage."
            )
        ]
        mock_message.usage = MagicMock(input_tokens=150, output_tokens=50)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        metrics_data = {
            "metrics": [
                {"name": "cpu_usage", "value": 45, "unit": "%"},
                {"name": "memory_usage", "value": 60, "unit": "%"},
            ]
        }

        result = await engine.generate_narrative(
            narrative_type="realtime", metrics_data=metrics_data, time_range_minutes=60
        )

        assert (
            result["narrative"]
            == "System is running smoothly with normal CPU and memory usage."
        )
        assert result["metrics_analyzed"] == 2
        assert result["anomalies_detected"] == 0
        assert result["time_range_minutes"] == 60
        assert result["narrative_type"] == "realtime"
        assert result["tokens_used"] == 200
        assert "timestamp" in result
        assert result["model"] == "claude-sonnet-4-5-20250929"

    @pytest.mark.asyncio
    async def test_generate_narrative_summary_with_focus_areas(self):
        """Test summary narrative generation with focus areas."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text="Database performance analysis complete.")
        ]
        mock_message.usage = MagicMock(input_tokens=200, output_tokens=100)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        metrics_data = {
            "metrics": [
                {"name": "db_connections", "value": 25, "unit": ""},
                {"name": "query_latency", "value": 150, "unit": "ms"},
            ]
        }

        result = await engine.generate_narrative(
            narrative_type="summary",
            metrics_data=metrics_data,
            time_range_minutes=120,
            focus_areas=["database", "performance"],
        )

        assert result["narrative"] == "Database performance analysis complete."
        assert result["focus_areas"] == ["database", "performance"]
        assert result["narrative_type"] == "summary"
        assert result["tokens_used"] == 300

    @pytest.mark.asyncio
    async def test_generate_narrative_alert_with_anomalies(self):
        """Test alert narrative generation with detected anomalies."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text="Critical: CPU usage at 95%. Immediate action required.")
        ]
        mock_message.usage = MagicMock(input_tokens=180, output_tokens=80)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        metrics_data = {
            "metrics": [
                {"name": "cpu_usage", "value": 95, "unit": "%"},
                {"name": "memory_usage", "value": 85, "unit": "%"},
            ]
        }

        result = await engine.generate_narrative(
            narrative_type="alert", metrics_data=metrics_data, time_range_minutes=15
        )

        assert (
            result["narrative"]
            == "Critical: CPU usage at 95%. Immediate action required."
        )
        assert result["anomalies_detected"] == 2  # CPU critical + memory warning
        assert len(result["anomalies"]) == 2
        assert result["narrative_type"] == "alert"

    @pytest.mark.asyncio
    async def test_generate_narrative_briefing(self):
        """Test briefing narrative generation."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text="Executive summary: All systems operational.")
        ]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=40)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        metrics_data = {
            "metrics": [{"name": "system_health", "value": 100, "unit": "%"}],
            "services": [
                {"name": "api", "status": "healthy"},
                {"name": "database", "status": "healthy"},
            ],
        }

        result = await engine.generate_narrative(
            narrative_type="briefing", metrics_data=metrics_data
        )

        assert result["narrative"] == "Executive summary: All systems operational."
        assert result["narrative_type"] == "briefing"

    @pytest.mark.asyncio
    async def test_generate_narrative_empty_content(self):
        """Test narrative generation with empty message content."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = []
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=0)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        result = await engine.generate_narrative(
            narrative_type="realtime", metrics_data={"metrics": []}
        )

        assert result["narrative"] == "No narrative generated"

    @pytest.mark.asyncio
    async def test_generate_narrative_api_error(self):
        """Test narrative generation handles API errors."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )
        engine.client = mock_client

        with pytest.raises(Exception, match="API rate limit exceeded"):
            await engine.generate_narrative(
                narrative_type="realtime", metrics_data={"metrics": []}
            )

    @pytest.mark.asyncio
    async def test_generate_narrative_with_anomalies_in_data(self):
        """Test narrative generation with pre-existing anomalies in metrics data."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Error rate spike detected.")]
        mock_message.usage = MagicMock(input_tokens=150, output_tokens=50)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        metrics_data = {
            "metrics": [{"name": "error_rate", "value": 8, "unit": "%"}],
            "anomalies": [{"description": "High error rate detected"}],
        }

        result = await engine.generate_narrative(
            narrative_type="alert", metrics_data=metrics_data
        )

        assert result["anomalies_detected"] == 1  # From _detect_anomalies_in_metrics
        assert result["narrative"] == "Error rate spike detected."


class TestDetectAnomaliesInMetrics:
    """Test _detect_anomalies_in_metrics method."""

    def test_detect_cpu_critical_anomaly(self):
        """Test detection of critical CPU usage anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "cpu_usage", "value": 95}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["metric"] == "cpu_usage"
        assert anomalies[0]["value"] == 95
        assert anomalies[0]["severity"] == "critical"
        assert "Critical CPU usage: 95%" in anomalies[0]["description"]

    def test_detect_cpu_warning_anomaly(self):
        """Test detection of warning-level CPU usage anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "system_cpu_usage", "value": 80}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "warning"
        assert "High CPU usage: 80%" in anomalies[0]["description"]

    def test_detect_memory_critical_anomaly(self):
        """Test detection of critical memory usage anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "memory_usage", "value": 92}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["metric"] == "memory_usage"
        assert anomalies[0]["value"] == 92
        assert anomalies[0]["severity"] == "critical"
        assert "Critical memory usage: 92%" in anomalies[0]["description"]

    def test_detect_memory_warning_anomaly(self):
        """Test detection of warning-level memory usage anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "heap_memory_usage", "value": 85}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "warning"
        assert "High memory usage: 85%" in anomalies[0]["description"]

    def test_detect_error_rate_critical_anomaly(self):
        """Test detection of critical error rate anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "error_rate", "value": 10}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["metric"] == "error_rate"
        assert anomalies[0]["value"] == 10
        assert anomalies[0]["severity"] == "critical"
        assert "High error rate: 10%" in anomalies[0]["description"]

    def test_detect_error_rate_warning_anomaly(self):
        """Test detection of warning-level error rate anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "api_error_rate", "value": 3}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "warning"
        assert "Elevated error rate: 3%" in anomalies[0]["description"]

    def test_detect_latency_critical_anomaly(self):
        """Test detection of critical latency anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "api_latency", "value": 5500}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["metric"] == "api_latency"
        assert anomalies[0]["value"] == 5500
        assert anomalies[0]["severity"] == "critical"
        assert "Critical latency: 5500ms" in anomalies[0]["description"]

    def test_detect_latency_warning_anomaly(self):
        """Test detection of warning-level latency anomaly."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "response_time", "value": 3000}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "warning"
        assert "High latency: 3000ms" in anomalies[0]["description"]

    def test_detect_multiple_anomalies(self):
        """Test detection of multiple anomalies at once."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {
            "metrics": [
                {"name": "cpu_usage", "value": 92},
                {"name": "memory_usage", "value": 88},
                {"name": "error_rate", "value": 6},
                {"name": "latency", "value": 4000},
            ]
        }

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 4
        assert any(a["metric"] == "cpu_usage" for a in anomalies)
        assert any(a["metric"] == "memory_usage" for a in anomalies)
        assert any(a["metric"] == "error_rate" for a in anomalies)
        assert any(a["metric"] == "latency" for a in anomalies)

    def test_detect_no_anomalies(self):
        """Test detection with normal metrics - no anomalies."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {
            "metrics": [
                {"name": "cpu_usage", "value": 45},
                {"name": "memory_usage", "value": 60},
                {"name": "error_rate", "value": 0.5},
                {"name": "latency", "value": 150},
            ]
        }

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 0

    def test_detect_anomalies_empty_metrics(self):
        """Test detection with empty metrics list."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": []}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 0

    def test_detect_anomalies_missing_name(self):
        """Test detection with metrics missing name field."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"value": 95}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 0

    def test_detect_anomalies_missing_value(self):
        """Test detection with metrics missing value field."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": [{"name": "cpu_usage"}]}

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 0

    def test_detect_anomalies_case_insensitive(self):
        """Test anomaly detection is case-insensitive."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {
            "metrics": [
                {"name": "CPU_USAGE", "value": 92},
                {"name": "Memory_Usage", "value": 88},
            ]
        }

        anomalies = engine._detect_anomalies_in_metrics(metrics_data)

        assert len(anomalies) == 2


class TestGetSystemPrompt:
    """Test _get_system_prompt method."""

    def test_get_system_prompt_returns_string(self):
        """Test system prompt returns a non-empty string."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        prompt = engine._get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_system_prompt_contains_mvp_role(self):
        """Test system prompt identifies MVP role."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        prompt = engine._get_system_prompt()

        assert "MAXIMUS Vision Protocol" in prompt
        assert "MVP" in prompt

    def test_get_system_prompt_contains_guidelines(self):
        """Test system prompt contains generation guidelines."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        prompt = engine._get_system_prompt()

        assert "Guidelines:" in prompt
        assert "concise" in prompt.lower()
        assert "actionable insights" in prompt.lower()

    def test_get_system_prompt_contains_narrative_types(self):
        """Test system prompt defines narrative types."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        prompt = engine._get_system_prompt()

        assert "realtime" in prompt
        assert "summary" in prompt
        assert "alert" in prompt
        assert "briefing" in prompt


class TestBuildNarrativePrompt:
    """Test _build_narrative_prompt method."""

    def test_build_prompt_basic_structure(self):
        """Test prompt builds with basic structure."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": []}

        prompt = engine._build_narrative_prompt(
            narrative_type="realtime",
            metrics_data=metrics_data,
            time_range_minutes=60,
            focus_areas=None,
        )

        assert "realtime narrative" in prompt
        assert "Last 60 minutes" in prompt
        assert "System Metrics" in prompt

    def test_build_prompt_with_focus_areas(self):
        """Test prompt includes focus areas when provided."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": []}

        prompt = engine._build_narrative_prompt(
            narrative_type="summary",
            metrics_data=metrics_data,
            time_range_minutes=120,
            focus_areas=["database", "api"],
        )

        assert "Focus Areas: database, api" in prompt

    def test_build_prompt_with_metrics(self):
        """Test prompt includes metric details."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {
            "metrics": [
                {"name": "cpu_usage", "value": 45, "unit": "%"},
                {"name": "memory_usage", "value": 60, "unit": "%"},
            ]
        }

        prompt = engine._build_narrative_prompt(
            narrative_type="realtime",
            metrics_data=metrics_data,
            time_range_minutes=60,
            focus_areas=None,
        )

        assert "cpu_usage: 45 %" in prompt
        assert "memory_usage: 60 %" in prompt

    def test_build_prompt_limits_metrics_to_20(self):
        """Test prompt limits metrics to top 20."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        # Create 30 metrics
        metrics_list = [
            {"name": f"metric_{i}", "value": i, "unit": ""} for i in range(30)
        ]

        metrics_data = {"metrics": metrics_list}

        prompt = engine._build_narrative_prompt(
            narrative_type="summary",
            metrics_data=metrics_data,
            time_range_minutes=60,
            focus_areas=None,
        )

        # Count how many metrics appear in prompt
        metric_count = sum(1 for i in range(30) if f"metric_{i}" in prompt)
        assert metric_count <= 20

    def test_build_prompt_with_empty_metrics(self):
        """Test prompt handles empty metrics list."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": []}

        prompt = engine._build_narrative_prompt(
            narrative_type="realtime",
            metrics_data=metrics_data,
            time_range_minutes=60,
            focus_areas=None,
        )

        assert "No metrics available" in prompt

    def test_build_prompt_with_anomalies(self):
        """Test prompt includes anomaly information."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {
            "metrics": [],
            "anomalies": [
                {"description": "High CPU usage detected"},
                {"description": "Memory leak suspected"},
            ],
        }

        prompt = engine._build_narrative_prompt(
            narrative_type="alert",
            metrics_data=metrics_data,
            time_range_minutes=15,
            focus_areas=None,
        )

        assert "Detected Anomalies" in prompt
        assert "High CPU usage detected" in prompt
        assert "Memory leak suspected" in prompt

    def test_build_prompt_limits_anomalies_to_10(self):
        """Test prompt limits anomalies to top 10."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        anomalies_list = [{"description": f"Anomaly {i}"} for i in range(15)]

        metrics_data = {"metrics": [], "anomalies": anomalies_list}

        prompt = engine._build_narrative_prompt(
            narrative_type="alert",
            metrics_data=metrics_data,
            time_range_minutes=30,
            focus_areas=None,
        )

        # Count how many anomalies appear
        anomaly_count = sum(1 for i in range(15) if f"Anomaly {i}" in prompt)
        assert anomaly_count <= 10

    def test_build_prompt_with_services(self):
        """Test prompt includes service status."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {
            "metrics": [],
            "services": [
                {"name": "api-service", "status": "healthy"},
                {"name": "db-service", "status": "degraded"},
            ],
        }

        prompt = engine._build_narrative_prompt(
            narrative_type="briefing",
            metrics_data=metrics_data,
            time_range_minutes=60,
            focus_areas=None,
        )

        assert "Service Status" in prompt
        assert "api-service: healthy" in prompt
        assert "db-service: degraded" in prompt

    def test_build_prompt_includes_task_section(self):
        """Test prompt includes task instructions."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {"metrics": []}

        prompt = engine._build_narrative_prompt(
            narrative_type="summary",
            metrics_data=metrics_data,
            time_range_minutes=60,
            focus_areas=None,
        )

        assert "Task" in prompt
        assert "Analyze the metrics" in prompt
        assert "summary narrative" in prompt

    def test_build_prompt_handles_missing_metric_fields(self):
        """Test prompt handles metrics with missing fields."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        metrics_data = {
            "metrics": [
                {"name": "cpu_usage", "value": 45},  # Missing unit
                {"value": 60, "unit": "%"},  # Missing name
                {},  # Missing everything
            ]
        }

        prompt = engine._build_narrative_prompt(
            narrative_type="realtime",
            metrics_data=metrics_data,
            time_range_minutes=60,
            focus_areas=None,
        )

        assert "cpu_usage: 45" in prompt
        assert "unknown: 60 %" in prompt


class TestHealthCheck:
    """Test health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check when engine is healthy."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True
        engine.client = MagicMock()

        result = await engine.health_check()

        assert result["status"] == "healthy"
        assert result["initialized"] is True
        assert result["model"] == "claude-sonnet-4-5-20250929"
        assert result["client_connected"] is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """Test health check when engine not initialized."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = False
        engine.client = None

        result = await engine.health_check()

        assert result["status"] == "unhealthy"
        assert result["initialized"] is False
        assert result["client_connected"] is False

    @pytest.mark.asyncio
    async def test_health_check_no_client(self):
        """Test health check when client is None."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True
        engine.client = None

        result = await engine.health_check()

        assert result["status"] == "healthy"  # Still marked healthy if initialized
        assert result["initialized"] is True
        assert result["client_connected"] is False


class TestShutdown:
    """Test shutdown method."""

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful shutdown."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        engine.client = mock_client

        await engine.shutdown()

        mock_client.close.assert_called_once()
        assert engine.client is None
        assert engine._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_no_client(self):
        """Test shutdown when no client exists."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True
        engine.client = None

        # Should not raise exception
        await engine.shutdown()

        assert engine.client is None
        assert engine._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_not_initialized(self):
        """Test shutdown when not initialized."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = False
        engine.client = None

        await engine.shutdown()

        assert engine._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_client_close_error(self):
        """Test shutdown propagates client close errors."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_client.close = AsyncMock(side_effect=Exception("Close failed"))
        engine.client = mock_client

        # The shutdown method doesn't catch exceptions, so it will propagate
        with pytest.raises(Exception, match="Close failed"):
            await engine.shutdown()


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_generate_narrative_with_very_long_metrics_list(self):
        """Test narrative generation with many metrics."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="System analysis complete.")]
        mock_message.usage = MagicMock(input_tokens=500, output_tokens=100)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        # Create 100 metrics
        metrics_list = [
            {"name": f"metric_{i}", "value": i, "unit": ""} for i in range(100)
        ]

        metrics_data = {"metrics": metrics_list}

        result = await engine.generate_narrative(
            narrative_type="summary", metrics_data=metrics_data
        )

        assert result["metrics_analyzed"] == 100
        assert result["narrative"] == "System analysis complete."

    def test_detect_anomalies_boundary_values(self):
        """Test anomaly detection at exact threshold boundaries."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        # Test CPU at exactly 90 (should be warning, not critical, since > 90 is critical)
        metrics_data = {"metrics": [{"name": "cpu_usage", "value": 90}]}
        anomalies = engine._detect_anomalies_in_metrics(metrics_data)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "warning"  # 90 is > 75 but not > 90

        # Test CPU at 91 (should be critical)
        metrics_data = {"metrics": [{"name": "cpu_usage", "value": 91}]}
        anomalies = engine._detect_anomalies_in_metrics(metrics_data)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "critical"

        # Test memory at exactly 80 (should not trigger)
        metrics_data = {"metrics": [{"name": "memory_usage", "value": 80}]}
        anomalies = engine._detect_anomalies_in_metrics(metrics_data)
        assert len(anomalies) == 0

        # Test memory at 81 (should be warning)
        metrics_data = {"metrics": [{"name": "memory_usage", "value": 81}]}
        anomalies = engine._detect_anomalies_in_metrics(metrics_data)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "warning"

    @pytest.mark.asyncio
    async def test_generate_narrative_with_special_characters_in_metrics(self):
        """Test narrative generation with special characters in metric names."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Metrics processed.")]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        metrics_data = {
            "metrics": [
                {"name": "api/v1/users:cpu_usage", "value": 45, "unit": "%"},
                {"name": "db-connection-pool", "value": 10, "unit": ""},
            ]
        }

        result = await engine.generate_narrative(
            narrative_type="realtime", metrics_data=metrics_data
        )

        assert result["metrics_analyzed"] == 2

    @pytest.mark.asyncio
    async def test_initialize_multiple_times(self):
        """Test calling initialize multiple times."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")

        with patch(
            "core.narrative_engine.AsyncAnthropic"
        ) as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock()
            mock_anthropic.return_value = mock_client

            # First initialization
            result1 = await engine.initialize()
            assert result1 is True

            # Second initialization (should still work)
            result2 = await engine.initialize()
            assert result2 is True

            # Should have created client twice
            assert mock_anthropic.call_count == 2

    def test_model_selection_preserved(self):
        """Test that custom model selection is preserved."""
        custom_model = "claude-3-opus-20240229"
        engine = NarrativeEngine(
            anthropic_api_key="sk-ant-test-key-123", model=custom_model
        )

        assert engine.model == custom_model

    @pytest.mark.asyncio
    async def test_generate_narrative_different_time_ranges(self):
        """Test narrative generation with various time ranges."""
        engine = NarrativeEngine(anthropic_api_key="sk-ant-test-key-123")
        engine._initialized = True

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Analysis complete.")]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        engine.client = mock_client

        metrics_data = {"metrics": []}

        # Test different time ranges
        for time_range in [5, 15, 30, 60, 120, 1440]:
            result = await engine.generate_narrative(
                narrative_type="realtime",
                metrics_data=metrics_data,
                time_range_minutes=time_range,
            )
            assert result["time_range_minutes"] == time_range
