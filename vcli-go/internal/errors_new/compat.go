package errors

// Compatibility layer for old error API (temporary)

// NewConnectionErrorBuilder creates a connection error (legacy compat)
func NewConnectionErrorBuilder() *Error {
	return New(ErrorTypeNetwork, "connection failed")
}

// NewAuthError creates an auth error (legacy compat)
func NewAuthError(message string) *Error {
	return New(ErrorTypeConfig, message)
}

// NewServerError creates a server error (legacy compat)
func NewServerError(message string) *Error {
	return New(ErrorTypeHTTP, message)
}

// NewContextualError creates a contextual error (legacy compat)
func NewContextualError(baseErr error, context ErrorContext) *Error {
	return Wrap(baseErr, ErrorTypeInternal, "contextual error")
}

// ErrorContext provides error context (legacy compat)
type ErrorContext struct {
	Operation   string
	Suggestions []string
}

// GetSuggestionsFor returns suggestions for error type (legacy compat)
func GetSuggestionsFor(errType ErrorType) []string {
	switch errType {
	case ErrorTypeNetwork:
		return []string{"Check your internet connection", "Verify endpoint configuration"}
	case ErrorTypeConfig:
		return []string{"Check configuration file", "Verify environment variables"}
	case ErrorTypeHTTP:
		return []string{"Check server status", "Verify API endpoint"}
	default:
		return []string{"Check logs for more details"}
	}
}

// ErrorTypeAuth legacy constant
const ErrorTypeAuth = ErrorTypeConfig
