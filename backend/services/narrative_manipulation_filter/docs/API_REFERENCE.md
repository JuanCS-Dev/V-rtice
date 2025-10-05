# API Reference - Cognitive Defense System v2.0.0

## Base URL

```
Production: https://api.cognitive-defense.vertice.dev/api/v2
Development: http://localhost:8013/api/v2
```

## Authentication

All API endpoints (except `/health`) require authentication via JWT token or API key.

```http
Authorization: Bearer <jwt_token>
```

or

```http
X-API-Key: <api_key>
```

---

## Endpoints

### 1. Content Analysis

#### `POST /analyze`

Analyze content for narrative manipulation.

**Request Body:**

```json
{
  "content": "string (required, max 10000 chars)",
  "source_info": {
    "domain": "string (optional)",
    "url": "string (optional)",
    "author": "string (optional)",
    "timestamp": "ISO 8601 datetime (optional)"
  },
  "mode": "FAST_TRACK | STANDARD | DEEP_ANALYSIS (default: STANDARD)"
}
```

**Response (200 OK):**

```json
{
  "analysis_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "mode": "STANDARD",
  "processing_time_ms": 450,

  "manipulation_score": 0.75,
  "threat_level": "HIGH",
  "confidence": 0.92,

  "modules": {
    "source_credibility": {
      "score": 0.35,
      "reputation": "LOW",
      "domain_age_days": 45,
      "ssl_valid": false,
      "newsguard_rating": null
    },
    "emotional_manipulation": {
      "score": 0.82,
      "primary_emotion": "fear",
      "intensity": 0.85,
      "detected_techniques": ["fear_mongering", "urgency"]
    },
    "logical_fallacies": {
      "count": 3,
      "fallacies": [
        {
          "type": "ad_hominem",
          "confidence": 0.88,
          "location": "paragraph 2"
        },
        {
          "type": "false_dichotomy",
          "confidence": 0.75,
          "location": "paragraph 4"
        }
      ]
    },
    "reality_distortion": {
      "distortion_score": 0.90,
      "verified_claims": 2,
      "unverified_claims": 5,
      "false_claims": 1,
      "claims": [
        {
          "text": "Government will distribute R$ 10,000",
          "status": "FALSE",
          "confidence": 0.95,
          "sources": ["ClaimBuster", "Google Fact Check"]
        }
      ]
    }
  },

  "summary": "High manipulation detected. Content uses fear-based appeals, contains logical fallacies, and makes unverified claims.",
  "recommendations": [
    "Verify claims with trusted sources",
    "Check source credibility",
    "Be aware of emotional manipulation"
  ]
}
```

**Error Responses:**

- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid auth
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Processing failed

---

### 2. Claim Verification

#### `POST /verify-claim`

Verify a specific claim against fact-checkers.

**Request Body:**

```json
{
  "claim": "string (required, max 500 chars)"
}
```

**Response (200 OK):**

```json
{
  "claim": "Government will distribute R$ 10,000",
  "status": "FALSE",
  "confidence": 0.95,
  "sources": [
    {
      "name": "ClaimBuster",
      "verdict": "FALSE",
      "url": "https://idir.uta.edu/claimbuster/claim/12345",
      "date": "2024-01-10"
    },
    {
      "name": "Google Fact Check",
      "verdict": "FALSE",
      "url": "https://factcheck.example.com/claim/67890",
      "date": "2024-01-12"
    }
  ],
  "explanation": "This claim has been fact-checked by multiple sources and found to be false."
}
```

---

### 3. Analysis History

#### `GET /history`

Retrieve historical analysis results.

**Query Parameters:**

- `limit` (integer, default: 20, max: 100)
- `offset` (integer, default: 0)
- `source_domain` (string, optional) - Filter by source domain
- `threat_level` (string, optional) - Filter by threat level
- `start_date` (ISO 8601, optional)
- `end_date` (ISO 8601, optional)

**Response (200 OK):**

```json
{
  "total": 1250,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "analysis_id": "uuid",
      "timestamp": "2024-01-15T10:30:00Z",
      "manipulation_score": 0.75,
      "threat_level": "HIGH",
      "source_domain": "fake-news-site.net",
      "summary": "..."
    }
  ]
}
```

---

### 4. Get Analysis by ID

#### `GET /analysis/{analysis_id}`

Retrieve a specific analysis result.

