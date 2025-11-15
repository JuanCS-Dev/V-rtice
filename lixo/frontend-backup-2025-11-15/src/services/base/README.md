# BaseService

Foundation class for all service layer classes in Vértice-Maximus.
Provides common functionality for API communication, retry logic, error handling, and data transformation.

## Architecture

```
┌─────────────────┐
│   Component     │  ← UI logic only
└────────┬────────┘
         │ uses
┌────────▼────────┐
│  Custom Hook    │  ← React Query integration
└────────┬────────┘
         │ calls
┌────────▼────────┐
│  Service Class  │  ← Business logic (THIS LAYER)
└────────┬────────┘
         │ uses
┌────────▼────────┐
│   API Client    │  ← HTTP, auth, retry
└─────────────────┘
```

## Retry Behavior

**Boris Cherny Pattern**: Idempotent operations auto-retry, non-idempotent require explicit opt-in.

### GET Requests (Idempotent) ✅ Auto-Retry

GET requests **automatically retry** up to 3 times with exponential backoff:

- **Max retries**: 3 (default)
- **Delays**: 1s → 2s → 4s (exponential backoff)
- **Total time**: ~7s maximum

```javascript
import { OffensiveService } from './services/offensive/OffensiveService';

const service = new OffensiveService();

// Automatic retry (3 attempts)
const data = await service.get('/scans');

// Disable retry
const data = await service.get('/scans', { retry: 0 });

// Custom retry count
const data = await service.get('/scans', { retry: 5, retryDelay: 500 });
```

### POST/PUT/DELETE (Non-Idempotent) ❌ No Auto-Retry

POST, PUT, and DELETE do **NOT retry by default** to prevent duplicate operations.

Enable retry explicitly when safe:

```javascript
// Default: NO retry
const result = await service.post('/create', data);

// Enable retry explicitly (use with caution!)
const result = await service.post('/create', data, {
  retry: true,       // Enable retry
  maxRetries: 2,     // Conservative: 2 attempts
  retryDelay: 1000   // 1s base delay
});
```

**⚠️ Warning**: Only enable retry for POST/PUT/DELETE if your backend implements idempotency keys or the operation is truly idempotent.

## Retry Exceptions

The retry mechanism **skips retry** for these errors:

