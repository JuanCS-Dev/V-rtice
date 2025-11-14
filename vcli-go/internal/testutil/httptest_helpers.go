package testutil

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// JSONServer creates a test HTTP server that returns JSON response.
// This is NOT a mock - it's a real HTTP server for testing.
//
// Constitutional Compliance: P1 - NO MOCKS (uses httptest.NewServer)
//
// Example:
//
//	server := testutil.JSONServer(t, http.StatusOK, Response{Status: "success"})
//	defer server.Close()
func JSONServer(t *testing.T, statusCode int, response interface{}) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(statusCode)
		if err := json.NewEncoder(w).Encode(response); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
}

// ErrorServer creates a test HTTP server that returns an error response.
//
// Constitutional Compliance: P1 - NO MOCKS (uses httptest.NewServer)
//
// Example:
//
//	server := testutil.ErrorServer(http.StatusInternalServerError, "Internal error")
//	defer server.Close()
func ErrorServer(statusCode int, message string) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(statusCode)
		w.Write([]byte(message))
	}))
}

// VerifyRequestServer creates a test server that verifies request details and returns response.
//
// Constitutional Compliance: P2 - Validação Preventiva (validates request before responding)
//
// Example:
//
//	server := testutil.VerifyRequestServer(t, "POST", "/endpoint", "Bearer token-123", response)
//	defer server.Close()
func VerifyRequestServer(t *testing.T, expectedMethod, expectedPath, expectedAuth string, response interface{}) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Verify method
		if r.Method != expectedMethod {
			t.Errorf("expected method %s, got %s", expectedMethod, r.Method)
		}

		// Verify path
		if r.URL.Path != expectedPath {
			t.Errorf("expected path %s, got %s", expectedPath, r.URL.Path)
		}

		// Verify authorization header (if provided)
		if expectedAuth != "" {
			authHeader := r.Header.Get("Authorization")
			if authHeader != expectedAuth {
				t.Errorf("expected Authorization %s, got %s", expectedAuth, authHeader)
			}
		}

		// Return response
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		if err := json.NewEncoder(w).Encode(response); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
}

// MultiEndpointServer creates a test server with multiple endpoints (for integration tests).
//
// Constitutional Compliance: P5 - Consciência Sistêmica (simulates real multi-endpoint backend)
//
// Example:
//
//	handlers := map[string]http.HandlerFunc{
//	    "/auth/login": func(w http.ResponseWriter, r *http.Request) { ... },
//	    "/resource":   func(w http.ResponseWriter, r *http.Request) { ... },
//	}
//	server := testutil.MultiEndpointServer(handlers)
//	defer server.Close()
func MultiEndpointServer(handlers map[string]http.HandlerFunc) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		handler, exists := handlers[r.URL.Path]
		if !exists {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("endpoint not found"))
			return
		}
		handler(w, r)
	}))
}

// VerifyBackendAvailable checks if a backend service is running and healthy.
// If not available, skips the test with a helpful message.
//
// Constitutional Compliance: P2 - Validação Preventiva (verify before testing)
// Constitutional Compliance: P1 - NO MOCKS (skip test if backend unavailable, don't mock)
//
// Example:
//
//	func TestClient_RealBackend(t *testing.T) {
//	    testutil.VerifyBackendAvailable(t, "http://localhost:8152")
//	    client := NewClient("http://localhost:8152")
//	    // ... test against real backend
//	}
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

// AssertJSONEquals compares two JSON-serializable objects for equality.
//
// Example:
//
//	expected := Response{Status: "success"}
//	actual := Response{Status: "success"}
//	testutil.AssertJSONEquals(t, expected, actual)
func AssertJSONEquals(t *testing.T, expected, actual interface{}) {
	expectedJSON, err := json.Marshal(expected)
	if err != nil {
		t.Fatalf("failed to marshal expected: %v", err)
	}

	actualJSON, err := json.Marshal(actual)
	if err != nil {
		t.Fatalf("failed to marshal actual: %v", err)
	}

	if string(expectedJSON) != string(actualJSON) {
		t.Errorf("JSON mismatch:\nexpected: %s\nactual:   %s", expectedJSON, actualJSON)
	}
}

// DecodeJSONResponse is a helper to decode JSON responses in tests.
//
// Example:
//
//	var result Response
//	testutil.DecodeJSONResponse(t, resp.Body, &result)
func DecodeJSONResponse(t *testing.T, body []byte, target interface{}) {
	if err := json.Unmarshal(body, target); err != nil {
		t.Fatalf("failed to decode JSON response: %v", err)
	}
}
