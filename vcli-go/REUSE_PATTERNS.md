# 🎯 REUSE PATTERNS - Testing & Implementation Gold Standards

**Generated**: 2025-11-13
**Purpose**: Extract reusable patterns to prevent duplication (P6: Eficiência de Token)
**Framework**: CONSTITUIÇÃO VÉRTICE v3.0 - Phase 0.5
**Source**: internal/hitl/client_test.go (838 lines, 90%+ coverage achieved)

---

## 🎯 EXECUTIVE SUMMARY

**Gold Standard**: `internal/hitl/client_test.go`
- **Lines**: 838
- **Coverage**: 90%+ (Target achieved)
- **Tests**: 70+ test cases
- **Pattern**: httptest.NewServer (NO MOCKS!)
- **Quality**: Production-grade testing

**Why It's Gold Standard**:
- ✅ Uses `httptest.NewServer` instead of mocks (P1: Completude)
- ✅ Comprehensive coverage (happy path + errors + edge cases)
- ✅ Clear, readable test structure (TDD-friendly)
- ✅ Tests network errors, invalid JSON, HTTP status codes
- ✅ Integration test included (full workflow)

---

## 📋 PATTERN 1: httptest.NewServer (ANTI-MOCK PATTERN)

**Principle**: P1 - MOCK AQUI É PROIBIDO! Use `httptest.NewServer` to simulate real HTTP

### Basic Pattern

```go
func TestClient_Method_Success(t *testing.T) {
    // SETUP: Create test HTTP server (NOT a mock!)
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // VERIFY: Assert request details
        assert.Equal(t, "POST", r.Method)
        assert.Equal(t, "/endpoint", r.URL.Path)
        assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
        assert.Equal(t, "Bearer token-123", r.Header.Get("Authorization"))

        // RESPOND: Return expected response
        w.WriteHeader(http.StatusOK)
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(ExpectedResponse{
            Status: "success",
            Data:   "result",
        })
    }))
    defer server.Close()

    // ACT: Create client pointing to test server
    client := NewClient(server.URL)
    client.SetToken("token-123")

    result, err := client.Method(request)

    // ASSERT: Verify response
    require.NoError(t, err)
    require.NotNil(t, result)
    assert.Equal(t, "success", result.Status)
    assert.Equal(t, "result", result.Data)
}
```

**Example from hitl/client_test.go** (lines 90-117):
```go
func TestGetStatus_Success(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        assert.Equal(t, "GET", r.Method)
        assert.Equal(t, "/status", r.URL.Path)
        assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(SystemStatus{
            Status:             "healthy",
            PendingDecisions:   5,
            CriticalPending:    2,
        })
    }))
    defer server.Close()

    client := NewClient(server.URL)
    client.SetToken("test-token")

    status, err := client.GetStatus()

    require.NoError(t, err)
    require.NotNil(t, status)
    assert.Equal(t, "healthy", status.Status)
    assert.Equal(t, 5, status.PendingDecisions)
}
```

**Key Points**:
- ✅ `httptest.NewServer` simulates real HTTP (NOT a mock framework)
- ✅ Test actual HTTP request/response cycle
- ✅ Verify headers, method, path, body
- ✅ Respond with JSON-encoded structs
- ✅ Always `defer server.Close()`

---

## 📋 PATTERN 2: Error Cases (4xx, 5xx, Network)

**Principle**: Test ALL error paths for 90%+ coverage

### HTTP Status Error Pattern

```go
func TestClient_Method_ServerError(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusInternalServerError)
        w.Write([]byte("Internal Server Error"))
    }))
    defer server.Close()

    client := NewClient(server.URL)

    result, err := client.Method(request)

    require.Error(t, err)
    assert.Nil(t, result)
    assert.Contains(t, err.Error(), "request failed with status 500")
}
```

**Example from hitl/client_test.go** (lines 119-134):
```go
func TestGetStatus_ServerError(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusInternalServerError)
        w.Write([]byte("Internal error"))
    }))
    defer server.Close()

    client := NewClient(server.URL)
    client.SetToken("test-token")

    status, err := client.GetStatus()

    require.Error(t, err)
    assert.Nil(t, status)
    assert.Contains(t, err.Error(), "request failed with status 500")
}
```

### Network Error Pattern

