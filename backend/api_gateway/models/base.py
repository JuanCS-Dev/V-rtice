"""
Base Models with ISO 8601 Datetime Standardization

DOUTRINA VÉRTICE - GAP #14 (P2)
All datetime fields use ISO 8601 format with UTC timezone

Following Boris Cherny's principle: "Data should be unambiguous"
"""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field, field_serializer
from pydantic.functional_validators import field_validator


# ============================================================================
# DATETIME UTILITIES
# ============================================================================

def utcnow() -> datetime:
    """
    Get current UTC datetime with timezone info.

    Returns:
        datetime with UTC timezone (aware datetime)

    Example:
        >>> dt = utcnow()
        >>> dt.isoformat()
        '2025-01-15T10:30:00+00:00'
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is in UTC timezone.

    Converts naive datetimes to UTC and localizes aware datetimes to UTC.

    Args:
        dt: Datetime to convert

    Returns:
        Datetime in UTC timezone

    Examples:
        >>> # Naive datetime → UTC
        >>> dt = datetime(2025, 1, 15, 10, 30)
        >>> ensure_utc(dt).isoformat()
        '2025-01-15T10:30:00+00:00'

        >>> # Aware datetime in different TZ → convert to UTC
        >>> import pytz
        >>> dt = datetime(2025, 1, 15, 10, 30, tzinfo=pytz.timezone('US/Eastern'))
        >>> ensure_utc(dt).isoformat()
        '2025-01-15T15:30:00+00:00'  # Converted to UTC
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Aware datetime - convert to UTC
        return dt.astimezone(timezone.utc)


def to_iso8601(dt: datetime) -> str:
    """
    Convert datetime to ISO 8601 string with 'Z' suffix (UTC).

    Args:
        dt: Datetime to convert

    Returns:
        ISO 8601 string with 'Z' suffix

    Examples:
        >>> dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        >>> to_iso8601(dt)
        '2025-01-15T10:30:45Z'

        >>> # With microseconds
        >>> dt = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)
        >>> to_iso8601(dt)
        '2025-01-15T10:30:45.123456Z'
    """
    dt_utc = ensure_utc(dt)
    # Use 'Z' suffix instead of '+00:00' for UTC
    iso_str = dt_utc.isoformat()
    # Replace '+00:00' with 'Z'
    if iso_str.endswith('+00:00'):
        return iso_str[:-6] + 'Z'
    return iso_str


# ============================================================================
# BASE MODELS
# ============================================================================

class BaseModelWithTimestamps(BaseModel):
    """
    Base model with automatic timestamp management.

    Provides created_at and updated_at fields that:
    - Default to current UTC time
    - Always serialize to ISO 8601 with 'Z' suffix
    - Automatically convert to UTC if provided in different timezone

    Example:
        >>> class User(BaseModelWithTimestamps):
        ...     username: str
        ...
        >>> user = User(username="alice")
        >>> user.created_at
        datetime.datetime(2025, 1, 15, 10, 30, 45, tzinfo=datetime.timezone.utc)
        >>> user.model_dump_json()
        '{"username":"alice","created_at":"2025-01-15T10:30:45Z",...}'
    """

    created_at: datetime = Field(
        default_factory=utcnow,
        description="Creation timestamp (ISO 8601 UTC)"
    )

    updated_at: datetime = Field(
        default_factory=utcnow,
        description="Last update timestamp (ISO 8601 UTC)"
    )

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def ensure_datetime_utc(cls, value: Any) -> datetime:
        """Ensure datetime fields are in UTC."""
        if isinstance(value, datetime):
            return ensure_utc(value)
        elif isinstance(value, str):
            # Parse ISO 8601 string
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return ensure_utc(dt)
        return value

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO 8601 with 'Z' suffix."""
        return to_iso8601(dt)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: to_iso8601
        }


class BaseResponse(BaseModel):
    """
    Base response model with timestamp.

    Example:
        >>> class HealthResponse(BaseResponse):
        ...     status: str
        ...
        >>> response = HealthResponse(status="healthy")
        >>> response.timestamp
        '2025-01-15T10:30:45Z'
    """

    timestamp: str = Field(
        default_factory=lambda: to_iso8601(utcnow()),
        description="Response timestamp (ISO 8601 UTC)",
        examples=["2025-01-15T10:30:45Z"]
    )


