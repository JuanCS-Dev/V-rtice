# User-Based Rate Limiting

## 🎯 Purpose

Rate limiting by **user ID** (not just IP address), ensuring each authenticated user has their own request quota.

**DOUTRINA VÉRTICE - GAP #13 (P2)**
**Following Boris Cherny: "Security should scale with identity"**

## ✅ Features

- **Per-User Limits**: Each authenticated user gets their own rate limit bucket
- **IP Fallback**: Anonymous users rate limited by IP address
- **No Bypass**: Authenticated users can't bypass limits by switching IPs
- **Token-Based**: Extracts user ID from JWT token automatically
- **Redis-Backed**: Distributed rate limiting across multiple API instances
- **Endpoint-Specific**: Different limits for different endpoints

## 🔄 How It Works

### Before (IP-Based)

```
User A from IP 192.168.1.1 → Rate limit: 100 req/min (shared with User B)
User B from IP 192.168.1.1 → Rate limit: 100 req/min (shared with User A)

Problem: Users behind same NAT/proxy share limits ❌
```

### After (User-Based)

```
User A (authenticated) → Rate limit: 100 req/min (separate)
User B (authenticated) → Rate limit: 100 req/min (separate)
Anonymous from IP 192.168.1.1 → Rate limit: 100 req/min

Benefit: Each user has independent limits ✅
```

## 📦 Setup

### 1. Install Dependencies

```bash
pip install slowapi redis
```

### 2. Set Environment Variables

```bash
# JWT secret (for decoding tokens)
export JWT_SECRET="your-secret-key"

# Redis URL (for distributed rate limiting)
export REDIS_URL="redis://localhost:6379"
```

### 3. Apply Middleware to App

```python
from fastapi import FastAPI
from middleware.rate_limiting import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI()

# Register limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## 🚀 Usage

### Global Default Limit

All endpoints automatically get default limit (100 req/min per user):

```python
# No decorator needed - default applies automatically
@app.get("/api/v1/data")
async def get_data():
    return {"data": "..."}

# Authenticated users: 100 req/min per user
# Anonymous users: 100 req/min per IP
```

### Endpoint-Specific Limits

Apply custom limits to specific endpoints:

```python
from middleware.rate_limiting import user_rate_limit

# Scan endpoint: 10 scans per minute per user
@app.post("/api/v1/scan/start")
@user_rate_limit("10/minute")
async def start_scan():
    return {"scan_id": "..."}

# Login endpoint: 5 attempts per minute per IP
@app.post("/api/v1/auth/login")
@user_rate_limit("5/minute")
async def login():
    return {"token": "..."}

# High-volume endpoint: 200 req/min per user
@app.get("/api/v1/metrics")
@user_rate_limit("200/minute")
async def get_metrics():
    return {"metrics": "..."}
```

### Pre-Configured Limits

Use predefined limits from `rate_limiting.py`:

```python
from middleware.rate_limiting import (
    SCAN_START_LIMIT,   # "10/minute"
    AUTH_LOGIN_LIMIT,   # "5/minute"
    MUTATION_LIMIT,     # "30/minute"
    READ_LIMIT,         # "100/minute"
    ADMIN_LIMIT,        # "200/minute"
)

@app.post("/api/v1/scan/start")
@user_rate_limit(SCAN_START_LIMIT)
async def start_scan():
    ...

@app.post("/api/v1/auth/login")
@user_rate_limit(AUTH_LOGIN_LIMIT)
async def login():
    ...
```

## 📚 Examples

### Example 1: Different Users, Same IP

```python
# Scenario: Two users behind corporate NAT

# User A (authenticated)
headers_a = {"Authorization": "Bearer <USER_A_TOKEN>"}
for i in range(15):
    requests.post("/api/v1/scan/start", headers=headers_a)

# Result: User A gets 10 requests (limit reached), 5 rejected ❌

# User B (authenticated, same IP as User A!)
headers_b = {"Authorization": "Bearer <USER_B_TOKEN>"}
for i in range(10):
    requests.post("/api/v1/scan/start", headers=headers_b)

# Result: User B gets 10 requests (separate limit) ✅

# With IP-based limiting, User A would have consumed
# the shared quota, blocking User B ❌
```

### Example 2: User Cannot Bypass by Switching IPs

```python
# User tries to bypass limit by switching networks

# From office WiFi (IP: 192.168.1.100)
headers = {"Authorization": "Bearer <USER_TOKEN>"}
for i in range(10):
    requests.post("/api/v1/scan/start", headers=headers)
# Result: 10 requests accepted, limit reached

# Switches to mobile hotspot (IP: 10.0.0.50)
for i in range(5):
    requests.post("/api/v1/scan/start", headers=headers)
# Result: 5 requests rejected ❌

# User-based limiting prevents IP hopping bypass ✅
```

### Example 3: Anonymous Users Share IP Limits

```python
# Multiple anonymous users from same IP share quota

# Anonymous User 1 (no token)
for i in range(60):
    requests.get("/api/v1/data")  # 100 req/min limit
# Result: 60 requests accepted

# Anonymous User 2 (same IP, no token)
for i in range(50):
    requests.get("/api/v1/data")
# Result: 40 accepted, 10 rejected (shared quota) ❌

# This is expected behavior for anonymous users
```

## 🎯 Rate Limit Headers

Every response includes rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1699564800

{
  "data": "..."
}
```

