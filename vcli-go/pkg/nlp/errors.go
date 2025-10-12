// Package nlp provides natural language processing with Zero Trust security
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
package nlp

import (
	"fmt"
)

// ErrorType categorizes NLP errors
type ErrorType string

const (
	ErrorTypeInvalidInput   ErrorType = "INVALID_INPUT"
	ErrorTypeTokenization   ErrorType = "TOKENIZATION"
	ErrorTypeClassification ErrorType = "CLASSIFICATION"
	ErrorTypeGeneration     ErrorType = "GENERATION"
	ErrorTypeTimeout        ErrorType = "TIMEOUT"
	ErrorTypeLowConfidence  ErrorType = "LOW_CONFIDENCE"
	ErrorTypeAuthentication ErrorType = "AUTHENTICATION"
	ErrorTypeAuthorization  ErrorType = "AUTHORIZATION"
	ErrorTypeRateLimit      ErrorType = "RATE_LIMIT"
)

// ParseError represents an NLP parsing error
type ParseError struct {
	Type       ErrorType
	Message    string
	Cause      error
	Suggestion string
}

func (e *ParseError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("%s: %s (caused by: %v)", e.Type, e.Message, e.Cause)
	}
	return fmt.Sprintf("%s: %s", e.Type, e.Message)
}

func (e *ParseError) Unwrap() error {
	return e.Cause
}

// Common errors
var (
	ErrSessionExpired        = &ParseError{Type: ErrorTypeAuthentication, Message: "Session expired"}
	ErrMFARequired           = &ParseError{Type: ErrorTypeAuthentication, Message: "MFA required"}
	ErrInvalidSignature      = &ParseError{Type: ErrorTypeAuthentication, Message: "Invalid cryptographic signature"}
	ErrNotAuthorized         = &ParseError{Type: ErrorTypeAuthorization, Message: "Not authorized"}
	ErrPermissionDenied      = &ParseError{Type: ErrorTypeAuthorization, Message: "Permission denied"}
	ErrRateLimitExceeded     = &ParseError{Type: ErrorTypeRateLimit, Message: "Rate limit exceeded"}
	ErrActionQuotaExceeded   = &ParseError{Type: ErrorTypeRateLimit, Message: "Action quota exceeded"}
	ErrCriticalQuotaExceeded = &ParseError{Type: ErrorTypeRateLimit, Message: "Critical action quota exceeded"}
	ErrUserCancelled         = &ParseError{Type: ErrorTypeLowConfidence, Message: "User cancelled action"}
	ErrChainBroken           = &ParseError{Type: ErrorTypeGeneration, Message: "Audit chain integrity broken"}
)
