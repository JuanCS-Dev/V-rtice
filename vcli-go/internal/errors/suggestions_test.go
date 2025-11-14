package errors

import (
	"strings"
	"testing"
)

// TestContextualError_Error tests the Error() method
func TestContextualError_Error(t *testing.T) {
	base := NewConnectionError("maximus", "Failed to connect")
	ctx := ErrorContext{
		Endpoint: "http://localhost:8080",
	}
	err := &ContextualError{
		VCLIError: base,
		Context:   ctx,
	}

	got := err.Error()
	if !strings.Contains(got, "CONNECTION") {
		t.Errorf("Error() = %q, want to contain 'CONNECTION'", got)
	}
	if !strings.Contains(got, "Failed to connect") {
		t.Errorf("Error() = %q, want to contain 'Failed to connect'", got)
	}
}

// TestContextualError_Format tests the Format() method
func TestContextualError_Format(t *testing.T) {
	base := NewAuthError("hitl", "Authentication failed")
	ctx := ErrorContext{
		Endpoint: "http://localhost:8000",
		Operation: "Login",
		Suggestions: []Suggestion{
			{Description: "Check your credentials", Command: "vcli hitl login"},
			{Description: "Verify token expiry"},
		},
		HelpCommand: "vcli troubleshoot hitl",
	}
	err := &ContextualError{
		VCLIError: base,
		Context:   ctx,
	}

	formatted := err.Format()

	// Should contain error type
	if !strings.Contains(formatted, "AUTH") {
		t.Errorf("Format() missing error type, got: %s", formatted)
	}

	// Should contain service
	if !strings.Contains(formatted, "hitl") {
		t.Errorf("Format() missing service, got: %s", formatted)
	}

	// Should contain message
	if !strings.Contains(formatted, "Authentication failed") {
		t.Errorf("Format() missing message, got: %s", formatted)
	}

	// Should contain endpoint
	if !strings.Contains(formatted, "http://localhost:8000") {
		t.Errorf("Format() missing endpoint, got: %s", formatted)
	}

	// Should contain operation
	if !strings.Contains(formatted, "Login") {
		t.Errorf("Format() missing operation, got: %s", formatted)
	}

	// Should contain suggestions
	if !strings.Contains(formatted, "Check your credentials") {
		t.Errorf("Format() missing first suggestion, got: %s", formatted)
	}
	if !strings.Contains(formatted, "vcli hitl login") {
		t.Errorf("Format() missing first suggestion command, got: %s", formatted)
	}
	if !strings.Contains(formatted, "Verify token expiry") {
		t.Errorf("Format() missing second suggestion, got: %s", formatted)
	}

	// Should contain help command
	if !strings.Contains(formatted, "vcli troubleshoot hitl") {
		t.Errorf("Format() missing help command, got: %s", formatted)
	}
}

// TestContextualError_FormatMinimal tests Format with minimal context
func TestContextualError_FormatMinimal(t *testing.T) {
	base := NewValidationError("Invalid input")
	ctx := ErrorContext{}
	err := &ContextualError{
		VCLIError: base,
		Context:   ctx,
	}

	formatted := err.Format()

	// Should at least contain the error type and message
	if !strings.Contains(formatted, "VALIDATION") {
		t.Errorf("Format() missing error type, got: %s", formatted)
	}
	if !strings.Contains(formatted, "Invalid input") {
		t.Errorf("Format() missing message, got: %s", formatted)
	}
}

// TestNewContextualError tests the constructor
func TestNewContextualError(t *testing.T) {
	base := NewTimeoutError("atlas", "Request timed out")
	ctx := ErrorContext{
		Endpoint: "http://atlas:9000",
		Suggestions: []Suggestion{
			{Description: "Increase timeout"},
		},
	}

	err := NewContextualError(base, ctx)

	if err.VCLIError != base {
		t.Error("NewContextualError did not set base error correctly")
	}
	if err.Context.Endpoint != ctx.Endpoint {
		t.Error("NewContextualError did not set context correctly")
	}
	if len(err.Context.Suggestions) != 1 {
		t.Error("NewContextualError did not copy suggestions correctly")
	}
}