**Path Parameters:**

- `analysis_id` (uuid, required)

**Response (200 OK):**

Same format as `/analyze` endpoint response.

**Error Responses:**

- `404 Not Found` - Analysis ID not found

---

### 5. Batch Analysis

#### `POST /analyze/batch`

Analyze multiple content items in a single request.

**Request Body:**

```json
{
  "items": [
    {
      "id": "item1",
      "content": "...",
      "source_info": {...}
    },
    {
      "id": "item2",
      "content": "...",
      "source_info": {...}
    }
  ],
  "mode": "STANDARD"
}
```

**Response (200 OK):**

```json
{
  "batch_id": "uuid",
  "total_items": 2,
  "results": [
    {
      "id": "item1",
      "analysis": {...}
    },
    {
      "id": "item2",
      "analysis": {...}
    }
  ]
}
```

---

### 6. System Health

#### `GET /health`

Check system health (no auth required).

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 86400,
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "kafka": "healthy",
    "external_apis": "healthy"
  }
}
```

---

### 7. Readiness Check

#### `GET /ready`

Check if service is ready to accept traffic (no auth required).

**Response (200 OK):**

```json
{
  "ready": true
}
```

**Response (503 Service Unavailable):**

```json
{
  "ready": false,
  "reason": "Loading models..."
}
```

---

### 8. Prometheus Metrics

#### `GET /metrics`

Prometheus-compatible metrics endpoint.

**Response (200 OK):**

```
# HELP cognitive_defense_requests_total Total number of analysis requests
# TYPE cognitive_defense_requests_total counter
cognitive_defense_requests_total{module="source_credibility",status="success"} 12500

# HELP cognitive_defense_request_duration_seconds Request duration in seconds
# TYPE cognitive_defense_request_duration_seconds histogram
cognitive_defense_request_duration_seconds_bucket{module="reality_distortion",le="0.5"} 9500
...
```

---

## Rate Limiting

API rate limits (per IP address):

- **Standard**: 100 requests/minute
- **Burst**: 20 requests/second
- **Daily**: 10,000 requests/day

Rate limit headers returned with each response:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641392400
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service down |

---

## Processing Modes

| Mode | Latency | Components | Use Case |
|------|---------|------------|----------|
| FAST_TRACK | <500ms | Tier 1 APIs only | Real-time filtering |
| STANDARD | <2s | Tier 1 + Tier 2 (async) | Default analysis |
| DEEP_ANALYSIS | <5s | Full KG verification | Investigative analysis |

---

## SDK Examples

### Python

```python
import requests

# Configuration
API_URL = "https://api.cognitive-defense.vertice.dev/api/v2"
API_KEY = "your_api_key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Analyze content
response = requests.post(
    f"{API_URL}/analyze",
    headers=headers,
    json={
        "content": "Your content here...",
        "source_info": {
            "domain": "example.com"
        },
        "mode": "STANDARD"
    }
)

result = response.json()
print(f"Manipulation Score: {result['manipulation_score']}")
print(f"Threat Level: {result['threat_level']}")
```

### JavaScript

```javascript
const axios = require('axios');

const API_URL = 'https://api.cognitive-defense.vertice.dev/api/v2';
const API_KEY = 'your_api_key';

async function analyzeContent(content, sourceInfo) {
  const response = await axios.post(
    `${API_URL}/analyze`,
    {
      content,
      source_info: sourceInfo,
      mode: 'STANDARD'
    },
    {
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      }
    }
  );

  return response.data;
}

// Usage
const result = await analyzeContent(
  'Your content here...',
  { domain: 'example.com' }
);

console.log(`Manipulation Score: ${result.manipulation_score}`);
console.log(`Threat Level: ${result.threat_level}`);
```

### cURL

```bash
curl -X POST "https://api.cognitive-defense.vertice.dev/api/v2/analyze" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your content here...",
    "source_info": {
      "domain": "example.com"
    },
    "mode": "STANDARD"
  }'
```

---

## Webhooks (Coming Soon)

Subscribe to analysis events via webhooks:

```json
{
  "url": "https://your-server.com/webhook",
  "events": ["analysis.completed", "high_threat.detected"],
  "secret": "your_webhook_secret"
}
```

---

**Last Updated**: 2024-01-15
**API Version**: v2.0.0
**Support**: api-support@vertice.dev
