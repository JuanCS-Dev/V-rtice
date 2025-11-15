# ISO 8601 Datetime Standardization

## 🎯 Purpose

Standardize all datetime values to ISO 8601 format with UTC timezone, eliminating ambiguity and timezone-related bugs.

**DOUTRINA VÉRTICE - GAP #14 (P2)**
**Following Boris Cherny: "Data should be unambiguous"**

## ✅ Standard Format

All datetime values in the API use **ISO 8601 with UTC timezone**:

```
2025-01-15T10:30:45Z
```

- **Date**: `YYYY-MM-DD`
- **Time**: `HH:MM:SS` (24-hour format)
- **Separator**: `T`
- **Timezone**: `Z` (UTC, equivalent to `+00:00`)
- **Microseconds** (optional): `2025-01-15T10:30:45.123456Z`

## 🚫 What We DON'T Use

```bash
# ❌ Ambiguous formats
"2025-01-15 10:30:45"          # No timezone
"01/15/2025 10:30 AM"          # US format, 12-hour time
"15-01-2025 10:30"             # European format
"1736938245"                   # Unix timestamp

# ❌ Non-UTC timezones
"2025-01-15T10:30:45-05:00"    # US Eastern
"2025-01-15T10:30:45+05:00"    # Pakistan

# ✅ ONLY THIS
"2025-01-15T10:30:45Z"         # ISO 8601 UTC
```

## 🔧 Usage

### Import Base Models

```python
from models.base import (
    utcnow,                    # Get current UTC time
    ensure_utc,                # Convert datetime to UTC
    to_iso8601,                # Convert to ISO 8601 string
    BaseModelWithTimestamps,   # Auto-managed timestamps
    BaseResponse,              # Response with timestamp
    validate_iso8601,          # Parse ISO 8601 string
    is_valid_iso8601,          # Check if valid ISO 8601
)
```

### Example 1: Create Model with Auto-Timestamps

```python
from models.base import BaseModelWithTimestamps

class User(BaseModelWithTimestamps):
    """User model with automatic created_at/updated_at."""
    username: str
    email: str

# Create user
user = User(username="alice", email="alice@example.com")

# Timestamps auto-generated
print(user.created_at)  # datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC)
print(user.updated_at)  # datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC)

# Serialize to JSON
print(user.model_dump_json())
# {
#   "username": "alice",
#   "email": "alice@example.com",
#   "created_at": "2025-01-15T10:30:45Z",
#   "updated_at": "2025-01-15T10:30:45Z"
# }
```

### Example 2: Custom Datetime Field

```python
from models.base import to_iso8601
from pydantic import BaseModel, field_serializer
from datetime import datetime

class Event(BaseModel):
    """Event with custom scheduled_at field."""
    name: str
    scheduled_at: datetime

    @field_serializer('scheduled_at')
    def serialize_scheduled_at(self, dt: datetime) -> str:
        """Serialize to ISO 8601."""
        return to_iso8601(dt)

# Create event
from models.base import utcnow
event = Event(
    name="Security Scan",
    scheduled_at=utcnow()
)

print(event.model_dump_json())
# {
#   "name": "Security Scan",
#   "scheduled_at": "2025-01-15T10:30:45Z"
# }
```

### Example 3: Parse ISO 8601 String

```python
from models.base import validate_iso8601

# Parse various ISO 8601 formats
dt1 = validate_iso8601("2025-01-15T10:30:45Z")
dt2 = validate_iso8601("2025-01-15T10:30:45+00:00")
dt3 = validate_iso8601("2025-01-15T15:30:45+05:00")  # Converts to UTC

print(dt1)  # datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC)
print(dt3)  # datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC) - converted!
```

### Example 4: Validate ISO 8601

```python
from models.base import is_valid_iso8601

# Check if valid
is_valid_iso8601("2025-01-15T10:30:45Z")      # True
is_valid_iso8601("2025-01-15 10:30:45")       # False (no 'T')
is_valid_iso8601("01/15/2025")                # False (wrong format)
is_valid_iso8601("invalid")                   # False
```