```go
func TestClient_Method_NetworkError(t *testing.T) {
    // Use invalid URL to trigger network error
    client := NewClient("http://invalid-url-that-does-not-exist.local:99999")

    result, err := client.Method(request)

    require.Error(t, err)
    assert.Nil(t, result)
    assert.Contains(t, err.Error(), "failed to execute request")
}
```

**Example from hitl/client_test.go** (lines 532-541):
```go
func TestGetStatus_NetworkError(t *testing.T) {
    client := NewClient("http://invalid.local:99999")
    client.SetToken("test-token")

    status, err := client.GetStatus()

    require.Error(t, err)
    assert.Nil(t, status)
    assert.Contains(t, err.Error(), "failed to execute request")
}
```

### Invalid JSON Pattern

```go
func TestClient_Method_InvalidJSON(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("not valid json"))
    }))
    defer server.Close()

    client := NewClient(server.URL)

    result, err := client.Method(request)

    require.Error(t, err)
    assert.Nil(t, result)
    assert.Contains(t, err.Error(), "failed to decode response")
}
```

**Example from hitl/client_test.go** (lines 667-682):
```go
func TestGetStatus_InvalidJSON(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("bad json here"))
    }))
    defer server.Close()

    client := NewClient(server.URL)
    client.SetToken("test-token")

    status, err := client.GetStatus()

    require.Error(t, err)
    assert.Nil(t, status)
    assert.Contains(t, err.Error(), "failed to decode response")
}
```

**Coverage Checklist** (for 90%+):
- ✅ Happy path (200 OK + valid JSON)
- ✅ 4xx errors (400, 401, 403, 404)
- ✅ 5xx errors (500, 503)
- ✅ Network errors (connection refused)
- ✅ Invalid JSON responses
- ✅ Invalid URL (malformed)

---

## 📋 PATTERN 3: Table-Driven Tests (Multiple Scenarios)

**Principle**: Test multiple scenarios efficiently

### Table-Driven Pattern

```go
func TestClient_Method_Scenarios(t *testing.T) {
    testCases := []struct {
        name           string
        inputRequest   Request
        serverResponse Response
        expectedStatus string
        expectedError  string
    }{
        {
            name:           "valid request",
            inputRequest:   Request{ID: "123"},
            serverResponse: Response{Status: "success"},
            expectedStatus: "success",
            expectedError:  "",
        },
        {
            name:           "invalid request",
            inputRequest:   Request{ID: ""},
            serverResponse: Response{Status: "error"},
            expectedStatus: "error",
            expectedError:  "invalid ID",
        },
    }

    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
                json.NewEncoder(w).Encode(tc.serverResponse)
            }))
            defer server.Close()

            client := NewClient(server.URL)

            result, err := client.Method(tc.inputRequest)

            if tc.expectedError != "" {
                require.Error(t, err)
                assert.Contains(t, err.Error(), tc.expectedError)
            } else {
                require.NoError(t, err)
                assert.Equal(t, tc.expectedStatus, result.Status)
            }
        })
    }
}
```

**Use Cases**:
- Multiple input variations
- Different response scenarios
- Edge cases (empty strings, nil pointers, zero values)
- Boundary conditions

---

## 📋 PATTERN 4: Integration Test (Full Workflow)

**Principle**: Test complete user workflows end-to-end

### Full Workflow Pattern

```go
func TestFullWorkflow(t *testing.T) {
    // Setup server with multiple endpoints
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        switch r.URL.Path {
        case "/auth/login":
            json.NewEncoder(w).Encode(LoginResponse{AccessToken: "token-123"})

        case "/resource":
            json.NewEncoder(w).Encode(Resource{ID: "resource-1", Status: "active"})

        case "/resource/action":
            json.NewEncoder(w).Encode(ActionResponse{Status: "completed"})

        default:
            w.WriteHeader(http.StatusNotFound)
        }
    }))
    defer server.Close()

    client := NewClient(server.URL)

    // Step 1: Login
    err := client.Login("user", "password")
    require.NoError(t, err)

    // Step 2: Get resource
    resource, err := client.GetResource("resource-1")
    require.NoError(t, err)
    assert.Equal(t, "active", resource.Status)

    // Step 3: Perform action
    response, err := client.PerformAction("resource-1")
    require.NoError(t, err)
    assert.Equal(t, "completed", response.Status)
}
```