// TestGetSuggestionsFor tests suggestion generation
func TestGetSuggestionsFor(t *testing.T) {
	tests := []struct {
		name     string
		errType  ErrorType
		service  string
		endpoint string
		wantLen  int // minimum expected suggestions
	}{
		{
			name:     "connection error",
			errType:  ErrorTypeConnection,
			service:  "maximus",
			endpoint: "http://localhost:8080",
			wantLen:  1,
		},
		{
			name:     "timeout error",
			errType:  ErrorTypeTimeout,
			service:  "atlas",
			endpoint: "http://atlas:9000",
			wantLen:  1,
		},
		{
			name:     "auth error",
			errType:  ErrorTypeAuth,
			service:  "hitl",
			endpoint: "http://hitl:8000",
			wantLen:  1,
		},
		{
			name:    "validation error",
			errType: ErrorTypeValidation,
			wantLen: 1,
		},
		{
			name:    "not found error",
			errType: ErrorTypeNotFound,
			wantLen: 1,
		},
		{
			name:     "unavailable error",
			errType:  ErrorTypeUnavailable,
			service:  "nis",
			endpoint: "http://nis:7000",
			wantLen:  1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			suggestions := GetSuggestionsFor(tt.errType, tt.service, tt.endpoint)

			if len(suggestions) < tt.wantLen {
				t.Errorf("GetSuggestionsFor() returned %d suggestions, want at least %d", len(suggestions), tt.wantLen)
			}

			// Verify suggestions have descriptions
			for i, s := range suggestions {
				if s.Description == "" {
					t.Errorf("Suggestion %d has empty description", i)
				}
			}
		})
	}
}

// TestGetSuggestionsFor_UnknownType tests unknown error type
func TestGetSuggestionsFor_UnknownType(t *testing.T) {
	suggestions := GetSuggestionsFor("UNKNOWN", "", "")

	// Should return empty slice, not panic
	if suggestions == nil {
		t.Error("GetSuggestionsFor() returned nil for unknown type")
	}
}

// TestTimeoutSuggestions tests timeout-specific suggestions
func TestTimeoutSuggestions(t *testing.T) {
	// Test through GetSuggestionsFor since it's the public API
	suggestions := GetSuggestionsFor(ErrorTypeTimeout, "test-service", "http://test:8000")

	if len(suggestions) == 0 {
		t.Error("Timeout suggestions should not be empty")
	}

	// Check that at least one suggestion mentions timeout or retry
	found := false
	for _, s := range suggestions {
		lower := strings.ToLower(s.Description)
		if strings.Contains(lower, "timeout") || strings.Contains(lower, "retry") || strings.Contains(lower, "increase") {
			found = true
			break
		}
	}

	if !found {
		t.Error("Timeout suggestions should mention timeout, retry, or increase")
	}
}

// TestUnavailableSuggestions tests unavailable-specific suggestions
func TestUnavailableSuggestions(t *testing.T) {
	// Test through GetSuggestionsFor
	suggestions := GetSuggestionsFor(ErrorTypeUnavailable, "test-service", "http://test:8000")

	if len(suggestions) == 0 {
		t.Error("Unavailable suggestions should not be empty")
	}

	// Check that suggestions mention service availability
	found := false
	for _, s := range suggestions {
		lower := strings.ToLower(s.Description)
		if strings.Contains(lower, "service") || strings.Contains(lower, "running") || strings.Contains(lower, "health") {
			found = true
			break
		}
	}

	if !found {
		t.Error("Unavailable suggestions should mention service status")
	}
}

// TestSuggestion_Struct tests the Suggestion struct
func TestSuggestion_Struct(t *testing.T) {
	s := Suggestion{
		Description: "Test description",
		Command:     "vcli test",
	}

	if s.Description != "Test description" {
		t.Errorf("Description = %q, want %q", s.Description, "Test description")
	}
	if s.Command != "vcli test" {
		t.Errorf("Command = %q, want %q", s.Command, "vcli test")
	}
}

// TestErrorContext_Struct tests the ErrorContext struct
func TestErrorContext_Struct(t *testing.T) {
	ctx := ErrorContext{
		Endpoint:  "http://test:8000",
		Operation: "TestOp",
		Resource:  "pod/default/nginx",
		Suggestions: []Suggestion{
			{Description: "Try this"},
		},
		HelpCommand: "vcli help",
	}

	if ctx.Endpoint != "http://test:8000" {
		t.Error("Endpoint not set correctly")
	}
	if ctx.Operation != "TestOp" {
		t.Error("Operation not set correctly")
	}
	if ctx.Resource != "pod/default/nginx" {
		t.Error("Resource not set correctly")
	}
	if len(ctx.Suggestions) != 1 {
		t.Error("Suggestions not set correctly")
	}
	if ctx.HelpCommand != "vcli help" {
		t.Error("HelpCommand not set correctly")
	}
}