# ============================================================================
# DATETIME FIELD TYPES
# ============================================================================

class DatetimeField(BaseModel):
    """
    Standalone datetime field that always serializes to ISO 8601.

    Use this for datetime fields that need guaranteed ISO 8601 serialization.

    Example:
        >>> class Event(BaseModel):
        ...     name: str
        ...     scheduled_at: datetime
        ...
        ...     @field_serializer('scheduled_at')
        ...     def serialize_scheduled_at(self, dt: datetime) -> str:
        ...         return to_iso8601(dt)
    """

    value: datetime

    @field_validator('value', mode='before')
    @classmethod
    def ensure_utc(cls, value: Any) -> datetime:
        """Ensure value is UTC datetime."""
        if isinstance(value, datetime):
            return ensure_utc(value)
        elif isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return ensure_utc(dt)
        return value

    @field_serializer('value')
    def serialize(self, dt: datetime) -> str:
        """Serialize to ISO 8601."""
        return to_iso8601(dt)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_iso8601(value: str) -> datetime:
    """
    Validate and parse ISO 8601 datetime string.

    Args:
        value: ISO 8601 string (with or without 'Z' suffix)

    Returns:
        Parsed datetime in UTC

    Raises:
        ValueError: If string is not valid ISO 8601

    Examples:
        >>> validate_iso8601("2025-01-15T10:30:45Z")
        datetime.datetime(2025, 1, 15, 10, 30, 45, tzinfo=datetime.timezone.utc)

        >>> validate_iso8601("2025-01-15T10:30:45+00:00")
        datetime.datetime(2025, 1, 15, 10, 30, 45, tzinfo=datetime.timezone.utc)

        >>> validate_iso8601("invalid")
        Traceback (most recent call last):
        ...
        ValueError: Invalid ISO 8601 datetime: invalid
    """
    try:
        # Replace 'Z' with '+00:00' for fromisoformat
        normalized = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(normalized)
        return ensure_utc(dt)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid ISO 8601 datetime: {value}") from e


def is_valid_iso8601(value: str) -> bool:
    """
    Check if string is valid ISO 8601 datetime.

    Args:
        value: String to validate

    Returns:
        True if valid ISO 8601, False otherwise

    Examples:
        >>> is_valid_iso8601("2025-01-15T10:30:45Z")
        True

        >>> is_valid_iso8601("2025-01-15")
        True

        >>> is_valid_iso8601("invalid")
        False
    """
    try:
        validate_iso8601(value)
        return True
    except ValueError:
        return False


# ============================================================================
# EXAMPLE MODELS
# ============================================================================

class ScanRecord(BaseModelWithTimestamps):
    """
    Example: Scan record with automatic timestamps.

    Demonstrates:
    - Automatic created_at/updated_at
    - ISO 8601 serialization
    - UTC timezone enforcement

    Example:
        >>> scan = ScanRecord(
        ...     scan_id="scan-123",
        ...     target="example.com",
        ...     status="completed"
        ... )
        >>> scan.model_dump_json()
        '{
            "scan_id": "scan-123",
            "target": "example.com",
            "status": "completed",
            "created_at": "2025-01-15T10:30:45Z",
            "updated_at": "2025-01-15T10:30:45Z"
        }'
    """

    scan_id: str
    target: str
    status: str


class EventLog(BaseModelWithTimestamps):
    """
    Example: Event log with custom event_time.

    Demonstrates:
    - Custom datetime field
    - Inheriting created_at/updated_at
    - Multiple datetime fields

    Example:
        >>> event = EventLog(
        ...     event_type="scan_started",
        ...     event_time=utcnow(),
        ...     message="Scan initiated"
        ... )
        >>> event.model_dump_json()
        '{
            "event_type": "scan_started",
            "event_time": "2025-01-15T10:30:45Z",
            "message": "Scan initiated",
            "created_at": "2025-01-15T10:30:45Z",
            "updated_at": "2025-01-15T10:30:45Z"
        }'
    """

    event_type: str
    event_time: datetime
    message: str

    @field_serializer('event_time')
    def serialize_event_time(self, dt: datetime) -> str:
        """Serialize event_time to ISO 8601."""
        return to_iso8601(dt)
