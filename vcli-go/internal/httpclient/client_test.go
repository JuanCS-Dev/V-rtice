package httpclient

import (
	"context"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/errors"
)

// TestDefaultClientConfig verifies default configuration values
func TestDefaultClientConfig(t *testing.T) {
	config := DefaultClientConfig("http://localhost:8080")

	assert.Equal(t, "http://localhost:8080", config.BaseURL)
	assert.Equal(t, 30*time.Second, config.Timeout)
	assert.Equal(t, 3, config.RetryConfig.MaxAttempts)
	assert.Equal(t, 5, config.BreakerConfig.MaxFailures)
	assert.NotNil(t, config.Headers)
}

// TestNewClient verifies client creation with config
func TestNewClient(t *testing.T) {
	config := ClientConfig{
		BaseURL: "http://localhost:8080",
		Timeout: 10 * time.Second,
		Headers: map[string]string{
			"X-Custom": "test",
		},
		RetryConfig:   DefaultRetryConfig(),
		BreakerConfig: DefaultBreakerConfig(),
	}

	client := NewClient(config)

	assert.NotNil(t, client)
	assert.Equal(t, "http://localhost:8080", client.BaseURL)
	assert.NotNil(t, client.HTTPClient)
	assert.Equal(t, 10*time.Second, client.HTTPClient.Timeout)
	assert.NotNil(t, client.Retrier)
	assert.NotNil(t, client.Breaker)
	assert.Equal(t, "test", client.Headers["X-Custom"])
	assert.Equal(t, "application/json", client.Headers["Content-Type"])
}

// TestNewClient_DefaultHeaders verifies default headers are set
func TestNewClient_DefaultHeaders(t *testing.T) {
	config := ClientConfig{
		BaseURL: "http://localhost:8080",
	}

	client := NewClient(config)

	assert.Equal(t, "application/json", client.Headers["Content-Type"])
	assert.Equal(t, "application/json", client.Headers["Accept"])
}

// TestGet_Success verifies successful GET request
func TestGet_Success(t *testing.T) {
	// GIVEN: Server returns JSON response
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "GET", r.Method)
		assert.Equal(t, "/test", r.URL.Path)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
	}))
	defer server.Close()

	// WHEN: Client makes GET request
	config := DefaultClientConfig(server.URL)
	client := NewClient(config)
	ctx := context.Background()
	body, err := client.Get(ctx, "/test")

	// THEN: Response is returned successfully
	require.NoError(t, err)
	assert.Contains(t, string(body), "ok")
}

// TestGet_404NotFound verifies 404 error handling
func TestGet_404NotFound(t *testing.T) {
	// GIVEN: Server returns 404
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		w.Write([]byte("not found"))
	}))
	defer server.Close()

	// WHEN: Client makes GET request
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	_, err := client.Get(ctx, "/missing")

	// THEN: Error is returned (non-retryable)
	require.Error(t, err)
	assert.False(t, errors.IsRetryable(err))
}

// TestGet_500ServerError verifies 500 triggers retry
func TestGet_500ServerError(t *testing.T) {
	// GIVEN: Server always returns 500
	attempts := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("server error"))
	}))
	defer server.Close()

	// WHEN: Client makes GET request
	config := ClientConfig{
		BaseURL: server.URL,
		RetryConfig: RetryConfig{
			MaxAttempts:  3,
			InitialDelay: 10 * time.Millisecond,
			MaxDelay:     100 * time.Millisecond,
			Multiplier:   2.0,
		},
		BreakerConfig: DefaultBreakerConfig(),
	}
	client := NewClient(config)
	ctx := context.Background()
	_, err := client.Get(ctx, "/error")

	// THEN: Request is retried (3 attempts)
	require.Error(t, err)
	assert.Equal(t, 3, attempts, "Should retry 3 times for 500 error")
}

