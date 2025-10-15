"""Unit tests for PatternDetectorRefactored.

Tests the production-hardened Pattern Detector with 100% coverage.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
from datetime import datetime, timezone

from analyzers.pattern_detector_refactored import PatternDetectorRefactored


@pytest.fixture(autouse=True)
def mock_cache_globally(monkeypatch):
    """Global fixture to mock cache operations."""
    async def get_mock(self, key):
        return None

    async def set_mock(self, key, value):
        pass

    from core.cache_manager import CacheManager
    monkeypatch.setattr(CacheManager, "get", get_mock)
    monkeypatch.setattr(CacheManager, "set", set_mock)


class TestPatternDetectorBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_detector_initialization(self):
        """Test detector initializes correctly."""
        detector = PatternDetectorRefactored()

        assert detector.total_detections == 0
        assert detector.total_patterns_found == 0
        assert len(detector.pattern_definitions) > 0
        assert detector.logger is not None
        assert detector.metrics is not None

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method."""
        detector = PatternDetectorRefactored()

        repr_str = repr(detector)

        assert "PatternDetectorRefactored" in repr_str
        assert "detections=0" in repr_str
        assert "patterns_found=0" in repr_str


class TestInputValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_query_without_data_raises_error(self):
        """Test querying without data raises ValueError."""
        detector = PatternDetectorRefactored()

        with pytest.raises(ValueError, match="Data parameter is required"):
            await detector.query(target="user_123")

    @pytest.mark.asyncio
    async def test_query_with_invalid_data_type_raises_error(self):
        """Test querying with non-dict data raises ValueError."""
        detector = PatternDetectorRefactored()

        with pytest.raises(ValueError, match="Data must be a dictionary"):
            await detector.query(target="user_123", data="not a dict")


