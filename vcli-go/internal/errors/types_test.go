package errors

import (
	"errors"
	"strings"
	"testing"
)

// TestVCLIError_Error tests the Error() method
func TestVCLIError_Error(t *testing.T) {
	tests := []struct {
		name string
		err  *VCLIError
		want []string // strings that should be present
	}{
		{
			name: "basic error",
			err: &VCLIError{
				Type:    ErrorTypeConnection,
				Message: "failed to connect",
			},
			want: []string{"CONNECTION", "failed to connect"},
		},
		{
			name: "error with service",
			err: &VCLIError{
				Type:    ErrorTypeAuth,
				Message: "invalid credentials",
				Service: "maximus",
			},
			want: []string{"[maximus]", "AUTH", "invalid credentials"},
		},
		{
			name: "error with details",
			err: &VCLIError{
				Type:    ErrorTypeValidation,
				Message: "invalid input",
				Details: "field 'name' is required",
			},
			want: []string{"VALIDATION", "invalid input", "(field 'name' is required)"},
		},
		{
			name: "full error",
			err: &VCLIError{
				Type:    ErrorTypeTimeout,
				Message: "request timed out",
				Details: "exceeded 30s deadline",
				Service: "atlas",
			},
			want: []string{"[atlas]", "TIMEOUT", "request timed out", "(exceeded 30s deadline)"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.err.Error()
			for _, want := range tt.want {
				if !strings.Contains(got, want) {
					t.Errorf("Error() = %q, want to contain %q", got, want)
				}
			}
		})
	}
}

// TestVCLIError_Unwrap tests error unwrapping
func TestVCLIError_Unwrap(t *testing.T) {
	innerErr := errors.New("inner error")
	err := &VCLIError{
		Type:    ErrorTypeConnection,
		Message: "connection failed",
		Cause:   innerErr,
	}

	unwrapped := errors.Unwrap(err)
	if unwrapped != innerErr {
		t.Errorf("Unwrap() = %v, want %v", unwrapped, innerErr)
	}

	// Test nil cause
	errNoCause := &VCLIError{
		Type:    ErrorTypeConnection,
		Message: "test",
	}
	if errors.Unwrap(errNoCause) != nil {
		t.Error("Unwrap() should return nil for error without cause")
	}
}

// TestVCLIError_IsRetryable tests retryability checking
func TestVCLIError_IsRetryable(t *testing.T) {
	tests := []struct {
		name      string
		err       *VCLIError
		retryable bool
	}{
		{
			name:      "timeout is retryable",
			err:       &VCLIError{Type: ErrorTypeTimeout, Retryable: true},
			retryable: true,
		},
		{
			name:      "network is retryable",
			err:       &VCLIError{Type: ErrorTypeNetwork, Retryable: true},
			retryable: true,
		},
		{
			name:      "unavailable is retryable",
			err:       &VCLIError{Type: ErrorTypeUnavailable, Retryable: true},
			retryable: true,
		},
		{
			name:      "auth is not retryable",
			err:       &VCLIError{Type: ErrorTypeAuth, Retryable: false},
			retryable: false,
		},
		{
			name:      "validation is not retryable",
			err:       &VCLIError{Type: ErrorTypeValidation, Retryable: false},
			retryable: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.err.IsRetryable()
			if got != tt.retryable {
				t.Errorf("IsRetryable() = %v, want %v", got, tt.retryable)
			}
		})
	}
}

// TestVCLIError_WithCause tests adding a cause
func TestVCLIError_WithCause(t *testing.T) {
	cause := errors.New("root cause")
	err := &VCLIError{
		Type:    ErrorTypeConnection,
		Message: "failed",
	}

	result := err.WithCause(cause)

	if result.Cause != cause {
		t.Errorf("WithCause() did not set cause correctly")
	}

	// Should return same instance for method chaining
	if result != err {
		t.Error("WithCause() should return same instance for method chaining")
	}
}

// TestVCLIError_WithDetails tests adding details
func TestVCLIError_WithDetails(t *testing.T) {
	details := "additional context"
	err := &VCLIError{
		Type:    ErrorTypeValidation,
		Message: "failed",
	}

	result := err.WithDetails(details)

	if result.Details != details {
		t.Errorf("WithDetails() did not set details correctly")
	}

	// Should return same instance for method chaining
	if result != err {
		t.Error("WithDetails() should return same instance for method chaining")
	}
}

