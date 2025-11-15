# Sentry Error Tracking & Monitoring

## 🎯 Purpose

Production error tracking, performance monitoring, and session replay with Sentry.

**DOUTRINA VÉRTICE - GAP #8 (P2)**
**Following Boris Cherny: "Errors should be observable"**

## ✅ What Sentry Provides

- **Error Tracking**: Capture and track exceptions in production
- **Performance Monitoring**: Measure API response times, database queries
- **Session Replay**: See user actions leading to errors
- **Release Tracking**: Track errors across deployments
- **Alerting**: Get notified of new errors via email/Slack/PagerDuty
- **User Context**: See which users encountered errors
- **Breadcrumbs**: Trail of events before error occurred

## 📦 Setup

### 1. Create Sentry Account

1. Go to [sentry.io](https://sentry.io)
2. Sign up (free tier available)
3. Create new project:
   - Backend: Python (FastAPI)
   - Frontend: React
4. Copy DSN (Data Source Name)

### 2. Backend Setup (FastAPI)

#### Install Dependencies

```bash
cd backend/api_gateway
pip install sentry-sdk[fastapi]
```

Add to `requirements.txt`:
```
sentry-sdk[fastapi]==1.40.0
```

#### Configure Environment

```bash
# .env
SENTRY_DSN=https://YOUR_KEY@o123456.ingest.sentry.io/123456
ENVIRONMENT=production
RELEASE_VERSION=1.0.0  # Or git commit hash
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% of transactions
SENTRY_SEND_PII=false  # Don't send emails/IPs
```

#### Initialize in main.py

```python
from middleware.sentry_integration import init_sentry, SentryContextMiddleware

# Initialize Sentry (at startup)
init_sentry()

# Add middleware
app.add_middleware(SentryContextMiddleware)
```

#### Use in Endpoints

```python
from middleware.sentry_integration import (
    set_user_context,
    add_breadcrumb,
    capture_exception,
    start_span,
)

@app.post("/api/v1/scan/start")
async def start_scan(scan_data: ScanRequest, user = Depends(get_current_user)):
    # Set user context
    set_user_context(user.id, user.email)

    # Add breadcrumb
    add_breadcrumb("Starting scan", "scan", "info", {
        "target": scan_data.target
    })

    try:
        # Measure performance
        with start_span("scanner.nmap", "Run Nmap scan"):
            result = await run_nmap_scan(scan_data.target)

        return result

    except Exception as e:
        # Capture with context
        capture_exception(e, level="error", extras={
            "target": scan_data.target,
            "user_id": user.id,
        })
        raise
```

### 3. Frontend Setup (React + Vite)

#### Install Dependencies

```bash
cd frontend
npm install @sentry/react @sentry/tracing
```

#### Configure Environment

```bash
# .env
VITE_SENTRY_DSN=https://YOUR_KEY@o123456.ingest.sentry.io/789012
VITE_ENVIRONMENT=production
VITE_RELEASE_VERSION=1.0.0
VITE_SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% of transactions
VITE_SENTRY_REPLAYS_SESSION=0.1     # 10% of sessions
VITE_SENTRY_REPLAYS_ERROR=1.0       # 100% when error occurs
```

#### Initialize in main.tsx

```typescript
import { initSentry } from './lib/sentry';

// Initialize Sentry
initSentry();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

#### Wrap App with Error Boundary

```typescript
import { SentryErrorBoundary, ErrorFallback } from './lib/sentry';

function App() {
  return (
    <SentryErrorBoundary fallback={<ErrorFallback />}>
      <YourApp />
    </SentryErrorBoundary>
  );
}
```

#### Use in Components

```typescript
import { setUserContext, captureException, addBreadcrumb } from './lib/sentry';

// After login
function handleLogin(user) {
  setUserContext({
    id: user.id,
    email: user.email,
    username: user.username,
  });
}

// In components
async function startScan(target: string) {
  try {
    addBreadcrumb('Starting scan', 'scan', 'info', { target });

    const result = await fetch('/api/v1/scan/start', {
      method: 'POST',
      body: JSON.stringify({ target }),
    });

    return result;
  } catch (error) {
    captureException(error as Error, 'error', {
      action: 'start_scan',
      target,
    });

    throw error;
  }
}
```

## 📚 Usage Examples

### Example 1: Capture Handled Exception

```python
# Backend
try:
    result = external_api_call()
except ExternalAPIError as e:
    # Log to Sentry but don't fail
    capture_exception(e, level="warning", extras={
        "api": "external_service",
        "endpoint": "/api/data"
    })

    # Return fallback
    return fallback_data
```

```typescript
// Frontend
try {
  const data = await fetchData();
  return data;
} catch (error) {
  captureException(error as Error, 'warning', {
    component: 'DataFetcher',
    url: '/api/data',
  });

  // Show error to user
  toast.error('Failed to load data');
}
```

### Example 2: Add Breadcrumbs

```python
# Backend
@app.post("/api/v1/scan/start")
async def start_scan(scan_data: ScanRequest):
    add_breadcrumb("Validating scan request", "validation", "info")

    # Validate
    if not scan_data.target:
        add_breadcrumb("Validation failed", "validation", "error")
        raise HTTPException(400, "Target required")

    add_breadcrumb("Starting Nmap scan", "scan", "info", {
        "target": scan_data.target
    })

    result = await run_nmap(scan_data.target)

    add_breadcrumb("Scan completed", "scan", "info", {
        "duration_seconds": result.duration
    })

    return result
```

### Example 3: Performance Monitoring

```python
# Backend
@app.get("/api/v1/scans")
async def list_scans():
    with start_span("db.query", "Fetch scans from database"):
        scans = db.query(Scan).all()

    with start_span("serialize", "Serialize scans to JSON"):
        result = [scan.dict() for scan in scans]

    return result
```

```typescript
// Frontend
import { measurePerformance } from './lib/sentry';

async function loadDashboard() {
  const scans = await measurePerformance('fetchScans', async () => {
    return await fetch('/api/v1/scans').then(r => r.json());
  });

  const vulnerabilities = await measurePerformance('fetchVulnerabilities', async () => {
    return await fetch('/api/v1/vulnerabilities').then(r => r.json());
  });

  return { scans, vulnerabilities };
}
```

### Example 4: User Context

```python
# Backend - Set after authentication
@app.post("/api/v1/auth/login")
async def login(credentials: LoginRequest):
    user = authenticate(credentials)

    # Set user context for all subsequent errors
    set_user_context(
        user_id=user.id,
        email=user.email,
        username=user.username
    )

    return {"token": create_token(user)}
```

```typescript
// Frontend - Set after login
async function handleLogin(email: string, password: string) {
  const response = await loginUser(email, password);

  // Set user context
  setUserContext({
    id: response.user.id,
    email: response.user.email,
    username: response.user.username,
  });

  // All errors from now on will include user info
}

// Frontend - Clear on logout
function handleLogout() {
  clearUserContext();
  // Redirect to login
}
```

### Example 5: Custom Context

```python
# Backend
@app.post("/api/v1/scan/start")
async def start_scan(scan_data: ScanRequest):
    # Add custom context
    sentry_sdk.set_context("scan_details", {
        "target": scan_data.target,
        "scan_type": scan_data.scan_type,
        "ports": scan_data.ports,
        "estimated_duration": calculate_duration(scan_data),
    })

    # If error occurs, context will be included
    result = await run_scan(scan_data)
    return result
```

## 🎯 Best Practices

### 1. Set Sampling Rates

```python
# Production: Sample 10% of transactions (reduce costs)
SENTRY_TRACES_SAMPLE_RATE=0.1

# Development: Sample 100% (catch all errors)
SENTRY_TRACES_SAMPLE_RATE=1.0
```

### 2. Don't Send PII

```python
# ❌ BAD - Sends emails, IPs to Sentry
SENTRY_SEND_PII=true

# ✅ GOOD - Filters PII
SENTRY_SEND_PII=false

# Use user IDs instead of emails
set_user_context(user_id="user-123")  # OK
set_user_context(email="user@example.com")  # Not OK (unless SEND_PII=true)
```

### 3. Filter Noisy Errors

```python
# Backend - In before_send_filter()
def before_send_filter(event, hint):
    # Ignore health check errors
    if event.get("transaction") == "/api/v1/health":
        return None

    # Ignore 404s
    if "404" in str(event.get("exception")):
        return None

    return event
```

```typescript
// Frontend - In ignoreErrors
ignoreErrors: [
  'ResizeObserver loop',  // Browser noise
  'NetworkError',         // Offline users
  'AbortError',           // User canceled
]
```

### 4. Use Releases

```bash
# Backend
export RELEASE_VERSION=$(git rev-parse --short HEAD)

# Frontend
export VITE_RELEASE_VERSION=$(git rev-parse --short HEAD)
```

Benefits:
- Track which version introduced error
- Compare error rates between releases
- Automatic source map upload

### 5. Add Breadcrumbs Liberally

```python
# More breadcrumbs = easier debugging
add_breadcrumb("User clicked button", "ui", "info")
add_breadcrumb("API request started", "http", "info")
add_breadcrumb("Database query executed", "db", "info")
add_breadcrumb("Cache miss", "cache", "debug")
add_breadcrumb("Validation failed", "validation", "warning")
```

## 🔔 Alerting

### Email Alerts

1. Go to **Settings** → **Alerts**
2. Create alert rule:
   - **When**: Error occurs
   - **If**: First seen OR frequency > 10/hour
   - **Then**: Send email to team@example.com

### Slack Integration

1. Go to **Settings** → **Integrations** → **Slack**
2. Authorize Slack workspace
3. Configure alert rule to post to #errors channel

### PagerDuty (Critical Errors)

1. Go to **Settings** → **Integrations** → **PagerDuty**
2. Add integration key
3. Create alert for critical errors only

## 📊 Dashboard

Sentry dashboard shows:
- **Error count** (last 24h, 7d, 30d)
- **Users affected** (unique users with errors)
- **Error frequency** (spikes indicate new bugs)
- **Release comparison** (which version is stable?)
- **Performance metrics** (slow endpoints)

Key metrics to monitor:
- **Unhandled errors** (should be 0 in production)
- **New issues** (introduced by recent deploy)
- **Regression** (errors coming back after fix)
- **P95 response time** (performance degradation)

## 🧪 Testing

### Test Sentry Integration

```python
# Backend - Trigger test error
@app.get("/debug/sentry-test")
async def test_sentry():
    """Trigger test error to verify Sentry integration."""
    raise Exception("This is a test error from Sentry integration")
```

```typescript
// Frontend - Trigger test error
function testSentry() {
  throw new Error('This is a test error from Sentry integration');
}
```

### Verify in Sentry

1. Trigger test error
2. Go to Sentry dashboard
3. Should see new error within ~10 seconds
4. Check:
   - Error message
   - Stack trace
   - User context (if set)
   - Breadcrumbs
   - Request data

## 💰 Cost Optimization

### Free Tier Limits

- **Errors**: 5,000/month
- **Performance**: 10,000 transactions/month
- **Replays**: 50/month

### Reduce Costs

1. **Lower sampling rates**
   ```python
   SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% instead of 100%
   ```

2. **Filter noisy endpoints**
   ```python
   # Don't track health checks
   if transaction == "/health":
       return None
   ```

3. **Limit session replays**
   ```typescript
   replaysSessionSampleRate: 0.05,  // 5% of sessions
   replaysOnErrorSampleRate: 0.5,   // 50% when errors (not 100%)
   ```

4. **Use environments**
   - **Production**: Track everything
   - **Staging**: Lower sampling
   - **Development**: Disable or use local Sentry

## 🔗 Related

- [Sentry Python Docs](https://docs.sentry.io/platforms/python/)
- [Sentry React Docs](https://docs.sentry.io/platforms/javascript/guides/react/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [Best Practices](https://docs.sentry.io/product/best-practices/)

---

**DOUTRINA VÉRTICE - GAP #8 (P2)**
**Following Boris Cherny: "Errors should be observable"**
**Soli Deo Gloria** 🙏