class TestTemporalPatterns:
    """Temporal pattern detection tests."""

    @pytest.mark.asyncio
    async def test_detect_unusual_login_time_early_morning(self):
        """Test detection of early morning login (outside normal hours)."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={"login_hour": 3},
            pattern_types=["temporal"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["pattern"] == "unusual_login_time"
        assert result["detected_patterns"][0]["type"] == "temporal"
        assert result["detected_patterns"][0]["severity"] == "medium"
        assert "3:00" in result["detected_patterns"][0]["description"]

    @pytest.mark.asyncio
    async def test_detect_unusual_login_time_late_night(self):
        """Test detection of late night login (outside normal hours)."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={"login_hour": 23},
            pattern_types=["temporal"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["pattern"] == "unusual_login_time"
        assert result["detected_patterns"][0]["details"]["login_hour"] == 23

    @pytest.mark.asyncio
    async def test_no_temporal_pattern_during_normal_hours(self):
        """Test no pattern detected during normal hours."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_789",
            data={"login_hour": 14},  # 2 PM - normal
            pattern_types=["temporal"]
        )

        assert result["pattern_count"] == 0
        assert result["assessment"] == "No significant patterns detected."


class TestBehavioralPatterns:
    """Behavioral pattern detection tests."""

    @pytest.mark.asyncio
    async def test_detect_repeated_failed_logins(self):
        """Test detection of repeated failed login attempts."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={"failed_login_attempts": 10},
            pattern_types=["behavioral"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["pattern"] == "repeated_failed_logins"
        assert result["detected_patterns"][0]["type"] == "behavioral"
        assert result["detected_patterns"][0]["severity"] == "high"
        assert "10 failed login attempts" in result["detected_patterns"][0]["description"]

    @pytest.mark.asyncio
    async def test_detect_repeated_failed_logins_at_threshold(self):
        """Test detection at exact threshold."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={"failed_login_attempts": 5},  # Exactly at threshold
            pattern_types=["behavioral"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["details"]["failed_attempts"] == 5

    @pytest.mark.asyncio
    async def test_no_behavioral_pattern_below_threshold(self):
        """Test no pattern detected below threshold."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_789",
            data={"failed_login_attempts": 3},  # Below threshold of 5
            pattern_types=["behavioral"]
        )

        assert result["pattern_count"] == 0


class TestSpatialPatterns:
    """Spatial pattern detection tests."""

    @pytest.mark.asyncio
    async def test_detect_geospatial_anomaly_impossible_travel(self):
        """Test detection of impossible travel (supersonic speed)."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={
                "locations": ["New York", "London"],
                "distance_km": 5570,  # NYC to London
                "time_diff_hours": 0.5,  # 30 minutes - impossible
            },
            pattern_types=["spatial"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["pattern"] == "geospatial_anomaly"
        assert result["detected_patterns"][0]["type"] == "spatial"
        assert result["detected_patterns"][0]["severity"] == "high"
        assert "Impossible travel" in result["detected_patterns"][0]["description"]

    @pytest.mark.asyncio
    async def test_no_spatial_pattern_reasonable_travel(self):
        """Test no pattern for reasonable travel speed."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={
                "locations": ["New York", "Boston"],
                "distance_km": 340,
                "time_diff_hours": 5,  # 68 km/h - reasonable
            },
            pattern_types=["spatial"]
        )

        assert result["pattern_count"] == 0

    @pytest.mark.asyncio
    async def test_no_spatial_pattern_insufficient_data(self):
        """Test no pattern when spatial data is insufficient."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_789",
            data={"locations": ["New York"]},  # Only one location
            pattern_types=["spatial"]
        )

        assert result["pattern_count"] == 0


class TestFrequencyPatterns:
    """Frequency pattern detection tests."""

    @pytest.mark.asyncio
    async def test_detect_high_frequency_activity(self):
        """Test detection of high frequency activity."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={"activity_count": 250},  # Well above threshold of 100
            pattern_types=["frequency"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["pattern"] == "high_frequency_activity"
        assert result["detected_patterns"][0]["type"] == "frequency"
        assert result["detected_patterns"][0]["severity"] == "medium"
        assert "250 actions" in result["detected_patterns"][0]["description"]

    @pytest.mark.asyncio
    async def test_no_frequency_pattern_below_threshold(self):
        """Test no pattern below frequency threshold."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={"activity_count": 50},  # Below threshold of 100
            pattern_types=["frequency"]
        )

        assert result["pattern_count"] == 0


class TestAnomalyPatterns:
    """Anomaly pattern detection tests."""

    @pytest.mark.asyncio
    async def test_detect_statistical_outlier(self):
        """Test detection of statistical outlier."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={
                "value": 100,
                "mean": 50,
                "std_dev": 10,  # z-score = 5.0 (> 3.0 threshold)
            },
            pattern_types=["anomaly"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["pattern"] == "statistical_outlier"
        assert result["detected_patterns"][0]["type"] == "anomaly"
        assert result["detected_patterns"][0]["severity"] == "low"
        assert "5.00 standard deviations" in result["detected_patterns"][0]["description"]

    @pytest.mark.asyncio
    async def test_detect_statistical_outlier_negative_deviation(self):
        """Test detection of outlier below mean."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={
                "value": 10,
                "mean": 50,
                "std_dev": 10,  # z-score = 4.0 (> 3.0 threshold)
            },
            pattern_types=["anomaly"]
        )

        assert result["pattern_count"] == 1
        assert result["detected_patterns"][0]["details"]["z_score"] == 4.0

    @pytest.mark.asyncio
    async def test_no_anomaly_pattern_within_threshold(self):
        """Test no pattern when within normal range."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_789",
            data={
                "value": 55,
                "mean": 50,
                "std_dev": 10,  # z-score = 0.5 (< 3.0 threshold)
            },
            pattern_types=["anomaly"]
        )

        assert result["pattern_count"] == 0

    @pytest.mark.asyncio
    async def test_no_anomaly_pattern_zero_std_dev(self):
        """Test no pattern when std_dev is zero."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_000",
            data={
                "value": 100,
                "mean": 50,
                "std_dev": 0,  # Can't calculate z-score
            },
            pattern_types=["anomaly"]
        )

        assert result["pattern_count"] == 0


class TestMultiplePatternTypes:
    """Multiple pattern type detection tests."""

    @pytest.mark.asyncio
    async def test_detect_multiple_patterns_temporal_and_behavioral(self):
        """Test detection of multiple pattern types simultaneously."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={
                "login_hour": 2,  # Unusual time
                "failed_login_attempts": 8,  # Failed logins
            },
            pattern_types=["temporal", "behavioral"]
        )

        assert result["pattern_count"] == 2
        pattern_names = [p["pattern"] for p in result["detected_patterns"]]
        assert "unusual_login_time" in pattern_names
        assert "repeated_failed_logins" in pattern_names

    @pytest.mark.asyncio
    async def test_detect_all_pattern_types(self):
        """Test detection with 'all' pattern types."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={
                "login_hour": 1,  # Temporal
                "failed_login_attempts": 10,  # Behavioral
                "locations": ["NYC", "Tokyo"],
                "distance_km": 10000,
                "time_diff_hours": 1,  # Spatial - impossible travel
                "activity_count": 200,  # Frequency
                "value": 150,
                "mean": 50,
                "std_dev": 20,  # Anomaly - z-score = 5.0
            },
            pattern_types=["all"]
        )

        # Should detect all 5 pattern types
        assert result["pattern_count"] == 5
        assert result["pattern_types_checked"] == ["temporal", "behavioral", "spatial", "frequency", "anomaly"]

    @pytest.mark.asyncio
    async def test_default_pattern_types_is_all(self):
        """Test default pattern types when not specified."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_789",
            data={"login_hour": 3}  # Only temporal data
        )

        # Default should check all types
        assert "temporal" in result["pattern_types_checked"]
        assert "behavioral" in result["pattern_types_checked"]