// TestVCLIError_MethodChaining tests method chaining
func TestVCLIError_MethodChaining(t *testing.T) {
	cause := errors.New("cause")
	err := New(ErrorTypeConnection, "failed").
		WithCause(cause).
		WithDetails("timeout after 30s")

	if err.Cause != cause {
		t.Error("Method chaining: cause not set")
	}
	if err.Details != "timeout after 30s" {
		t.Error("Method chaining: details not set")
	}
}

// TestNew tests the New constructor
func TestNew(t *testing.T) {
	tests := []struct {
		name      string
		errType   ErrorType
		message   string
		retryable bool
	}{
		{"timeout", ErrorTypeTimeout, "request timed out", true},
		{"network", ErrorTypeNetwork, "connection refused", true},
		{"unavailable", ErrorTypeUnavailable, "service down", true},
		{"auth", ErrorTypeAuth, "invalid token", false},
		{"validation", ErrorTypeValidation, "invalid input", false},
		{"not_found", ErrorTypeNotFound, "resource missing", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := New(tt.errType, tt.message)

			if err.Type != tt.errType {
				t.Errorf("Type = %v, want %v", err.Type, tt.errType)
			}
			if err.Message != tt.message {
				t.Errorf("Message = %q, want %q", err.Message, tt.message)
			}
			if err.Retryable != tt.retryable {
				t.Errorf("Retryable = %v, want %v", err.Retryable, tt.retryable)
			}
		})
	}
}

// TestWrap tests the Wrap function
func TestWrap(t *testing.T) {
	cause := errors.New("original error")
	err := Wrap(cause, ErrorTypeTimeout, "request timed out")

	if err.Type != ErrorTypeTimeout {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeTimeout)
	}
	if err.Message != "request timed out" {
		t.Errorf("Message = %q, want %q", err.Message, "request timed out")
	}
	if err.Cause != cause {
		t.Error("Cause not set correctly")
	}
	if !err.Retryable {
		t.Error("Timeout error should be retryable")
	}

	// Test unwrapping
	if !errors.Is(err, cause) {
		t.Error("errors.Is() should find wrapped error")
	}
}

// TestNewConnectionError tests connection error constructor
func TestNewConnectionError(t *testing.T) {
	err := NewConnectionError("maximus", "connection refused")

	if err.Type != ErrorTypeConnection {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeConnection)
	}
	if err.Service != "maximus" {
		t.Errorf("Service = %q, want %q", err.Service, "maximus")
	}
	if err.Message != "connection refused" {
		t.Errorf("Message = %q, want %q", err.Message, "connection refused")
	}
	if !err.Retryable {
		t.Error("Connection errors should be retryable")
	}
}

// TestNewTimeoutError tests timeout error constructor
func TestNewTimeoutError(t *testing.T) {
	err := NewTimeoutError("atlas", "request deadline exceeded")

	if err.Type != ErrorTypeTimeout {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeTimeout)
	}
	if err.Service != "atlas" {
		t.Errorf("Service = %q, want %q", err.Service, "atlas")
	}
	if !err.Retryable {
		t.Error("Timeout errors should be retryable")
	}
}

// TestNewAuthError tests auth error constructor
func TestNewAuthError(t *testing.T) {
	err := NewAuthError("maba", "invalid credentials")

	if err.Type != ErrorTypeAuth {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeAuth)
	}
	if err.Service != "maba" {
		t.Errorf("Service = %q, want %q", err.Service, "maba")
	}
	if err.Retryable {
		t.Error("Auth errors should not be retryable")
	}
}

// TestNewValidationError tests validation error constructor
func TestNewValidationError(t *testing.T) {
	err := NewValidationError("field is required")

	if err.Type != ErrorTypeValidation {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeValidation)
	}
	if err.Message != "field is required" {
		t.Errorf("Message = %q, want %q", err.Message, "field is required")
	}
	if err.Retryable {
		t.Error("Validation errors should not be retryable")
	}
}

// TestNewNotFoundError tests not found error constructor
func TestNewNotFoundError(t *testing.T) {
	err := NewNotFoundError("pod")

	if err.Type != ErrorTypeNotFound {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeNotFound)
	}
	if !strings.Contains(err.Message, "pod") {
		t.Errorf("Message = %q, want to contain 'pod'", err.Message)
	}
	if err.Retryable {
		t.Error("Not found errors should not be retryable")
	}
}

// TestNewServerError tests server error constructor
func TestNewServerError(t *testing.T) {
	err := NewServerError("penelope", "internal server error")

	if err.Type != ErrorTypeServer {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeServer)
	}
	if err.Service != "penelope" {
		t.Errorf("Service = %q, want %q", err.Service, "penelope")
	}
	if err.Retryable {
		t.Error("Server errors should not be retryable by default")
	}
}