// TestGet_ContextCancelled verifies context cancellation
func TestGet_ContextCancelled(t *testing.T) {
	// GIVEN: Server with slow response
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(200 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// WHEN: Context is cancelled before response
	client := NewClient(DefaultClientConfig(server.URL))
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	_, err := client.Get(ctx, "/slow")

	// THEN: Error indicates context timeout
	require.Error(t, err)
	assert.Contains(t, err.Error(), "TIMEOUT")
}

// TestPost_Success verifies successful POST request
func TestPost_Success(t *testing.T) {
	// GIVEN: Server accepts POST with body
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "POST", r.Method)
		assert.Equal(t, "/submit", r.URL.Path)

		var payload map[string]string
		json.NewDecoder(r.Body).Decode(&payload)
		assert.Equal(t, "value", payload["key"])

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(map[string]string{"result": "created"})
	}))
	defer server.Close()

	// WHEN: Client makes POST request
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	requestBody := []byte(`{"key":"value"}`)
	body, err := client.Post(ctx, "/submit", requestBody)

	// THEN: Response is returned successfully
	require.NoError(t, err)
	assert.Contains(t, string(body), "created")
}

// TestPostJSON_Success verifies JSON serialization and POST
func TestPostJSON_Success(t *testing.T) {
	// GIVEN: Server expects JSON payload
	type Request struct {
		Name  string `json:"name"`
		Count int    `json:"count"`
	}
	type Response struct {
		Status string `json:"status"`
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req Request
		json.NewDecoder(r.Body).Decode(&req)
		assert.Equal(t, "test", req.Name)
		assert.Equal(t, 42, req.Count)

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(Response{Status: "ok"})
	}))
	defer server.Close()

	// WHEN: Client posts JSON payload
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	payload := Request{Name: "test", Count: 42}
	body, err := client.PostJSON(ctx, "/api", payload)

	// THEN: Response is returned successfully
	require.NoError(t, err)
	assert.Contains(t, string(body), "ok")
}

// TestPostJSON_MarshalError verifies invalid payload handling
func TestPostJSON_MarshalError(t *testing.T) {
	// GIVEN: Client with valid server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// WHEN: Payload cannot be marshaled (channel type)
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	invalidPayload := make(chan int) // channels cannot be JSON marshaled
	_, err := client.PostJSON(ctx, "/api", invalidPayload)

	// THEN: Marshal error is returned
	require.Error(t, err)
	assert.Contains(t, err.Error(), "marshal")
}

// TestPut_Success verifies successful PUT request
func TestPut_Success(t *testing.T) {
	// GIVEN: Server accepts PUT
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "PUT", r.Method)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("updated"))
	}))
	defer server.Close()

	// WHEN: Client makes PUT request
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	body, err := client.Put(ctx, "/resource/1", []byte(`{"name":"updated"}`))

	// THEN: Response is returned successfully
	require.NoError(t, err)
	assert.Contains(t, string(body), "updated")
}

// TestDelete_Success verifies successful DELETE request
func TestDelete_Success(t *testing.T) {
	// GIVEN: Server accepts DELETE
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "DELETE", r.Method)
		assert.Equal(t, "/resource/1", r.URL.Path)
		w.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	// WHEN: Client makes DELETE request
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	_, err := client.Delete(ctx, "/resource/1")

	// THEN: No error returned
	require.NoError(t, err)
}

// TestGetJSON_Success verifies JSON deserialization
func TestGetJSON_Success(t *testing.T) {
	// GIVEN: Server returns JSON object
	type User struct {
		ID   int    `json:"id"`
		Name string `json:"name"`
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(User{ID: 1, Name: "Alice"})
	}))
	defer server.Close()

	// WHEN: Client requests JSON
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	var user User
	err := client.GetJSON(ctx, "/user/1", &user)

	// THEN: Result is deserialized correctly
	require.NoError(t, err)
	assert.Equal(t, 1, user.ID)
	assert.Equal(t, "Alice", user.Name)
}