class TestSeverityAssessment:
    """Severity and assessment tests."""

    @pytest.mark.asyncio
    async def test_severity_counts_high_severity(self):
        """Test severity counts for high severity patterns."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={"failed_login_attempts": 10},  # High severity
            pattern_types=["behavioral"]
        )

        assert result["severity_counts"]["high"] == 1
        assert result["severity_counts"]["medium"] == 0
        assert result["severity_counts"]["low"] == 0

    @pytest.mark.asyncio
    async def test_severity_counts_mixed(self):
        """Test severity counts with mixed severity patterns."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={
                "login_hour": 2,  # Medium severity
                "failed_login_attempts": 7,  # High severity
            },
            pattern_types=["temporal", "behavioral"]
        )

        assert result["severity_counts"]["high"] == 1
        assert result["severity_counts"]["medium"] == 1

    @pytest.mark.asyncio
    async def test_assessment_no_patterns(self):
        """Test assessment message when no patterns detected."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_789",
            data={"login_hour": 14},  # Normal hour
            pattern_types=["temporal"]
        )

        assert result["assessment"] == "No significant patterns detected."

    @pytest.mark.asyncio
    async def test_assessment_with_patterns(self):
        """Test assessment message with patterns detected."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={
                "login_hour": 2,  # Medium
                "failed_login_attempts": 8,  # High
            },
            pattern_types=["temporal", "behavioral"]
        )

        assert "2 pattern(s) detected" in result["assessment"]
        assert "1 high severity" in result["assessment"]
        assert "1 medium severity" in result["assessment"]


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated_after_detection(self):
        """Test statistics are updated after detections."""
        detector = PatternDetectorRefactored()

        await detector.query(
            target="user_123",
            data={"login_hour": 3},
            pattern_types=["temporal"]
        )

        await detector.query(
            target="user_456",
            data={"failed_login_attempts": 10},
            pattern_types=["behavioral"]
        )

        assert detector.total_detections == 2
        assert detector.total_patterns_found == 2

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        detector = PatternDetectorRefactored()

        status = await detector.get_status()

        assert status["tool"] == "PatternDetectorRefactored"
        assert status["total_detections"] == 0
        assert status["total_patterns_found"] == 0
        assert status["pattern_definitions_count"] > 0
        assert "available_pattern_types" in status
        assert len(status["available_pattern_types"]) == 5


class TestObservability:
    """Observability tests."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        detector = PatternDetectorRefactored()

        assert detector.logger is not None
        assert detector.logger.tool_name == "PatternDetectorRefactored"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        detector = PatternDetectorRefactored()

        assert detector.metrics is not None
        assert detector.metrics.tool_name == "PatternDetectorRefactored"


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_detection_with_none_values(self):
        """Test detection handles None values gracefully."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_123",
            data={
                "login_hour": None,  # None value
                "failed_login_attempts": None,
            },
            pattern_types=["temporal", "behavioral"]
        )

        # Should not detect patterns for None values
        assert result["pattern_count"] == 0

    @pytest.mark.asyncio
    async def test_detection_with_empty_data(self):
        """Test detection with empty data dict."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_456",
            data={},  # Empty dict
            pattern_types=["all"]
        )

        assert result["pattern_count"] == 0
        assert result["assessment"] == "No significant patterns detected."

    @pytest.mark.asyncio
    async def test_result_structure_complete(self):
        """Test result dictionary has all expected fields."""
        detector = PatternDetectorRefactored()

        result = await detector.query(
            target="user_789",
            data={"login_hour": 14},
            pattern_types=["temporal"]
        )

        # Verify all expected fields present
        assert "timestamp" in result
        assert "target" in result
        assert "pattern_types_checked" in result
        assert "detected_patterns" in result
        assert "pattern_count" in result
        assert "severity_counts" in result
        assert "assessment" in result
