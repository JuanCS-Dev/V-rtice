package errors

import (
	"errors"
	"strings"
	"testing"
)

// TestToolError_Error tests the Error() method
func TestToolError_Error(t *testing.T) {
	tests := []struct {
		name string
		err  *ToolError
		want string
	}{
		{
			name: "basic error message",
			err: &ToolError{
				Tool: "gosec",
				Err:  errors.New("not found in PATH"),
			},
			want: "gosec: not found in PATH",
		},
		{
			name: "with severity",
			err: &ToolError{
				Tool:     "kubectl",
				Err:      errors.New("connection refused"),
				Severity: SeverityError,
			},
			want: "kubectl: connection refused",
		},
		{
			name: "empty tool name",
			err: &ToolError{
				Tool: "",
				Err:  errors.New("some error"),
			},
			want: "some error",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.err.Error()
			if !strings.Contains(got, tt.want) {
				t.Errorf("Error() = %q, want to contain %q", got, tt.want)
			}
		})
	}
}

// TestToolError_Unwrap tests error unwrapping
func TestToolError_Unwrap(t *testing.T) {
	innerErr := errors.New("inner error")
	toolErr := &ToolError{
		Tool: "test",
		Err:  innerErr,
	}

	unwrapped := errors.Unwrap(toolErr)
	if unwrapped != innerErr {
		t.Errorf("Unwrap() = %v, want %v", unwrapped, innerErr)
	}
}

// TestToolError_Is tests error comparison with errors.Is
func TestToolError_Is(t *testing.T) {
	toolErr := &ToolError{
		Tool: "test",
		Err:  ErrToolNotFound,
	}

	if !errors.Is(toolErr, ErrToolNotFound) {
		t.Error("errors.Is() should return true for wrapped sentinel error")
	}
}

// TestToolError_As tests type assertion with errors.As
func TestToolError_As(t *testing.T) {
	originalErr := &ToolError{
		Tool:     "gosec",
		Err:      ErrToolNotFound,
		Severity: SeverityWarn,
	}

	var toolErr *ToolError
	if !errors.As(originalErr, &toolErr) {
		t.Fatal("errors.As() should succeed")
	}

	if toolErr.Tool != "gosec" {
		t.Errorf("Tool = %q, want %q", toolErr.Tool, "gosec")
	}

	if toolErr.Severity != SeverityWarn {
		t.Errorf("Severity = %v, want %v", toolErr.Severity, SeverityWarn)
	}
}

// TestToolError_IsFatal tests severity checking
func TestToolError_IsFatal(t *testing.T) {
	tests := []struct {
		name     string
		severity Severity
		want     bool
	}{
		{"fatal error", SeverityFatal, true},
		{"error severity", SeverityError, false},
		{"warn severity", SeverityWarn, false},
		{"info severity", SeverityInfo, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := &ToolError{
				Tool:     "test",
				Err:      errors.New("test"),
				Severity: tt.severity,
			}

			got := err.IsFatal()
			if got != tt.want {
				t.Errorf("IsFatal() = %v, want %v", got, tt.want)
			}
		})
	}
}

// TestNewToolError tests the constructor
func TestNewToolError(t *testing.T) {
	err := NewToolError("gosec", errors.New("not found"), SeverityWarn, "go install gosec@latest")

	if err.Tool != "gosec" {
		t.Errorf("Tool = %q, want %q", err.Tool, "gosec")
	}

	if err.Severity != SeverityWarn {
		t.Errorf("Severity = %v, want %v", err.Severity, SeverityWarn)
	}

	if err.InstallGuide != "go install gosec@latest" {
		t.Errorf("InstallGuide = %q, want %q", err.InstallGuide, "go install gosec@latest")
	}
}

// TestSeverity_String tests severity string representation
func TestSeverity_String(t *testing.T) {
	tests := []struct {
		severity Severity
		want     string
	}{
		{SeverityFatal, "FATAL"},
		{SeverityError, "ERROR"},
		{SeverityWarn, "WARN"},
		{SeverityInfo, "INFO"},
	}

	for _, tt := range tests {
		t.Run(tt.want, func(t *testing.T) {
			got := tt.severity.String()
			if got != tt.want {
				t.Errorf("String() = %q, want %q", got, tt.want)
			}
		})
	}
}

// TestSentinelErrors tests that sentinel errors are defined
func TestSentinelErrors(t *testing.T) {
	sentinels := []error{
		ErrToolNotFound,
		ErrInvalidConfig,
		ErrTimeout,
		ErrNetworkFailure,
	}

	for i, sentinel := range sentinels {
		if sentinel == nil {
			t.Errorf("sentinel error %d is nil", i)
		}

		if sentinel.Error() == "" {
			t.Errorf("sentinel error %d has empty message", i)
		}
	}
}

// TestToolError_EdgeCases tests edge cases for 100% coverage
func TestToolError_EdgeCases(t *testing.T) {
	t.Run("nil inner error", func(t *testing.T) {
		err := &ToolError{
			Tool: "test",
			Err:  nil,
		}

		// Should not panic
		msg := err.Error()
		if msg == "" {
			t.Error("Error() should return non-empty string even with nil Err")
		}
	})

	t.Run("zero value struct", func(t *testing.T) {
		var err ToolError

		// Should not panic
		_ = err.Error()
		_ = err.Unwrap()
		_ = err.IsFatal()
	})

	t.Run("empty install guide", func(t *testing.T) {
		err := &ToolError{
			Tool:         "test",
			Err:          errors.New("error"),
			InstallGuide: "",
		}

		// Should handle gracefully
		if err.InstallGuide != "" {
			t.Error("InstallGuide should remain empty")
		}
	})
}

// TestToolError_ErrorChain tests error wrapping chains
func TestToolError_ErrorChain(t *testing.T) {
	rootErr := errors.New("root cause")
	wrappedErr := &ToolError{
		Tool: "inner",
		Err:  rootErr,
	}
	outerErr := &ToolError{
		Tool: "outer",
		Err:  wrappedErr,
	}

	// Test errors.Is traverses the chain
	if !errors.Is(outerErr, rootErr) {
		t.Error("errors.Is() should find root cause in chain")
	}

	// Test errors.As finds first matching type
	var toolErr *ToolError
	if !errors.As(outerErr, &toolErr) {
		t.Fatal("errors.As() should find ToolError in chain")
	}

	if toolErr.Tool != "outer" {
		t.Errorf("errors.As() found wrong error in chain: got %q, want %q", toolErr.Tool, "outer")
	}
}