// TestGetJSON_InvalidJSON verifies unmarshal error handling
func TestGetJSON_InvalidJSON(t *testing.T) {
	// GIVEN: Server returns invalid JSON
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("not valid json"))
	}))
	defer server.Close()

	// WHEN: Client tries to unmarshal
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	var result map[string]string
	err := client.GetJSON(ctx, "/bad", &result)

	// THEN: Unmarshal error is returned
	require.Error(t, err)
	assert.Contains(t, err.Error(), "unmarshal")
}

// TestPostJSONResponse_Success verifies full JSON request/response cycle
func TestPostJSONResponse_Success(t *testing.T) {
	// GIVEN: Server accepts and returns JSON
	type Request struct {
		Query string `json:"query"`
	}
	type Response struct {
		Result string `json:"result"`
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req Request
		json.NewDecoder(r.Body).Decode(&req)

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(Response{Result: "answer for " + req.Query})
	}))
	defer server.Close()

	// WHEN: Client posts JSON and expects JSON response
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	payload := Request{Query: "test"}
	var response Response
	err := client.PostJSONResponse(ctx, "/search", payload, &response)

	// THEN: Response is deserialized correctly
	require.NoError(t, err)
	assert.Equal(t, "answer for test", response.Result)
}

// TestHealthCheck_Success verifies health check endpoint
func TestHealthCheck_Success(t *testing.T) {
	// GIVEN: Server has healthy /health endpoint
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/health", r.URL.Path)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("healthy"))
	}))
	defer server.Close()

	// WHEN: Client performs health check
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	err := client.HealthCheck(ctx)

	// THEN: No error returned
	require.NoError(t, err)
}

// TestHealthCheck_Unhealthy verifies unhealthy service detection
func TestHealthCheck_Unhealthy(t *testing.T) {
	// GIVEN: Server returns 503
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("unhealthy"))
	}))
	defer server.Close()

	// WHEN: Client performs health check
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	err := client.HealthCheck(ctx)

	// THEN: Error is returned
	require.Error(t, err)
	assert.Contains(t, err.Error(), "503")
}

// TestDoRequest_WithCircuitBreaker verifies circuit breaker integration
func TestDoRequest_WithCircuitBreaker(t *testing.T) {
	// GIVEN: Server that fails consistently
	attempts := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	// WHEN: Client makes multiple requests (circuit should open)
	config := ClientConfig{
		BaseURL: server.URL,
		RetryConfig: RetryConfig{
			MaxAttempts:  1, // No retries to test breaker faster
			InitialDelay: 1 * time.Millisecond,
			MaxDelay:     10 * time.Millisecond,
			Multiplier:   2.0,
		},
		BreakerConfig: BreakerConfig{
			MaxFailures:  3,
			OpenTimeout:  100 * time.Millisecond,
			HalfOpenMax:  1,
			SuccessReset: 1,
		},
	}
	client := NewClient(config)
	ctx := context.Background()

	// First 3 requests fail, circuit opens
	for i := 0; i < 3; i++ {
		_, err := client.Get(ctx, "/test")
		require.Error(t, err)
	}

	// THEN: Circuit is now open, subsequent requests fail immediately
	startTime := time.Now()
	_, err := client.Get(ctx, "/test")
	duration := time.Since(startTime)

	require.Error(t, err)
	assert.Contains(t, err.Error(), "CIRCUIT_OPEN")
	assert.Less(t, duration, 50*time.Millisecond, "Circuit breaker should reject immediately")
	assert.Equal(t, 3, attempts, "Should not attempt request when circuit is open")
}

// TestDoRequest_CustomHeaders verifies custom headers are sent
func TestDoRequest_CustomHeaders(t *testing.T) {
	// GIVEN: Server expects custom headers
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "Bearer token123", r.Header.Get("Authorization"))
		assert.Equal(t, "custom-value", r.Header.Get("X-Custom"))
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// WHEN: Client sends request with custom headers
	config := DefaultClientConfig(server.URL)
	config.Headers["Authorization"] = "Bearer token123"
	config.Headers["X-Custom"] = "custom-value"
	client := NewClient(config)
	ctx := context.Background()
	_, err := client.Get(ctx, "/test")

	// THEN: Headers are sent correctly
	require.NoError(t, err)
}

