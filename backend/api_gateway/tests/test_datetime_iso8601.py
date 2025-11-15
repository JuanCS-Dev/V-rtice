"""
Tests for ISO 8601 Datetime Standardization

DOUTRINA VÉRTICE - GAP #14 (P2)
Tests for datetime models and utilities

Following Boris Cherny: "Tests or it didn't happen"
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, field_serializer

from models.base import (
    utcnow,
    ensure_utc,
    to_iso8601,
    BaseModelWithTimestamps,
    BaseResponse,
    validate_iso8601,
    is_valid_iso8601,
    ScanRecord,
    EventLog,
)


# ============================================================================
# TESTS: utcnow()
# ============================================================================

def test_utcnow_returns_aware_datetime():
    """utcnow() should return timezone-aware datetime."""
    dt = utcnow()

    assert dt.tzinfo is not None
    assert dt.tzinfo == timezone.utc


def test_utcnow_is_recent():
    """utcnow() should return current time."""
    before = datetime.now(timezone.utc)
    dt = utcnow()
    after = datetime.now(timezone.utc)

    assert before <= dt <= after


# ============================================================================
# TESTS: ensure_utc()
# ============================================================================

def test_ensure_utc_with_naive_datetime():
    """Naive datetime should be treated as UTC."""
    naive_dt = datetime(2025, 1, 15, 10, 30, 45)

    result = ensure_utc(naive_dt)

    assert result.tzinfo == timezone.utc
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15
    assert result.hour == 10
    assert result.minute == 30


def test_ensure_utc_with_utc_datetime():
    """UTC datetime should remain unchanged."""
    utc_dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=timezone.utc)

    result = ensure_utc(utc_dt)

    assert result == utc_dt
    assert result.tzinfo == timezone.utc


def test_ensure_utc_with_offset_datetime():
    """Datetime with offset should be converted to UTC."""
    # +05:00 offset (e.g., Pakistan time)
    offset_tz = timezone(timedelta(hours=5))
    offset_dt = datetime(2025, 1, 15, 15, 30, 45, tzinfo=offset_tz)

    result = ensure_utc(offset_dt)

    assert result.tzinfo == timezone.utc
    # 15:30 +05:00 = 10:30 UTC
    assert result.hour == 10
    assert result.minute == 30


def test_ensure_utc_with_negative_offset():
    """Datetime with negative offset should be converted to UTC."""
    # -05:00 offset (e.g., US Eastern time)
    offset_tz = timezone(timedelta(hours=-5))
    offset_dt = datetime(2025, 1, 15, 5, 30, 45, tzinfo=offset_tz)

    result = ensure_utc(offset_dt)

    assert result.tzinfo == timezone.utc
    # 05:30 -05:00 = 10:30 UTC
    assert result.hour == 10
    assert result.minute == 30


# ============================================================================
# TESTS: to_iso8601()
# ============================================================================

def test_to_iso8601_with_utc_datetime():
    """UTC datetime should serialize with 'Z' suffix."""
    dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=timezone.utc)

    result = to_iso8601(dt)

    assert result == "2025-01-15T10:30:45Z"


def test_to_iso8601_with_microseconds():
    """Datetime with microseconds should be preserved."""
    dt = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)

    result = to_iso8601(dt)

    assert result == "2025-01-15T10:30:45.123456Z"


def test_to_iso8601_with_naive_datetime():
    """Naive datetime should be converted to UTC with 'Z'."""
    dt = datetime(2025, 1, 15, 10, 30, 45)

    result = to_iso8601(dt)

    assert result == "2025-01-15T10:30:45Z"


def test_to_iso8601_with_offset_datetime():
    """Offset datetime should be converted to UTC."""
    offset_tz = timezone(timedelta(hours=5))
    dt = datetime(2025, 1, 15, 15, 30, 45, tzinfo=offset_tz)

    result = to_iso8601(dt)

    # 15:30 +05:00 = 10:30 UTC
    assert result == "2025-01-15T10:30:45Z"


# ============================================================================
# TESTS: BaseModelWithTimestamps
# ============================================================================

def test_base_model_auto_timestamps():
    """BaseModelWithTimestamps should auto-generate timestamps."""
    model = BaseModelWithTimestamps()

    assert isinstance(model.created_at, datetime)
    assert isinstance(model.updated_at, datetime)
    assert model.created_at.tzinfo == timezone.utc
    assert model.updated_at.tzinfo == timezone.utc


def test_base_model_timestamps_serialization():
    """Timestamps should serialize to ISO 8601 with 'Z'."""
    model = BaseModelWithTimestamps()

    json_str = model.model_dump_json()
    data = json.loads(json_str)

    assert data["created_at"].endswith("Z")
    assert data["updated_at"].endswith("Z")
    assert "T" in data["created_at"]  # ISO 8601 format


def test_base_model_custom_timestamps():
    """Should accept custom timestamps."""
    custom_dt = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    model = BaseModelWithTimestamps(created_at=custom_dt, updated_at=custom_dt)

    assert model.created_at == custom_dt
    assert model.updated_at == custom_dt


def test_base_model_naive_datetime_converted():
    """Naive datetime should be converted to UTC."""
    naive_dt = datetime(2025, 1, 15, 10, 30)

    model = BaseModelWithTimestamps(created_at=naive_dt)

    assert model.created_at.tzinfo == timezone.utc


def test_base_model_parses_iso8601_string():
    """Should parse ISO 8601 string input."""
    model = BaseModelWithTimestamps(
        created_at="2025-01-15T10:30:45Z",
        updated_at="2025-01-15T10:30:45+00:00"
    )

    assert model.created_at.year == 2025
    assert model.created_at.month == 1
    assert model.created_at.day == 15
    assert model.updated_at.tzinfo == timezone.utc


# ============================================================================
# TESTS: BaseResponse
# ============================================================================

def test_base_response_has_timestamp():
    """BaseResponse should have ISO 8601 timestamp."""
    response = BaseResponse()

    assert isinstance(response.timestamp, str)
    assert response.timestamp.endswith("Z")
    assert "T" in response.timestamp


def test_base_response_timestamp_format():
    """Timestamp should be valid ISO 8601."""
    response = BaseResponse()

    # Should be parseable
    dt = datetime.fromisoformat(response.timestamp.replace("Z", "+00:00"))
    assert dt.tzinfo is not None


# ============================================================================
# TESTS: validate_iso8601()
# ============================================================================

def test_validate_iso8601_with_z_suffix():
    """Should parse ISO 8601 with 'Z' suffix."""
    result = validate_iso8601("2025-01-15T10:30:45Z")

    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15
    assert result.hour == 10
    assert result.minute == 30
    assert result.tzinfo == timezone.utc


def test_validate_iso8601_with_offset():
    """Should parse ISO 8601 with timezone offset."""
    result = validate_iso8601("2025-01-15T10:30:45+00:00")

    assert result.tzinfo == timezone.utc


def test_validate_iso8601_with_different_offset():
    """Should parse and convert different timezone offsets."""
    result = validate_iso8601("2025-01-15T15:30:45+05:00")

    # Should be converted to UTC
    assert result.tzinfo == timezone.utc
    assert result.hour == 10  # 15:30 +05:00 = 10:30 UTC


def test_validate_iso8601_with_microseconds():
    """Should parse datetime with microseconds."""
    result = validate_iso8601("2025-01-15T10:30:45.123456Z")

    assert result.microsecond == 123456


def test_validate_iso8601_with_invalid_string():
    """Should raise ValueError for invalid ISO 8601."""
    with pytest.raises(ValueError, match="Invalid ISO 8601 datetime"):
        validate_iso8601("not-a-date")


def test_validate_iso8601_with_date_only():
    """Should parse date-only ISO 8601."""
    result = validate_iso8601("2025-01-15")

    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


# ============================================================================
# TESTS: is_valid_iso8601()
# ============================================================================

def test_is_valid_iso8601_with_valid_strings():
    """Should return True for valid ISO 8601 strings."""
    assert is_valid_iso8601("2025-01-15T10:30:45Z") is True
    assert is_valid_iso8601("2025-01-15T10:30:45+00:00") is True
    assert is_valid_iso8601("2025-01-15T10:30:45.123Z") is True
    assert is_valid_iso8601("2025-01-15") is True


def test_is_valid_iso8601_with_invalid_strings():
    """Should return False for invalid strings."""
    assert is_valid_iso8601("not-a-date") is False
    assert is_valid_iso8601("2025-13-01") is False  # Invalid month
    assert is_valid_iso8601("") is False


# ============================================================================
# TESTS: ScanRecord (Example Model)
# ============================================================================

def test_scan_record_serialization():
    """ScanRecord should serialize with ISO 8601 timestamps."""
    scan = ScanRecord(
        scan_id="scan-123",
        target="example.com",
        status="completed"
    )

    json_str = scan.model_dump_json()
    data = json.loads(json_str)

    assert data["scan_id"] == "scan-123"
    assert data["target"] == "example.com"
    assert data["status"] == "completed"
    assert data["created_at"].endswith("Z")
    assert data["updated_at"].endswith("Z")


def test_scan_record_deserialization():
    """ScanRecord should deserialize ISO 8601 timestamps."""
    scan = ScanRecord(
        scan_id="scan-123",
        target="example.com",
        status="completed",
        created_at="2025-01-15T10:30:45Z",
        updated_at="2025-01-15T10:30:45Z"
    )

    assert scan.created_at.year == 2025
    assert scan.created_at.tzinfo == timezone.utc


# ============================================================================
# TESTS: EventLog (Example Model with Custom Datetime)
# ============================================================================

def test_event_log_custom_datetime():
    """EventLog should serialize custom datetime field."""
    event_time = datetime(2025, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
    event = EventLog(
        event_type="scan_started",
        event_time=event_time,
        message="Scan initiated"
    )

    json_str = event.model_dump_json()
    data = json.loads(json_str)

    assert data["event_type"] == "scan_started"
    assert data["event_time"] == "2025-01-15T10:30:45Z"
    assert data["message"] == "Scan initiated"
    assert data["created_at"].endswith("Z")


def test_event_log_multiple_datetimes():
    """EventLog should handle multiple datetime fields correctly."""
    event = EventLog(
        event_type="scan_completed",
        event_time=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        message="Scan completed",
        created_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
    )

    json_str = event.model_dump_json()
    data = json.loads(json_str)

    # All datetimes should be ISO 8601 with 'Z'
    assert data["event_time"].endswith("Z")
    assert data["created_at"].endswith("Z")
    assert data["updated_at"].endswith("Z")


# ============================================================================
# TESTS: Roundtrip (Serialize → Deserialize)
# ============================================================================

def test_roundtrip_serialization():
    """Should successfully roundtrip through JSON."""
    original = ScanRecord(
        scan_id="scan-456",
        target="test.com",
        status="running"
    )

    # Serialize
    json_str = original.model_dump_json()

    # Deserialize
    data = json.loads(json_str)
    restored = ScanRecord(**data)

    assert restored.scan_id == original.scan_id
    assert restored.target == original.target
    assert restored.status == original.status
    assert restored.created_at.replace(microsecond=0) == original.created_at.replace(microsecond=0)


# ============================================================================
# TESTS: Edge Cases
# ============================================================================

def test_year_2038_problem_safe():
    """Should handle dates beyond 2038 (no 32-bit timestamp issues)."""
    future_dt = datetime(2050, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    result = to_iso8601(future_dt)

    assert result == "2050-12-31T23:59:59Z"


def test_leap_year_handling():
    """Should correctly handle leap year dates."""
    leap_dt = datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)

    result = to_iso8601(leap_dt)

    assert result == "2024-02-29T12:00:00Z"


def test_midnight_handling():
    """Should correctly handle midnight (00:00:00)."""
    midnight = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

    result = to_iso8601(midnight)

    assert result == "2025-01-15T00:00:00Z"
