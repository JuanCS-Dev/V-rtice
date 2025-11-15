# API Client

Centralized API client for Vértice-Maximus platform.
Uses API Gateway (port 8000) as single entry point.

## Architecture

- **Boris Cherny Pattern**: Type-safe error handling with auth interceptor
- **Single Responsibility**: Clean separation of concerns
- **Production-Ready**: Timeout, retry, rate limiting, CORS handling

## Timeouts

All API requests have automatic timeout protection to prevent hanging requests.

### Default Timeout

**30 seconds** - Production-safe default for all requests.

```javascript
import { apiClient, DEFAULT_TIMEOUT } from './api/client';

// Uses default 30s timeout
const data = await apiClient.get('/api/data');
```

### Custom Timeout

Override timeout for specific operations:

```javascript
// Custom timeout for long-running operations
const result = await apiClient.post('/api/malware/analyze', payload, {
  timeout: 120000  // 120s (2 minutes)
});

// Fast timeout for health checks
const health = await apiClient.get('/api/health', {
  timeout: 3000  // 3s
});
```

### Timeout Constants

```javascript
import { DEFAULT_TIMEOUT, HEALTH_CHECK_TIMEOUT } from './api/client';

console.log(DEFAULT_TIMEOUT);       // 30000 (30s)
console.log(HEALTH_CHECK_TIMEOUT);  // 3000 (3s)
```

### Timeout Error Handling

When a timeout occurs, the request is aborted and a clear error is thrown:

```javascript
try {
  const data = await apiClient.get('/slow-endpoint');
} catch (error) {
  if (error.message.includes('timeout')) {
    console.error('Request timed out after 30s');
    // Handle timeout gracefully
  }
}
```

## Usage

### GET Requests

```javascript
// Simple GET
const users = await apiClient.get('/api/users');

// With query parameters
const filtered = await apiClient.get('/api/users?role=admin');

// With custom timeout
const data = await apiClient.get('/api/data', { timeout: 60000 });
```

### POST Requests

```javascript
// POST with data
const result = await apiClient.post('/api/scans', {
  target: '192.168.1.1',
  type: 'vulnerability'
});

// POST with custom timeout
const analysis = await apiClient.post('/api/analyze', payload, {
  timeout: 180000  // 3 minutes
});
```

### PUT/DELETE Requests

```javascript
// Update resource
await apiClient.put('/api/users/123', { name: 'Updated' });

// Delete resource
await apiClient.delete('/api/users/123');
```

## Direct Client

For direct service-to-service communication (bypassing API Gateway):

```javascript
import { directClient } from './api/client';

const result = await directClient.request(
  'http://osint-service:8003',
  '/api/search',
  {
    method: 'POST',
    body: JSON.stringify({ query: 'example.com' }),
    timeout: 60000  // Custom timeout supported
  }
);
```

## Error Handling

### Automatic Auth Errors

- **401 Unauthorized**: Automatic token refresh attempt, redirect to login if fails
- **403 Forbidden**: Clear error, no retry
- **Rate Limit**: Respects rate limits, throws `RateLimitError`

### Custom Errors

```javascript
import { UnauthorizedError, ForbiddenError } from './api/client';

try {
  await apiClient.post('/api/admin/users', data);
} catch (error) {
  if (error instanceof UnauthorizedError) {
    // Handle session expiry
  } else if (error instanceof ForbiddenError) {
    // Handle permission denied
  } else {
    // Handle generic errors
  }
}
```

## Features

- ✅ **Automatic timeout** (30s default, configurable)
- ✅ **CORS preflight caching** (5 min TTL)
- ✅ **CSRF token injection** (automatic)
- ✅ **API key authentication** (automatic)
- ✅ **Rate limiting** (client-side check)
- ✅ **Auth token refresh** (automatic 401 handling)
- ✅ **Type-safe errors** (UnauthorizedError, ForbiddenError, RateLimitError)
- ✅ **WebSocket URL helper** (HTTP → WS conversion)

## WebSocket Support

```javascript
import { getWebSocketUrl } from './api/client';

const wsUrl = getWebSocketUrl('/ws/scans');
// Returns: ws://api-gateway:8000/ws/scans?api_key=...

const socket = new WebSocket(wsUrl);
```

## Configuration

Configured via `config/endpoints.js`:

```javascript
export const ServiceEndpoints = {
  apiGateway: 'http://api-gateway:8000',
  // ...
};

export const AuthConfig = {
  apiKey: 'your-api-key',
  // ...
};
```

## Testing

Comprehensive test suite with 100% coverage target:

```bash
npm test -- src/api/__tests__/client.test.js
```

Tests cover:
- GET/POST/PUT/DELETE requests
- Timeout behavior (default, custom, abort)
- Error handling (401, 403, 404, 500)
- Rate limiting
- CORS preflight
- Direct client
- WebSocket URLs

## Best Practices

### DO

✅ Use `apiClient` for all backend communication
✅ Set custom timeouts for long operations
✅ Handle `UnauthorizedError` and `ForbiddenError`
✅ Use `DEFAULT_TIMEOUT` constant (avoid magic numbers)
✅ Leverage automatic CSRF and API key injection

### DON'T

❌ Use `fetch()` directly (bypasses auth, timeout, rate limiting)
❌ Hardcode timeout values (use constants)
❌ Ignore timeout errors (handle gracefully)
❌ Set timeout < 3s for production endpoints
❌ Set timeout > 180s (indicates architectural issue)

## Governed By

- **Constituição Vértice v2.7**: System governance
- **ADR-001**: Centralized API Gateway pattern
- **ADR-002**: Authentication & authorization strategy