// TestNewUnavailableError tests unavailable error constructor
func TestNewUnavailableError(t *testing.T) {
	err := NewUnavailableError("nis")

	if err.Type != ErrorTypeUnavailable {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeUnavailable)
	}
	if err.Service != "nis" {
		t.Errorf("Service = %q, want %q", err.Service, "nis")
	}
	if !err.Retryable {
		t.Error("Unavailable errors should be retryable")
	}
}

// TestNewConfigError tests config error constructor
func TestNewConfigError(t *testing.T) {
	err := NewConfigError("missing required field")

	if err.Type != ErrorTypeConfig {
		t.Errorf("Type = %v, want %v", err.Type, ErrorTypeConfig)
	}
	if err.Message != "missing required field" {
		t.Errorf("Message = %q, want %q", err.Message, "missing required field")
	}
	if err.Retryable {
		t.Error("Config errors should not be retryable")
	}
}

// TestNewHTTPError tests HTTP error constructor
func TestNewHTTPError(t *testing.T) {
	tests := []struct {
		name       string
		statusCode int
		body       string
		retryable  bool
	}{
		{"200 OK", 200, "success", false},
		{"400 Bad Request", 400, "invalid", false},
		{"401 Unauthorized", 401, "unauthorized", false},
		{"404 Not Found", 404, "not found", false},
		{"429 Too Many Requests", 429, "rate limited", true},
		{"500 Internal Server Error", 500, "error", true},
		{"502 Bad Gateway", 502, "gateway error", true},
		{"503 Service Unavailable", 503, "unavailable", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := NewHTTPError(tt.statusCode, tt.body)

			if err.StatusCode != tt.statusCode {
				t.Errorf("StatusCode = %d, want %d", err.StatusCode, tt.statusCode)
			}
			if err.Details != tt.body {
				t.Errorf("Details = %q, want %q", err.Details, tt.body)
			}
			if err.Retryable != tt.retryable {
				t.Errorf("Retryable = %v, want %v (status %d)", err.Retryable, tt.retryable, tt.statusCode)
			}
		})
	}
}

// TestIsRetryable tests the global IsRetryable function
func TestIsRetryable(t *testing.T) {
	tests := []struct {
		name      string
		err       error
		retryable bool
	}{
		{
			name:      "nil error",
			err:       nil,
			retryable: false,
		},
		{
			name:      "vcli error retryable",
			err:       &VCLIError{Type: ErrorTypeTimeout, Retryable: true},
			retryable: true,
		},
		{
			name:      "vcli error not retryable",
			err:       &VCLIError{Type: ErrorTypeAuth, Retryable: false},
			retryable: false,
		},
		{
			name:      "standard error",
			err:       errors.New("standard error"),
			retryable: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsRetryable(tt.err)
			if got != tt.retryable {
				t.Errorf("IsRetryable() = %v, want %v", got, tt.retryable)
			}
		})
	}
}

// TestErrorChain tests error chain traversal
func TestErrorChain(t *testing.T) {
	root := errors.New("root cause")
	wrapped := Wrap(root, ErrorTypeConnection, "connection failed")
	outer := Wrap(wrapped, ErrorTypeTimeout, "request timed out")

	// Test errors.Is traverses the chain
	if !errors.Is(outer, root) {
		t.Error("errors.Is() should find root cause in chain")
	}

	// Test errors.As finds first VCLIError
	var vcliErr *VCLIError
	if !errors.As(outer, &vcliErr) {
		t.Fatal("errors.As() should find VCLIError in chain")
	}

	if vcliErr.Type != ErrorTypeTimeout {
		t.Errorf("errors.As() found wrong error: got type %v, want %v", vcliErr.Type, ErrorTypeTimeout)
	}
}

// TestIsRetryableInternal tests the internal isRetryable function
func TestIsRetryableInternal(t *testing.T) {
	tests := []struct {
		errType   ErrorType
		retryable bool
	}{
		{ErrorTypeTimeout, true},
		{ErrorTypeNetwork, true},
		{ErrorTypeUnavailable, true},
		{ErrorTypeConnection, false},
		{ErrorTypeAuth, false},
		{ErrorTypeValidation, false},
		{ErrorTypeNotFound, false},
		{ErrorTypeServer, false},
		{ErrorTypeConfig, false},
	}

	for _, tt := range tests {
		t.Run(string(tt.errType), func(t *testing.T) {
			got := isRetryable(tt.errType)
			if got != tt.retryable {
				t.Errorf("isRetryable(%v) = %v, want %v", tt.errType, got, tt.retryable)
			}
		})
	}
}