**Example from hitl/client_test.go** (lines 788-837):
```go
func TestFullWorkflow(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        switch r.URL.Path {
        case "/auth/login":
            json.NewEncoder(w).Encode(LoginResponse{AccessToken: "token-123"})

        case "/status":
            json.NewEncoder(w).Encode(SystemStatus{Status: "healthy", PendingDecisions: 1})

        case "/decisions/pending":
            json.NewEncoder(w).Encode([]Decision{{AnalysisID: "ANA-001"}})

        case "/decisions/ANA-001":
            json.NewEncoder(w).Encode(Decision{AnalysisID: "ANA-001", Status: "pending"})

        case "/decisions/ANA-001/decide":
            json.NewEncoder(w).Encode(DecisionResponse{Status: "approved"})

        default:
            w.WriteHeader(http.StatusNotFound)
        }
    }))
    defer server.Close()

    client := NewClient(server.URL)

    // 1. Login
    err := client.Login("admin", "password")
    require.NoError(t, err)

    // 2. Check status
    status, err := client.GetStatus()
    require.NoError(t, err)
    assert.Equal(t, "healthy", status.Status)

    // 3. List pending
    decisions, err := client.ListPendingDecisions("")
    require.NoError(t, err)
    require.Len(t, decisions, 1)

    // 4. Get specific decision
    decision, err := client.GetDecision("ANA-001")
    require.NoError(t, err)
    assert.Equal(t, "pending", decision.Status)

    // 5. Make decision
    response, err := client.MakeDecision("ANA-001", DecisionCreate{Status: "approved"})
    require.NoError(t, err)
    assert.Equal(t, "approved", response.Status)
}
```

**Benefits**:
- Tests realistic user workflows
- Verifies multiple endpoints work together
- Tests state changes across requests
- Ensures token/auth persistence works

---

## 📋 PATTERN 5: Real Backend Testing (Anti-Mock Protocol)

**Principle**: P2 - Validação Preventiva (verify backend before testing)

### Real Backend Pattern

```go
// internal/testutil/httptest_helpers.go (TO BE CREATED)
package testutil

import (
    "net/http"
    "testing"
)

// VerifyBackendAvailable checks if backend is running, skips test if not
func VerifyBackendAvailable(t *testing.T, endpoint string) {
    resp, err := http.Get(endpoint + "/health")
    if err != nil {
        t.Skipf("Backend not available at %s - start service first (see BACKEND_MAP.md)", endpoint)
        return
    }
    defer resp.Body.Close()

    if resp.StatusCode != 200 {
        t.Skipf("Backend unhealthy at %s - status: %d", endpoint, resp.StatusCode)
    }
}
```

### Real Backend Test Pattern

```go
func TestClient_RealBackend(t *testing.T) {
    // P2: Validação Preventiva - Verify backend is running
    testutil.VerifyBackendAvailable(t, "http://localhost:8152")

    // Create client pointing to REAL backend
    client := NewClient("http://localhost:8152")

    // Test against real API
    result, err := client.Method(request)

    require.NoError(t, err)
    assert.NotNil(t, result)
}
```

### Awaiting Backend Pattern

```go
func TestClient_AwaitingBackend(t *testing.T) {
    // P1: Completude Obrigatória - Document "awaiting backend"
    t.Skip("Backend not implemented yet - port TBD (see BACKEND_MAP.md)")
}
```

**Decision Tree**:
```
Backend exists? → YES → Use VerifyBackendAvailable + test real backend
                → NO  → Use t.Skip("awaiting backend")
```

---

## 📋 PATTERN 6: Test Structure (TDD Protocol)

**Principle**: DETER-AGENT Camada 2 - TDD Protocol

### TDD Test Structure

```go
func TestClient_Method(t *testing.T) {
    // GIVEN (Arrange): Setup test server and client
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Verify request
        assert.Equal(t, "POST", r.Method)

        // Return response
        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(expectedResponse)
    }))
    defer server.Close()

    client := NewClient(server.URL)

    // WHEN (Act): Execute the method under test
    result, err := client.Method(request)

    // THEN (Assert): Verify expectations
    require.NoError(t, err)
    require.NotNil(t, result)
    assert.Equal(t, "expected", result.Field)
}
```

### TDD Cycle (RED → GREEN → REFACTOR → VERIFY → DOCUMENT)