When limit exceeded:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699564800
Retry-After: 45

{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Try again in 45 seconds."
}
```

## 🔧 Configuration

### Endpoint-Specific Limits

Edit `middleware/rate_limiting.py`:

```python
# Scan endpoints (resource-intensive)
SCAN_START_LIMIT = "10/minute"  # Adjust this

# Authentication endpoints
AUTH_LOGIN_LIMIT = "5/minute"   # Adjust this

# Data modification endpoints
MUTATION_LIMIT = "30/minute"    # Adjust this
```

### Global Default

Change default limit for all endpoints:

```python
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["200/minute"],  # Increase from 100
)
```

### Time Windows

Supported time windows:

```python
@user_rate_limit("5/second")   # 5 per second
@user_rate_limit("100/minute") # 100 per minute
@user_rate_limit("1000/hour")  # 1000 per hour
@user_rate_limit("10000/day")  # 10000 per day
```

## 🔍 Monitoring & Debugging

### Check User's Current Limit

```python
from middleware.rate_limiting import get_rate_limit_key

@app.get("/debug/rate-limit")
async def debug_rate_limit(request: Request):
    """Check rate limit key for debugging."""
    key = get_rate_limit_key(request)
    is_auth = is_user_authenticated(request)

    return {
        "rate_limit_key": key,
        "authenticated": is_auth,
        "type": "user-based" if is_auth else "ip-based"
    }
```

### Log Rate Limit Hits

```python
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Log rate limit violations."""
    key = get_rate_limit_key(request)
    log.warning(
        "Rate limit exceeded",
        identifier=key,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded"},
        headers={"Retry-After": str(exc.detail)},
    )
```

### Check Redis Keys

```bash
# Connect to Redis
redis-cli

# List all rate limit keys
KEYS ratelimit:*

# Check specific user's remaining quota
GET ratelimit:user:USER_ID:/api/v1/scan/start
```

## 🚨 Common Issues

### Issue: User Always Treated as Anonymous

**Cause**: JWT_SECRET not set or incorrect

**Fix**:
```bash
export JWT_SECRET="same-secret-used-for-token-generation"
```

### Issue: Rate Limit Not Applied

**Cause**: Limiter not registered with app

**Fix**:
```python
app.state.limiter = limiter  # Don't forget this!
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Issue: Redis Connection Failed

**Cause**: Redis not running or wrong URL

**Fix**:
```bash
# Start Redis
redis-server

# Or use correct URL
export REDIS_URL="redis://your-redis-host:6379"
```

## 📊 Benefits

| Scenario | Before (IP-Based) | After (User-Based) |
|----------|-------------------|-------------------|
| **Corp NAT** | All employees share limit ❌ | Each employee has own limit ✅ |
| **Public WiFi** | All customers share limit ❌ | Each customer has own limit ✅ |
| **VPN** | All VPN users share limit ❌ | Each user has own limit ✅ |
| **IP Hopping** | User can bypass ❌ | User cannot bypass ✅ |
| **DDoS** | IP blocking required | User-level blocking available |

## 🎯 Security Considerations

### ✅ Prevents

- **IP Hopping**: Users can't bypass limits by switching IPs
- **Shared NAT Abuse**: Users behind same NAT get separate quotas
- **Token Reuse**: Same token = same user = same quota (correct)

### ⚠️ Limitations

- **Stolen Tokens**: Attacker with valid token can consume user's quota
- **Anonymous Abuse**: Multiple anonymous users can share IP quota

### 🔒 Mitigation

For sensitive endpoints, combine with additional security:

```python
from fastapi import Depends
from middleware.auth import verify_token

@app.post("/api/v1/sensitive-operation")
@user_rate_limit("3/minute")  # Low limit
async def sensitive_op(user = Depends(verify_token)):  # Require auth
    # Additionally log + monitor for abuse
    log.info("Sensitive op", user_id=user["sub"])
    ...
```

## 🧪 Testing

Run tests:

```bash
cd backend/api_gateway
pytest tests/test_rate_limiting.py -v
```

Test coverage:

```bash
pytest tests/test_rate_limiting.py --cov=middleware.rate_limiting --cov-report=html
```

## 📖 API Reference

### `get_user_identifier(request: Request) -> str`

Get unique identifier for rate limiting.

**Returns**: `"user:{USER_ID}"` or `"ip:{IP_ADDRESS}"`

### `user_rate_limit(limit: str)`

Decorator for endpoint-specific rate limiting.

**Parameters**:
- `limit`: Rate limit string (e.g., "10/minute")

**Example**:
```python
@user_rate_limit("5/minute")
async def my_endpoint():
    ...
```

### `is_user_authenticated(request: Request) -> bool`

Check if request is from authenticated user.

**Returns**: `True` if authenticated, `False` if anonymous

### `get_rate_limit_key(request: Request) -> str`

Get rate limit key for debugging.

**Returns**: The actual key used for rate limiting

## 🔗 Related

- [slowapi Documentation](https://github.com/laurents/slowapi)
- [Redis Documentation](https://redis.io/docs/)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
- [RFC 6585 - HTTP 429](https://tools.ietf.org/html/rfc6585)

---

**DOUTRINA VÉRTICE - GAP #13 (P2)**
**Following Boris Cherny: "Security should scale with identity"**
**Soli Deo Gloria** 🙏