### Example 5: Convert Timezone-Aware Datetime

```python
from datetime import datetime, timezone, timedelta
from models.base import ensure_utc, to_iso8601

# Datetime in US Eastern (UTC-5)
eastern_tz = timezone(timedelta(hours=-5))
eastern_dt = datetime(2025, 1, 15, 5, 30, 0, tzinfo=eastern_tz)

# Convert to UTC
utc_dt = ensure_utc(eastern_dt)
print(utc_dt)  # datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)

# Serialize
iso_str = to_iso8601(eastern_dt)
print(iso_str)  # "2025-01-15T10:30:00Z"
```

## 📚 API Examples

### Health Endpoint

**Request:**
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:45Z",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### Scan Result

**Response:**
```json
{
  "scan_id": "scan-123",
  "target": "example.com",
  "status": "completed",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:30:45Z",
  "completed_at": "2025-01-15T10:30:45Z",
  "results": {
    "vulnerabilities_found": 3,
    "scan_duration_seconds": 1845
  }
}
```

### Event Log

**Response:**
```json
{
  "events": [
    {
      "event_type": "scan_started",
      "event_time": "2025-01-15T10:00:00Z",
      "message": "Scan initiated for target: example.com"
    },
    {
      "event_type": "vulnerability_found",
      "event_time": "2025-01-15T10:15:23Z",
      "message": "XSS vulnerability detected"
    },
    {
      "event_type": "scan_completed",
      "event_time": "2025-01-15T10:30:45Z",
      "message": "Scan completed successfully"
    }
  ]
}
```

## 🔍 Frontend Integration

### TypeScript Types (Auto-Generated)

```typescript
// Generated from OpenAPI schema
export interface ScanResult {
  scan_id: string;
  target: string;
  status: string;
  created_at: string;      // ISO 8601 UTC
  updated_at: string;      // ISO 8601 UTC
  completed_at?: string;   // ISO 8601 UTC
}

// Parse datetime string
const scan: ScanResult = await fetchScan('scan-123');

// Convert to JavaScript Date
const createdDate = new Date(scan.created_at);

// Display in user's local timezone
console.log(createdDate.toLocaleString());
// "1/15/2025, 5:30:45 AM" (if user is in US Eastern)
```

### Display Relative Time

```typescript
import { formatDistanceToNow } from 'date-fns';

function ScanCard({ scan }: { scan: ScanResult }) {
  const createdDate = new Date(scan.created_at);

  return (
    <div>
      <h3>Scan #{scan.scan_id}</h3>
      <p>
        Created {formatDistanceToNow(createdDate, { addSuffix: true })}
      </p>
      {/* "Created 2 hours ago" */}
    </div>
  );
}
```

### Sort by Datetime

```typescript
// Sort scans by created_at (newest first)
const sortedScans = scans.sort((a, b) => {
  return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
});
```

## 🎯 Benefits

| Problem | Solution |
|---------|----------|
| **Timezone Ambiguity** | All times in UTC - no confusion |
| **Date Format Confusion** | ISO 8601 - international standard |
| **Parsing Errors** | Consistent format - easy to parse |
| **Sorting Issues** | Lexicographic sort works correctly |
| **DST Bugs** | UTC has no DST transitions |
| **Cross-TZ Collaboration** | Everyone sees same absolute time |

## ⚠️ Common Pitfalls

### 1. Don't Use Naive Datetimes in Python

```python
# ❌ BAD - Naive datetime (no timezone)
from datetime import datetime
now = datetime.now()  # What timezone is this?

# ✅ GOOD - Always use UTC
from models.base import utcnow
now = utcnow()  # Explicitly UTC
```

### 2. Don't Convert to Local Timezone on Backend

