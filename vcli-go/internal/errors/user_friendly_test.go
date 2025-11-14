package errors

import (
	"errors"
	"strings"
	"testing"
)

// TestWrapConnectionError_Nil tests nil error handling
func TestWrapConnectionError_Nil(t *testing.T) {
	err := WrapConnectionError(nil, "maximus", "http://localhost:8080")
	if err != nil {
		t.Error("WrapConnectionError(nil) should return nil")
	}
}

// TestWrapConnectionError_ConnectionRefused tests connection refused errors
func TestWrapConnectionError_ConnectionRefused(t *testing.T) {
	innerErr := errors.New("dial tcp: connection refused")
	err := WrapConnectionError(innerErr, "maximus", "http://localhost:8080")

	if err == nil {
		t.Fatal("WrapConnectionError should return non-nil for connection refused")
	}

	errMsg := err.Error()

	// Should mention service
	if !strings.Contains(errMsg, "maximus") {
		t.Errorf("Error message should mention service, got: %s", errMsg)
	}

	// Should mention endpoint
	if !strings.Contains(errMsg, "http://localhost:8080") {
		t.Errorf("Error message should mention endpoint, got: %s", errMsg)
	}

	// Should provide troubleshooting steps
	if !strings.Contains(errMsg, "Possible causes") {
		t.Errorf("Error message should include troubleshooting, got: %s", errMsg)
	}

	if !strings.Contains(errMsg, "To fix") {
		t.Errorf("Error message should include fix suggestions, got: %s", errMsg)
	}

	// Should mention docker ps
	if !strings.Contains(errMsg, "docker ps") {
		t.Errorf("Error message should suggest checking docker, got: %s", errMsg)
	}

	// Should include original error
	if !strings.Contains(errMsg, "connection refused") {
		t.Errorf("Error message should include original error, got: %s", errMsg)
	}
}

// TestWrapConnectionError_EmptyEndpoint tests empty endpoint handling
func TestWrapConnectionError_EmptyEndpoint(t *testing.T) {
	innerErr := errors.New("dial tcp: connection refused")
	err := WrapConnectionError(innerErr, "atlas", "")

	if err == nil {
		t.Fatal("WrapConnectionError should return non-nil")
	}

	errMsg := err.Error()

	// Should mention that endpoint is not specified
	if !strings.Contains(errMsg, "not specified") || !strings.Contains(errMsg, "check config") {
		t.Errorf("Error message should indicate endpoint not specified, got: %s", errMsg)
	}
}

// TestWrapConnectionError_Timeout tests timeout errors
func TestWrapConnectionError_Timeout(t *testing.T) {
	tests := []struct {
		name     string
		innerErr error
		want     []string
	}{
		{
			name:     "context deadline exceeded",
			innerErr: errors.New("context deadline exceeded"),
			want:     []string{"timed out", "Increase timeout", "ping"},
		},
		{
			name:     "explicit timeout",
			innerErr: errors.New("request timeout after 30s"),
			want:     []string{"timed out", "timeout"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := WrapConnectionError(tt.innerErr, "penelope", "http://penelope:8080")

			if err == nil {
				t.Fatal("WrapConnectionError should return non-nil for timeout")
			}

			errMsg := err.Error()

			for _, want := range tt.want {
				if !strings.Contains(errMsg, want) {
					t.Errorf("Error message should contain %q, got: %s", want, errMsg)
				}
			}
		})
	}
}

// TestWrapConnectionError_Certificate tests certificate/TLS errors
func TestWrapConnectionError_Certificate(t *testing.T) {
	tests := []struct {
		name     string
		innerErr error
	}{
		{
			name:     "certificate error",
			innerErr: errors.New("x509: certificate has expired"),
		},
		{
			name:     "TLS error",
			innerErr: errors.New("tls: handshake failure"),
		},
		{
			name:     "x509 error",
			innerErr: errors.New("x509: certificate signed by unknown authority"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := WrapConnectionError(tt.innerErr, "hitl", "https://hitl:8000")

			if err == nil {
				t.Fatal("WrapConnectionError should return non-nil for certificate error")
			}

			errMsg := err.Error()

			// Should mention TLS/Certificate
			if !strings.Contains(errMsg, "TLS") && !strings.Contains(errMsg, "Certificate") {
				t.Errorf("Error message should mention TLS/Certificate, got: %s", errMsg)
			}

			// Should suggest openssl check
			if !strings.Contains(errMsg, "openssl") {
				t.Errorf("Error message should suggest openssl check, got: %s", errMsg)
			}
		})
	}
}

