package errors

import (
	"fmt"
	"net/http"
)

// ErrorType represents the category of error
type ErrorType string

const (
	// Network errors (transient, retryable)
	ErrorTypeNetwork ErrorType = "network"
	ErrorTypeTimeout ErrorType = "timeout"

	// HTTP errors (non-2xx responses)
	ErrorTypeHTTP ErrorType = "http"

	// API errors (business logic failures)
	ErrorTypeAPI ErrorType = "api"

	// Configuration errors (setup issues)
	ErrorTypeConfig ErrorType = "config"

	// Circuit breaker errors (protective)
	ErrorTypeCircuitOpen ErrorType = "circuit_open"

	// Validation errors (input issues)
	ErrorTypeValidation ErrorType = "validation"

	// Internal errors (unexpected)
	ErrorTypeInternal ErrorType = "internal"
)

// Error is the base error type for all vcli errors
type Error struct {
	Type    ErrorType
	Message string
	Cause   error
	Details map[string]interface{}
}

func (e *Error) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("%s: %s (caused by: %v)", e.Type, e.Message, e.Cause)
	}
	return fmt.Sprintf("%s: %s", e.Type, e.Message)
}

func (e *Error) Unwrap() error {
	return e.Cause
}

// New creates a new error
func New(errType ErrorType, message string) *Error {
	return &Error{
		Type:    errType,
		Message: message,
		Details: make(map[string]interface{}),
	}
}

// Wrap wraps an error with additional context
func Wrap(err error, errType ErrorType, message string) *Error {
	return &Error{
		Type:    errType,
		Message: message,
		Cause:   err,
		Details: make(map[string]interface{}),
	}
}

// WithDetails adds details to an error
func (e *Error) WithDetails(key string, value interface{}) *Error {
	e.Details[key] = value
	return e
}

// HTTPError represents an HTTP-level error
type HTTPError struct {
	Err        *Error
	StatusCode int
	Body       string
}

func (h *HTTPError) Error() string {
	return h.Err.Error()
}

func (h *HTTPError) Unwrap() error {
	return h.Err
}

func NewHTTPError(statusCode int, body string) *HTTPError {
	return &HTTPError{
		Err: &Error{
			Type:    ErrorTypeHTTP,
			Message: fmt.Sprintf("HTTP %d: %s", statusCode, http.StatusText(statusCode)),
			Details: make(map[string]interface{}),
		},
		StatusCode: statusCode,
		Body:       body,
	}
}

// APIError represents an API-level error (business logic)
type APIError struct {
	Err        *Error
	Code       string
	APIDetails map[string]interface{}
}

func (a *APIError) Error() string {
	return a.Err.Error()
}

func (a *APIError) Unwrap() error {
	return a.Err
}

func NewAPIError(code, message string) *APIError {
	return &APIError{
		Err: &Error{
			Type:    ErrorTypeAPI,
			Message: message,
			Details: make(map[string]interface{}),
		},
		Code:       code,
		APIDetails: make(map[string]interface{}),
	}
}

// IsRetryable determines if an error is retryable
func IsRetryable(err error) bool {
	if err == nil {
		return false
	}

	// Check if it's our error type
	if e, ok := err.(*Error); ok {
		switch e.Type {
		case ErrorTypeNetwork, ErrorTypeTimeout:
			return true
		case ErrorTypeHTTP:
			// Retry 5xx and 429 (rate limit)
			if httpErr, ok := err.(*HTTPError); ok {
				return httpErr.StatusCode >= 500 || httpErr.StatusCode == 429
			}
		}
	}

	return false
}

// IsCircuitBreakerError checks if error is from circuit breaker
func IsCircuitBreakerError(err error) bool {
	if e, ok := err.(*Error); ok {
		return e.Type == ErrorTypeCircuitOpen
	}
	return false
}