```python
# ❌ BAD - Converting to local timezone on server
import pytz
eastern = pytz.timezone('US/Eastern')
local_time = utcnow().astimezone(eastern)  # Don't do this!

# ✅ GOOD - Always return UTC, let client convert
utc_time = utcnow()  # Client will convert to their local time
```

### 3. Don't Use Unix Timestamps in API

```python
# ❌ BAD - Unix timestamp
{
  "created_at": 1736938245  # What timezone? Hard to read!
}

# ✅ GOOD - ISO 8601
{
  "created_at": "2025-01-15T10:30:45Z"  # Clear and standard
}
```

### 4. Don't Forget to Serialize Custom Datetime Fields

```python
# ❌ BAD - Missing serializer
class Event(BaseModel):
    scheduled_at: datetime  # Will serialize with +00:00 instead of Z

# ✅ GOOD - Add serializer
class Event(BaseModel):
    scheduled_at: datetime

    @field_serializer('scheduled_at')
    def serialize_scheduled_at(self, dt: datetime) -> str:
        return to_iso8601(dt)
```

## 🧪 Testing

### Run Tests

```bash
cd backend/api_gateway
pytest tests/test_datetime_iso8601.py -v
```

### Test Coverage

```bash
pytest tests/test_datetime_iso8601.py --cov=models.base --cov-report=html
```

### Example Tests

```python
def test_scan_has_iso8601_timestamps(client):
    """All scan endpoints should return ISO 8601 timestamps."""
    response = client.post("/api/v1/scan/start", json={
        "target": "example.com"
    })

    assert response.status_code == 200
    data = response.json()

    # Check format
    assert data["created_at"].endswith("Z")
    assert "T" in data["created_at"]

    # Should be parseable
    created_dt = datetime.fromisoformat(
        data["created_at"].replace("Z", "+00:00")
    )
    assert created_dt.tzinfo is not None
```

## 📖 References

### ISO 8601 Standard

```
Full format: YYYY-MM-DDTHH:MM:SS.ssssssZ
Examples:
  2025-01-15T10:30:45Z           (seconds)
  2025-01-15T10:30:45.123Z       (milliseconds)
  2025-01-15T10:30:45.123456Z    (microseconds)

Date only:
  2025-01-15

Time only:
  10:30:45Z

With timezone offset:
  2025-01-15T10:30:45+00:00      (UTC)
  2025-01-15T05:30:45-05:00      (US Eastern)
```

### Python datetime Cheatsheet

```python
from datetime import datetime, timezone
from models.base import utcnow, ensure_utc, to_iso8601

# Get current UTC time
now = utcnow()

# Parse ISO 8601 string
dt = datetime.fromisoformat("2025-01-15T10:30:45Z".replace("Z", "+00:00"))

# Convert to UTC
dt_utc = ensure_utc(dt)

# Format to ISO 8601
iso_str = to_iso8601(dt)

# Get Unix timestamp
timestamp = dt.timestamp()
```

### JavaScript/TypeScript Cheatsheet

```typescript
// Parse ISO 8601 string
const date = new Date("2025-01-15T10:30:45Z");

// Format to ISO 8601
const isoString = date.toISOString();  // "2025-01-15T10:30:45.000Z"

// Display in local timezone
const local = date.toLocaleString();  // "1/15/2025, 5:30:45 AM"

// Get Unix timestamp
const timestamp = date.getTime();  // milliseconds
```

## 🔗 Related

- [ISO 8601 Wikipedia](https://en.wikipedia.org/wiki/ISO_8601)
- [RFC 3339](https://tools.ietf.org/html/rfc3339) (Internet timestamp format)
- [Python datetime docs](https://docs.python.org/3/library/datetime.html)
- [Pydantic datetime handling](https://docs.pydantic.dev/latest/concepts/types/#datetime-types)

---

**DOUTRINA VÉRTICE - GAP #14 (P2)**
**Following Boris Cherny: "Data should be unambiguous"**
**Soli Deo Gloria** 🙏