1. **RED**: Write failing test
   ```go
   func TestNewFeature(t *testing.T) {
       result, err := client.NewFeature(request)
       require.NoError(t, err)
       assert.Equal(t, "expected", result.Status)
   }
   // Run: go test -run TestNewFeature → FAIL (method doesn't exist)
   ```

2. **GREEN**: Implement minimum to pass
   ```go
   func (c *Client) NewFeature(req Request) (*Response, error) {
       return &Response{Status: "expected"}, nil
   }
   // Run: go test -run TestNewFeature → PASS
   ```

3. **REFACTOR**: Clean up code
   ```go
   func (c *Client) NewFeature(req Request) (*Response, error) {
       resp, err := c.httpClient.Post(c.baseURL + "/feature", req)
       if err != nil {
           return nil, err
       }
       // Proper implementation
   }
   ```

4. **VERIFY**: Run full test suite
   ```bash
   go test ./internal/package/... -v -cover
   # Target: 90%+ coverage
   ```

5. **DOCUMENT**: Add doc comments
   ```go
   // NewFeature performs X operation.
   // Returns error if Y condition.
   func (c *Client) NewFeature(req Request) (*Response, error) {
       ...
   }
   ```

---

## 📋 PATTERN 7: Assertions (require vs assert)

**Principle**: Use `require` for critical checks, `assert` for additional

### require vs assert Pattern

```go
func TestClient_Method(t *testing.T) {
    server := httptest.NewServer(...)
    defer server.Close()

    client := NewClient(server.URL)

    result, err := client.Method(request)

    // Use require.NoError: STOP test if error (can't continue)
    require.NoError(t, err)

    // Use require.NotNil: STOP test if nil (would panic on next line)
    require.NotNil(t, result)

    // Use assert.Equal: Continue test even if fails (multiple assertions)
    assert.Equal(t, "expected", result.Status)
    assert.Equal(t, 123, result.Code)
    assert.NotEmpty(t, result.Message)
}
```

**Guidelines**:
- `require`: Critical checks that prevent further assertions (nil, error)
- `assert`: Non-critical checks that can run independently

**Example from hitl/client_test.go** (lines 110-117):
```go
require.NoError(t, err)          // STOP if error
require.NotNil(t, status)        // STOP if nil
assert.Equal(t, "healthy", status.Status)      // Continue if fails
assert.Equal(t, 5, status.PendingDecisions)    // Continue if fails
```

---

## 📋 PATTERN 8: Test Helpers (Shared Utilities)

**Principle**: DRY - Don't Repeat Yourself

### Helper Pattern (TO BE CREATED)

```go
// internal/testutil/httptest_helpers.go
package testutil

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"
)

// JSONServer creates test server that returns JSON
func JSONServer(t *testing.T, statusCode int, response interface{}) *httptest.Server {
    return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(statusCode)
        w.Header().Set("Content-Type", "application/json")
        if err := json.NewEncoder(w).Encode(response); err != nil {
            t.Fatalf("failed to encode response: %v", err)
        }
    }))
}

// ErrorServer creates test server that returns error
func ErrorServer(statusCode int, message string) *httptest.Server {
    return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(statusCode)
        w.Write([]byte(message))
    }))
}

// VerifyRequest creates handler that verifies request details
func VerifyRequest(t *testing.T, expectedMethod, expectedPath string, response interface{}) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        assert.Equal(t, expectedMethod, r.Method)
        assert.Equal(t, expectedPath, r.URL.Path)

        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(response)
    }
}
```

### Usage

```go
func TestClient_Method_Success(t *testing.T) {
    // Use helper instead of repeating code
    server := testutil.JSONServer(t, http.StatusOK, ExpectedResponse{Status: "success"})
    defer server.Close()

    client := NewClient(server.URL)
    result, err := client.Method(request)

    require.NoError(t, err)
    assert.Equal(t, "success", result.Status)
}

func TestClient_Method_Error(t *testing.T) {
    // Use helper for error case
    server := testutil.ErrorServer(http.StatusInternalServerError, "Internal error")
    defer server.Close()

    client := NewClient(server.URL)
    result, err := client.Method(request)

    require.Error(t, err)
    assert.Nil(t, result)
}
```

---

## 📊 COVERAGE TARGETS

### Overall Target: 90%+

