// Package errors provides custom error types for vcli-go
// Following Boris Cherny principles: "Errors should be impossible to ignore"
package errors

import (
	"errors"
	"fmt"
)

// Sentinel errors for common conditions
var (
	// ErrToolNotFound indicates a required external tool is not in PATH
	ErrToolNotFound = errors.New("tool not found in PATH")

	// ErrInvalidConfig indicates configuration is malformed
	ErrInvalidConfig = errors.New("invalid configuration")

	// ErrTimeout indicates an operation exceeded its deadline
	ErrTimeout = errors.New("operation timed out")

	// ErrNetworkFailure indicates a network connection failed
	ErrNetworkFailure = errors.New("network connection failed")
)

// Severity classifies error impact
type Severity int

const (
	// SeverityFatal indicates tool is required, must abort
	SeverityFatal Severity = iota

	// SeverityError indicates operation failed but system can continue
	SeverityError

	// SeverityWarn indicates problem detected but fully functional
	SeverityWarn

	// SeverityInfo indicates informational message only
	SeverityInfo
)

// String returns human-readable severity level
func (s Severity) String() string {
	switch s {
	case SeverityFatal:
		return "FATAL"
	case SeverityError:
		return "ERROR"
	case SeverityWarn:
		return "WARN"
	case SeverityInfo:
		return "INFO"
	default:
		return "UNKNOWN"
	}
}

// ToolError represents a tool-related error with context
type ToolError struct {
	// Tool is the name of the tool that failed
	Tool string

	// Err is the underlying error
	Err error

	// Severity indicates how critical this error is
	Severity Severity

	// InstallGuide provides instructions for installing the tool
	InstallGuide string
}

// Error implements the error interface
func (e *ToolError) Error() string {
	if e.Tool == "" {
		if e.Err != nil {
			return e.Err.Error()
		}
		return "unknown tool error"
	}

	if e.Err != nil {
		return fmt.Sprintf("%s: %v", e.Tool, e.Err)
	}

	return fmt.Sprintf("%s: error", e.Tool)
}

// Unwrap returns the underlying error for error chain traversal
func (e *ToolError) Unwrap() error {
	return e.Err
}

// IsFatal returns true if this error should abort the operation
func (e *ToolError) IsFatal() bool {
	return e.Severity == SeverityFatal
}

// NewToolError creates a new ToolError with all fields
func NewToolError(tool string, err error, severity Severity, installGuide string) *ToolError {
	return &ToolError{
		Tool:         tool,
		Err:          err,
		Severity:     severity,
		InstallGuide: installGuide,
	}
}