// TestDoRequest_PathCombination verifies BaseURL + path handling
func TestDoRequest_PathCombination(t *testing.T) {
	tests := []struct {
		name     string
		basePath string // what to append to server.URL
		reqPath  string // path to request
		expected string // expected final path
	}{
		{
			name:     "base without slash, path with slash",
			basePath: "",
			reqPath:  "/api/test",
			expected: "/api/test",
		},
		{
			name:     "base with path, path with slash",
			basePath: "/v1",
			reqPath:  "/users",
			expected: "/v1/users",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// GIVEN: Server that captures request path
			var capturedPath string
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				capturedPath = r.URL.Path
				w.WriteHeader(http.StatusOK)
			}))
			defer server.Close()

			// WHEN: Client makes request
			config := DefaultClientConfig(server.URL + tt.basePath)
			client := NewClient(config)
			ctx := context.Background()
			_, err := client.Get(ctx, tt.reqPath)

			// THEN: Path is combined correctly
			require.NoError(t, err)
			assert.Equal(t, tt.expected, capturedPath)
		})
	}
}

// TestClient_Integration_RetryThenSuccess verifies retry succeeds eventually
func TestClient_Integration_RetryThenSuccess(t *testing.T) {
	// GIVEN: Server that fails first 2 attempts, then succeeds
	attempts := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		if attempts < 3 {
			w.WriteHeader(http.StatusServiceUnavailable)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{"status": "success"})
	}))
	defer server.Close()

	// WHEN: Client retries (3 max attempts)
	config := ClientConfig{
		BaseURL:     server.URL,
		BreakerConfig: DefaultBreakerConfig(),
		RetryConfig: RetryConfig{
			MaxAttempts:  3,
			InitialDelay: 10 * time.Millisecond,
			MaxDelay:     50 * time.Millisecond,
			Multiplier:   2.0,
		},
	}
	client := NewClient(config)
	ctx := context.Background()
	body, err := client.Get(ctx, "/test")

	// THEN: Request succeeds on 3rd attempt
	require.NoError(t, err)
	assert.Contains(t, string(body), "success")
	assert.Equal(t, 3, attempts, "Should attempt 3 times before success")
}

// TestSetLogger verifies logger can be set
func TestSetLogger(t *testing.T) {
	// GIVEN: Client with default logger
	client := NewClient(DefaultClientConfig("http://localhost:8080"))

	// WHEN: Custom logger is set
	customLogger := log.New(io.Discard, "[TEST] ", log.LstdFlags)
	client.SetLogger(customLogger)

	// THEN: Logger is updated
	assert.NotNil(t, client.Logger)
	assert.Equal(t, customLogger, client.Logger)
}

// TestGetCircuitBreakerState verifies circuit breaker state can be queried
func TestGetCircuitBreakerState(t *testing.T) {
	// GIVEN: Client with circuit breaker
	client := NewClient(DefaultClientConfig("http://localhost:8080"))

	// WHEN: Get circuit breaker state
	state := client.GetCircuitBreakerState()

	// THEN: State is "closed" initially
	assert.Equal(t, "closed", state)
}

// TestResetCircuitBreaker verifies circuit breaker can be reset
func TestResetCircuitBreaker(t *testing.T) {
	// GIVEN: Client with open circuit breaker
	attempts := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	config := DefaultClientConfig(server.URL)
	config.RetryConfig.MaxAttempts = 1
	config.BreakerConfig.MaxFailures = 2
	client := NewClient(config)
	ctx := context.Background()

	// Open circuit with failures
	for i := 0; i < 2; i++ {
		client.Get(ctx, "/test")
	}

	assert.Equal(t, "open", client.GetCircuitBreakerState())

	// WHEN: Circuit breaker is reset
	client.ResetCircuitBreaker()

	// THEN: Circuit is closed again
	assert.Equal(t, "closed", client.GetCircuitBreakerState())
}