**Package Breakdown**:
| Package | Target Coverage | Priority |
|---------|----------------|----------|
| `internal/httpclient` | 95%+ | P0 (Foundation) |
| `internal/maba` | 90%+ | P0 (Confirmed backend) |
| `internal/nis` | 90%+ | P0 (Confirmed backend) |
| `internal/rte` | 90%+ | P0 (Confirmed backend) |
| `internal/hunting` | 90%+ | P1 |
| `internal/immunity` | 90%+ | P1 |
| `internal/neuro` | 90%+ | P1 |
| `internal/intel` | 90%+ | P1 |
| Others (Tier 2-3) | 90%+ | P2-P3 |

### Test Case Distribution (per client)

**Minimum Test Cases**:
1. ✅ Constructor test (`TestNewClient`)
2. ✅ Happy path test (200 OK + valid JSON)
3. ✅ Server error test (500)
4. ✅ Client error test (404 or 400)
5. ✅ Network error test (connection refused)
6. ✅ Invalid JSON test (malformed response)
7. ✅ Invalid URL test (malformed URL)

**Additional for 90%+ Coverage**:
8. ✅ Unauthorized test (401)
9. ✅ Forbidden test (403)
10. ✅ Service unavailable test (503)
11. ✅ Full workflow integration test

---

## 🚀 QUICK REFERENCE

### Test File Template

```go
package packagename

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestNewClient(t *testing.T) {
    client := NewClient("https://test.com")

    assert.NotNil(t, client)
    assert.Equal(t, "https://test.com", client.baseURL)
}

func TestClient_Method_Success(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        assert.Equal(t, "POST", r.Method)
        assert.Equal(t, "/endpoint", r.URL.Path)

        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(Response{Status: "success"})
    }))
    defer server.Close()

    client := NewClient(server.URL)

    result, err := client.Method(request)

    require.NoError(t, err)
    require.NotNil(t, result)
    assert.Equal(t, "success", result.Status)
}

func TestClient_Method_ServerError(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusInternalServerError)
        w.Write([]byte("Internal error"))
    }))
    defer server.Close()

    client := NewClient(server.URL)

    result, err := client.Method(request)

    require.Error(t, err)
    assert.Nil(t, result)
    assert.Contains(t, err.Error(), "request failed with status 500")
}

func TestClient_Method_NetworkError(t *testing.T) {
    client := NewClient("http://invalid.local:99999")

    result, err := client.Method(request)

    require.Error(t, err)
    assert.Nil(t, result)
    assert.Contains(t, err.Error(), "failed to execute request")
}

func TestClient_Method_InvalidJSON(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("not json"))
    }))
    defer server.Close()

    client := NewClient(server.URL)

    result, err := client.Method(request)

    require.Error(t, err)
    assert.Nil(t, result)
    assert.Contains(t, err.Error(), "failed to decode response")
}
```

---

## 📝 CONSTITUTIONAL COMPLIANCE

**P1: Completude Obrigatória**:
- ✅ Use httptest.NewServer (NOT mocks!)
- ✅ Test all error paths (90%+ coverage)
- ✅ Document "awaiting backend" with t.Skip()

**P2: Validação Preventiva**:
- ✅ VerifyBackendAvailable before real backend tests
- ✅ Test request validation (method, path, headers)
- ✅ Test response validation (status, JSON)

**P6: Eficiência de Token**:
- ✅ Reuse patterns from hitl/client_test.go
- ✅ Create shared helpers (testutil package)
- ✅ Don't reinvent - copy proven patterns

---

## 🎯 NEXT STEPS

1. ✅ Study `internal/hitl/client_test.go` (Gold Standard)
2. ⚠️ Create `internal/testutil/httptest_helpers.go` (Phase 1)
3. ⚠️ Apply Pattern 1-8 to `internal/httpclient/*_test.go` (Phase 2)
4. ⚠️ Apply Pattern 1-8 to `internal/maba/clients_test.go` (Phase 3)
5. ⚠️ Repeat for all 26 client packages

---

**Generated**: 2025-11-13
**Framework**: CONSTITUIÇÃO VÉRTICE v3.0 - Phase 0.5
**Source**: internal/hitl/client_test.go (838 lines, 90%+ coverage)
**Purpose**: Enable efficient Phase 2-3 execution with proven patterns
**Constitutional Compliance**: P1 (NO MOCKS ✅), P2 (Validação ✅), P6 (Eficiência ✅)
