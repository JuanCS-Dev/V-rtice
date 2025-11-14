package errors

import (
	"fmt"
	"strings"
)

// ErrorType represents the category of error
type ErrorType string

const (
	// Connection errors
	ErrorTypeConnection ErrorType = "CONNECTION"
	ErrorTypeTimeout    ErrorType = "TIMEOUT"
	ErrorTypeNetwork    ErrorType = "NETWORK"

	// Authentication/Authorization errors
	ErrorTypeAuth        ErrorType = "AUTH"
	ErrorTypePermission  ErrorType = "PERMISSION"
	ErrorTypeCredentials ErrorType = "CREDENTIALS"

	// Validation errors
	ErrorTypeValidation ErrorType = "VALIDATION"
	ErrorTypeNotFound   ErrorType = "NOT_FOUND"
	ErrorTypeConflict   ErrorType = "CONFLICT"

	// Server errors
	ErrorTypeServer   ErrorType = "SERVER"
	ErrorTypeInternal ErrorType = "INTERNAL"
	ErrorTypeUnavailable ErrorType = "UNAVAILABLE"

	// Client errors
	ErrorTypeClient ErrorType = "CLIENT"
	ErrorTypeConfig ErrorType = "CONFIG"
	ErrorTypeInput  ErrorType = "INPUT"

	// Circuit breaker errors
	ErrorTypeCircuitOpen ErrorType = "CIRCUIT_OPEN"
)

// VCLIError represents a structured error with context
type VCLIError struct {
	Type       ErrorType
	Message    string
	Details    string
	Cause      error
	Retryable  bool
	StatusCode int
	Service    string // Which backend service caused the error
}

// Error implements the error interface
func (e *VCLIError) Error() string {
	var parts []string

	// Add service context if available
	if e.Service != "" {
		parts = append(parts, fmt.Sprintf("[%s]", e.Service))
	}

	// Add error type
	parts = append(parts, string(e.Type))

	// Add main message
	parts = append(parts, e.Message)

	// Add details if available
	if e.Details != "" {
		parts = append(parts, fmt.Sprintf("(%s)", e.Details))
	}

	return strings.Join(parts, " ")
}

// Unwrap returns the underlying cause
func (e *VCLIError) Unwrap() error {
	return e.Cause
}

// IsRetryable returns whether this error can be retried
func (e *VCLIError) IsRetryable() bool {
	return e.Retryable
}

// WithCause adds a cause to the error
func (e *VCLIError) WithCause(cause error) *VCLIError {
	e.Cause = cause
	return e
}

// WithDetails adds details to the error
func (e *VCLIError) WithDetails(details string) *VCLIError {
	e.Details = details
	return e
}

// New creates a new VCLIError
func New(errType ErrorType, message string) *VCLIError {
	return &VCLIError{
		Type:      errType,
		Message:   message,
		Retryable: isRetryable(errType),
	}
}

// Wrap wraps an existing error with additional context
func Wrap(err error, errType ErrorType, message string) *VCLIError {
	return &VCLIError{
		Type:      errType,
		Message:   message,
		Cause:     err,
		Retryable: isRetryable(errType),
	}
}

// isRetryable determines if an error type is retryable
func isRetryable(errType ErrorType) bool {
	switch errType {
	case ErrorTypeTimeout, ErrorTypeNetwork, ErrorTypeUnavailable:
		return true
	default:
		return false
	}
}

// Common error constructors

// NewConnectionError creates a connection error
func NewConnectionError(service, message string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeConnection,
		Message:   message,
		Service:   service,
		Retryable: true,
	}
}

// NewTimeoutError creates a timeout error
func NewTimeoutError(service, message string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeTimeout,
		Message:   message,
		Service:   service,
		Retryable: true,
	}
}

// NewAuthError creates an authentication error
func NewAuthError(service, message string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeAuth,
		Message:   message,
		Service:   service,
		Retryable: false,
	}
}

// NewValidationError creates a validation error
func NewValidationError(message string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeValidation,
		Message:   message,
		Retryable: false,
	}
}

// NewNotFoundError creates a not found error
func NewNotFoundError(resource string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeNotFound,
		Message:   fmt.Sprintf("%s not found", resource),
		Retryable: false,
	}
}

// NewServerError creates a server error
func NewServerError(service, message string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeServer,
		Message:   message,
		Service:   service,
		Retryable: false,
	}
}

// NewUnavailableError creates a service unavailable error
func NewUnavailableError(service string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeUnavailable,
		Message:   "service unavailable",
		Service:   service,
		Retryable: true,
	}
}

// NewConfigError creates a configuration error
func NewConfigError(message string) *VCLIError {
	return &VCLIError{
		Type:      ErrorTypeConfig,
		Message:   message,
		Retryable: false,
	}
}

// NewHTTPError creates an HTTP error with status code
func NewHTTPError(statusCode int, body string) *VCLIError {
	return &VCLIError{
		Type:       ErrorTypeServer,
		Message:    fmt.Sprintf("HTTP %d", statusCode),
		Details:    body,
		StatusCode: statusCode,
		Retryable:  statusCode >= 500 || statusCode == 429,
	}
}

// IsRetryable checks if an error can be retried
func IsRetryable(err error) bool {
	if err == nil {
		return false
	}
	if vcliErr, ok := err.(*VCLIError); ok {
		return vcliErr.Retryable
	}
	return false
}