// TestGetJSON_NetworkError verifies network error handling
func TestGetJSON_NetworkError(t *testing.T) {
	// GIVEN: Client with invalid URL
	client := NewClient(DefaultClientConfig("http://invalid-host-that-does-not-exist:99999"))

	// WHEN: Request fails with network error
	ctx := context.Background()
	var result map[string]string
	err := client.GetJSON(ctx, "/test", &result)

	// THEN: Network error is returned
	require.Error(t, err)
	assert.Contains(t, err.Error(), "NETWORK")
}

// TestPostJSONResponse_NetworkError verifies network error handling in POST
func TestPostJSONResponse_NetworkError(t *testing.T) {
	// GIVEN: Client with invalid URL
	client := NewClient(DefaultClientConfig("http://invalid-host-that-does-not-exist:99999"))

	// WHEN: POST request fails with network error
	ctx := context.Background()
	payload := map[string]string{"key": "value"}
	var result map[string]string
	err := client.PostJSONResponse(ctx, "/test", payload, &result)

	// THEN: Network error is returned
	require.Error(t, err)
	assert.Contains(t, err.Error(), "NETWORK")
}

// TestPostJSONResponse_UnmarshalError verifies unmarshal error handling
func TestPostJSONResponse_UnmarshalError(t *testing.T) {
	// GIVEN: Server returns invalid JSON
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("not valid json"))
	}))
	defer server.Close()

	// WHEN: Client tries to unmarshal invalid JSON
	client := NewClient(DefaultClientConfig(server.URL))
	ctx := context.Background()
	payload := map[string]string{"key": "value"}
	var result map[string]string
	err := client.PostJSONResponse(ctx, "/test", payload, &result)

	// THEN: Unmarshal error is returned
	require.Error(t, err)
	assert.Contains(t, err.Error(), "unmarshal")
}

// TestClient_Integration_CircuitRecovery verifies circuit breaker recovery
func TestClient_Integration_CircuitRecovery(t *testing.T) {
	// GIVEN: Server that starts failing, then recovers
	shouldFail := true
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if shouldFail {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("recovered"))
	}))
	defer server.Close()

	// WHEN: Circuit opens from failures, then service recovers
	config := ClientConfig{
		BaseURL: server.URL,
		RetryConfig: RetryConfig{
			MaxAttempts:  1,
			InitialDelay: 1 * time.Millisecond,
			MaxDelay:     10 * time.Millisecond,
			Multiplier:   2.0,
		},
		BreakerConfig: BreakerConfig{
			MaxFailures:  3,
			OpenTimeout:  100 * time.Millisecond,
			HalfOpenMax:  2,
			SuccessReset: 1,
		},
	}
	client := NewClient(config)
	ctx := context.Background()

	// Trigger failures to open circuit
	for i := 0; i < 3; i++ {
		_, err := client.Get(ctx, "/test")
		require.Error(t, err)
	}

	// Circuit is now open
	_, err := client.Get(ctx, "/test")
	require.Error(t, err)
	assert.Contains(t, err.Error(), "CIRCUIT_OPEN")

	// Wait for open timeout to transition to half-open
	time.Sleep(150 * time.Millisecond)

	// Service recovers
	shouldFail = false

	// THEN: Circuit recovers to closed state
	body, err := client.Get(ctx, "/test")
	require.NoError(t, err)
	assert.Contains(t, string(body), "recovered")

	// Circuit should now be closed, subsequent requests succeed
	body, err = client.Get(ctx, "/test")
	require.NoError(t, err)
	assert.Contains(t, string(body), "recovered")
}