- ❌ **401 Unauthorized** - Auth token expired
- ❌ **403 Forbidden** - Insufficient permissions
- ❌ **400 Bad Request** - Client error (retry won't help)

These errors are thrown immediately without retry.

✅ **Retries on**:
- Network errors (timeout, connection refused)
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout

## Usage

### Creating a Service

```javascript
import { BaseService } from './services/base/BaseService';

class MyService extends BaseService {
  constructor() {
    super('/api/myservice');
  }

  // Optional: override transformResponse
  transformResponse(response) {
    return {
      ...response,
      transformedAt: new Date().toISOString()
    };
  }

  // Optional: override validateRequest
  validateRequest(data) {
    super.validateRequest(data); // Call base validation

    if (!data.requiredField) {
      throw new Error('requiredField is required');
    }
  }

  // Custom methods
  async getById(id) {
    return this.get(`/${id}`);
  }

  async create(data) {
    return this.post('/', data);
  }
}
```

### GET Requests

```javascript
const service = new MyService();

// Simple GET
const all = await service.get('/list');

// GET with path
const one = await service.get('/123');

// GET with custom options
const data = await service.get('/data', {
  retry: 5,           // 5 retry attempts
  retryDelay: 2000,   // 2s base delay
  timeout: 60000      // 60s timeout (passed to API client)
});
```

### POST Requests

```javascript
// POST without retry (default, safe)
const result = await service.post('/create', {
  name: 'New Item',
  value: 123
});

// POST with retry (use carefully)
const result = await service.post('/create', data, {
  retry: true,
  maxRetries: 2
});
```

### PUT Requests

```javascript
// Update resource
await service.put('/items/123', {
  name: 'Updated Name'
});

// With retry (if idempotent)
await service.put('/items/123', data, {
  retry: true
});
```

### DELETE Requests

```javascript
// Delete resource
await service.delete('/items/123');

// With retry (if idempotent)
await service.delete('/items/123', {
  retry: true
});
```

## Error Handling

BaseService enhances all errors with context:

```javascript
try {
  await service.get('/failing-endpoint');
} catch (error) {
  console.error(error.message);       // Original error message
  console.error(error.method);        // "GET"
  console.error(error.endpoint);      // "/api/myservice/failing-endpoint"
  console.error(error.service);       // "MyService"
  console.error(error.originalError); // Original Error object
}
```

### Error Message Extraction

BaseService intelligently extracts error messages from various formats:

```javascript
extractErrorMessage('string error')              // → 'string error'
extractErrorMessage({ message: 'msg' })          // → 'msg'
extractErrorMessage({ detail: 'detail' })        // → 'detail'
extractErrorMessage({ error: 'err' })            // → 'err'
extractErrorMessage({})                          // → 'Unknown error occurred'
```

## Validation

BaseService includes automatic request validation:

### Size Validation

```javascript
// Maximum payload size: 5MB
const largeData = { file: 'x'.repeat(6 * 1024 * 1024) };

await service.post('/upload', largeData);
// ❌ Throws: "Request payload too large: 6.00MB (max: 5MB)"
```

### Null/Undefined Protection

```javascript
await service.post('/create', null);
// ❌ Throws: "Request data cannot be null or undefined"

await service.post('/create', undefined);
// ❌ Throws: "Request data cannot be null or undefined"
```

### Custom Validation

Override `validateRequest()` in subclasses:

```javascript
class MyService extends BaseService {
  validateRequest(data) {
    // Call base validation first
    super.validateRequest(data);

    // Custom validation
    if (data.email && !data.email.includes('@')) {
      throw new Error('Invalid email format');
    }

    if (data.age && data.age < 0) {
      throw new Error('Age cannot be negative');
    }
  }
}
```

## Response Transformation

Override `transformResponse()` to normalize API responses:

```javascript
class UserService extends BaseService {
  transformResponse(response) {
    // API returns: { user_id, user_name }
    // Transform to: { id, name }
    return {
      id: response.user_id,
      name: response.user_name,
      fullName: response.user_name.toUpperCase()
    };
  }
}
```

## Advanced Features

### Manual Retry

Use the protected `retry()` method for custom retry logic:

```javascript
class MyService extends BaseService {
  async complexOperation() {
    return this.retry(async () => {
      // Your complex logic here
      const step1 = await this.externalApiCall();
      const step2 = await this.processData(step1);
      return step2;
    }, 5, 2000); // 5 retries, 2s base delay
  }
}
```

### Health Check

```javascript
const isHealthy = await service.healthCheck();

if (!isHealthy) {
  console.error('Service is down!');
}
```

### Endpoint Building

```javascript
service.buildEndpoint('');          // → '/api/myservice'
service.buildEndpoint('/users');    // → '/api/myservice/users'
service.buildEndpoint('users');     // → '/api/myservice/users' (auto-adds /)
```

## Best Practices

### DO ✅

- Use GET for read operations (automatic retry)
- Validate input in `validateRequest()`
- Transform responses in `transformResponse()`
- Log errors with context (BaseService does this automatically)
- Use `retry: true` for POST only if backend supports idempotency
- Override `validateRequest()` for domain-specific validation

### DON'T ❌

- Enable retry for POST/PUT/DELETE without idempotency protection
- Bypass validation (always call `super.validateRequest()`)
- Catch and swallow errors (let BaseService handle)
- Make direct API calls (use service methods)
- Hardcode retry values (use options)
- Create services without extending BaseService

## Logging

BaseService automatically logs:

- **Debug**: Every request (method + endpoint)
- **Info**: Success after retry
- **Warn**: Retry attempts, auth errors detected
- **Error**: Final failure after all retries

Example log output:

```
[DEBUG] [OffensiveService] GET /api/offensive/scans
[WARN] [OffensiveService] Attempt 1/3 failed. Retrying in 1000ms... { error: "Network timeout" }
[WARN] [OffensiveService] Attempt 2/3 failed. Retrying in 2000ms... { error: "Connection refused" }
[INFO] [OffensiveService] Success after 2 retry attempt(s)
```

## Testing

Comprehensive test suite included:

```bash
npm test -- src/services/base/__tests__/BaseService.test.js
```

Tests cover:
- GET automatic retry (8 tests)
- POST opt-in retry (5 tests)
- PUT/DELETE opt-in retry (4 tests)
- Retry method internals (3 tests)
- Error handling (2 tests)
- Validation (4 tests)
- Integration scenarios (3 tests)

**Total**: 29 tests, 100% coverage

## Governed By

- **Constituição Vértice v2.7**: System governance
- **ADR-002**: Service Layer Pattern
- **ADR-004**: Testing Strategy

---

**Questions?** Check existing services for examples:
- `frontend/src/services/offensive/OffensiveService.js`
- `frontend/src/services/defensive/DefensiveService.js`
- `frontend/src/services/osint/OsintService.js`