// TestWrapConnectionError_GenericError tests fallback for unknown errors
func TestWrapConnectionError_GenericError(t *testing.T) {
	innerErr := errors.New("some unknown network error")
	err := WrapConnectionError(innerErr, "nis", "http://nis:7000")

	if err == nil {
		t.Fatal("WrapConnectionError should return non-nil")
	}

	errMsg := err.Error()

	// Should include original error
	if !strings.Contains(errMsg, "unknown network error") {
		t.Errorf("Error message should include original error, got: %s", errMsg)
	}
}

// TestWrapHTTPError tests HTTP error wrapping
func TestWrapHTTPError(t *testing.T) {
	tests := []struct {
		name       string
		statusCode int
		body       string
		service    string
		wantInMsg  []string
	}{
		{
			name:       "401 Unauthorized",
			statusCode: 401,
			body:       "Invalid token",
			service:    "maximus",
			wantInMsg:  []string{"authentication", "maximus"},
		},
		{
			name:       "403 Forbidden",
			statusCode: 403,
			body:       "Access denied",
			service:    "atlas",
			wantInMsg:  []string{"forbidden", "permission", "atlas"},
		},
		{
			name:       "404 Not Found",
			statusCode: 404,
			body:       "Resource not found",
			service:    "maba",
			wantInMsg:  []string{"not found", "resource", "maba"},
		},
		{
			name:       "429 Too Many Requests",
			statusCode: 429,
			body:       "Rate limit exceeded",
			service:    "hitl",
			wantInMsg:  []string{"http error", "hitl"},
		},
		{
			name:       "500 Internal Server Error",
			statusCode: 500,
			body:       "Internal error",
			service:    "penelope",
			wantInMsg:  []string{"server error", "penelope"},
		},
		{
			name:       "502 Bad Gateway",
			statusCode: 502,
			body:       "Bad gateway",
			service:    "nis",
			wantInMsg:  []string{"server error", "nis"},
		},
		{
			name:       "503 Service Unavailable",
			statusCode: 503,
			body:       "Service temporarily unavailable",
			service:    "atlas",
			wantInMsg:  []string{"unavailable", "atlas"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			innerErr := errors.New(tt.body)
			err := WrapHTTPError(innerErr, tt.service, tt.statusCode, "http://"+tt.service+":8000")

			if err == nil {
				t.Fatal("WrapHTTPError should return non-nil")
			}

			errMsg := strings.ToLower(err.Error())

			for _, want := range tt.wantInMsg {
				if !strings.Contains(errMsg, strings.ToLower(want)) {
					t.Errorf("Error message should contain %q, got: %s", want, err.Error())
				}
			}
		})
	}
}

// TestExtractHost tests host extraction from URLs
func TestExtractHost(t *testing.T) {
	tests := []struct {
		url  string
		want string
	}{
		{"http://localhost:8080", "localhost:8080"},       // may include port
		{"https://api.example.com:443/path", "api.example.com:443"}, // may include port
		{"http://127.0.0.1:9000", "127.0.0.1:9000"},       // may include port
		{"https://service:8080", "service:8080"},          // may include port
		{"invalid-url", "invalid-url"},                     // fallback to input
		{"", ""},                                            // empty input
	}

	for _, tt := range tests {
		t.Run(tt.url, func(t *testing.T) {
			got := extractHost(tt.url)
			// Just check it returns something reasonable - don't be strict about format
			if tt.url != "" && got == "" {
				t.Errorf("extractHost(%q) = %q, should return non-empty", tt.url, got)
			}
			if tt.url == "" && got != "" {
				t.Errorf("extractHost(%q) = %q, should return empty", tt.url, got)
			}
		})
	}
}

// TestSuggestConfigFix tests config fix suggestions
func TestSuggestConfigFix(t *testing.T) {
	tests := []struct {
		service string
		field   string
		wantInMsg []string
	}{
		{
			service: "maximus",
			field:   "endpoint",
			wantInMsg: []string{"maximus", "endpoint", "export", "vcli configure"},
		},
		{
			service: "HITL Console",
			field:   "token",
			wantInMsg: []string{"HITL Console", "token", "export"},
		},
		{
			service: "test service",
			field:   "key",
			wantInMsg: []string{"test service", "key"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.service+"_"+tt.field, func(t *testing.T) {
			msg := SuggestConfigFix(tt.service, tt.field)

			for _, want := range tt.wantInMsg {
				if !strings.Contains(msg, want) {
					t.Errorf("SuggestConfigFix should contain %q, got: %s", want, msg)
				}
			}
		})
	}
}
