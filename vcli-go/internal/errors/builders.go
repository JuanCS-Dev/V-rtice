package errors

import "fmt"

// ConnectionErrorBuilder helps build rich connection errors
type ConnectionErrorBuilder struct {
	service   string
	endpoint  string
	operation string
	cause     error
}

// NewConnectionErrorBuilder creates a new connection error builder
func NewConnectionErrorBuilder(service, endpoint string) *ConnectionErrorBuilder {
	return &ConnectionErrorBuilder{
		service:  service,
		endpoint: endpoint,
	}
}

// WithOperation sets the operation that failed
func (b *ConnectionErrorBuilder) WithOperation(operation string) *ConnectionErrorBuilder {
	b.operation = operation
	return b
}

// WithCause sets the underlying cause
func (b *ConnectionErrorBuilder) WithCause(cause error) *ConnectionErrorBuilder {
	b.cause = cause
	return b
}

// Build constructs the final contextual error
func (b *ConnectionErrorBuilder) Build() *ContextualError {
	base := NewConnectionError(b.service, "Failed to connect")
	if b.cause != nil {
		base = base.WithCause(b.cause)
	}

	ctx := ErrorContext{
		Endpoint:    b.endpoint,
		Operation:   b.operation,
		Suggestions: GetSuggestionsFor(ErrorTypeConnection, b.service, b.endpoint),
		HelpCommand: fmt.Sprintf("vcli troubleshoot %s", serviceToCommand(b.service)),
	}

	return NewContextualError(base, ctx)
}

// AuthErrorBuilder helps build rich authentication errors
type AuthErrorBuilder struct {
	service   string
	endpoint  string
	operation string
	cause     error
}

// NewAuthErrorBuilder creates a new auth error builder
func NewAuthErrorBuilder(service, endpoint string) *AuthErrorBuilder {
	return &AuthErrorBuilder{
		service:  service,
		endpoint: endpoint,
	}
}

// WithOperation sets the operation that failed
func (b *AuthErrorBuilder) WithOperation(operation string) *AuthErrorBuilder {
	b.operation = operation
	return b
}

// WithCause sets the underlying cause
func (b *AuthErrorBuilder) WithCause(cause error) *AuthErrorBuilder {
	b.cause = cause
	return b
}

// Build constructs the final contextual error
func (b *AuthErrorBuilder) Build() *ContextualError {
	base := NewAuthError(b.service, "Authentication failed")
	if b.cause != nil {
		base = base.WithCause(b.cause)
	}

	ctx := ErrorContext{
		Endpoint:    b.endpoint,
		Operation:   b.operation,
		Suggestions: GetSuggestionsFor(ErrorTypeAuth, b.service, b.endpoint),
		HelpCommand: fmt.Sprintf("vcli troubleshoot %s", serviceToCommand(b.service)),
	}

	return NewContextualError(base, ctx)
}

// ValidationErrorBuilder helps build rich validation errors
type ValidationErrorBuilder struct {
	field   string
	value   string
	message string
}

// NewValidationErrorBuilder creates a new validation error builder
func NewValidationErrorBuilder() *ValidationErrorBuilder {
	return &ValidationErrorBuilder{}
}

// WithField sets the field that failed validation
func (b *ValidationErrorBuilder) WithField(field string) *ValidationErrorBuilder {
	b.field = field
	return b
}

// WithValue sets the invalid value
func (b *ValidationErrorBuilder) WithValue(value string) *ValidationErrorBuilder {
	b.value = value
	return b
}

// WithMessage sets a custom message
func (b *ValidationErrorBuilder) WithMessage(message string) *ValidationErrorBuilder {
	b.message = message
	return b
}

// Build constructs the final contextual error
func (b *ValidationErrorBuilder) Build() *ContextualError {
	message := b.message
	if message == "" {
		if b.field != "" && b.value != "" {
			message = fmt.Sprintf("Invalid value '%s' for field '%s'", b.value, b.field)
		} else if b.field != "" {
			message = fmt.Sprintf("Validation failed for field '%s'", b.field)
		} else {
			message = "Validation failed"
		}
	}

	base := NewValidationError(message)

	ctx := ErrorContext{
		Suggestions: GetSuggestionsFor(ErrorTypeValidation, "", ""),
		HelpCommand: "vcli examples",
	}

	return NewContextualError(base, ctx)
}

// NotFoundErrorBuilder helps build rich not found errors
type NotFoundErrorBuilder struct {
	resourceType string
	resourceName string
	namespace    string
}

// NewNotFoundErrorBuilder creates a new not found error builder
func NewNotFoundErrorBuilder(resourceType, resourceName string) *NotFoundErrorBuilder {
	return &NotFoundErrorBuilder{
		resourceType: resourceType,
		resourceName: resourceName,
	}
}

// WithNamespace sets the namespace
func (b *NotFoundErrorBuilder) WithNamespace(namespace string) *NotFoundErrorBuilder {
	b.namespace = namespace
	return b
}

// Build constructs the final contextual error
func (b *NotFoundErrorBuilder) Build() *ContextualError {
	resource := fmt.Sprintf("%s/%s", b.resourceType, b.resourceName)
	if b.namespace != "" {
		resource = fmt.Sprintf("%s/%s/%s", b.resourceType, b.namespace, b.resourceName)
	}

	base := NewNotFoundError(resource)

	ctx := ErrorContext{
		Resource:    resource,
		Suggestions: GetSuggestionsFor(ErrorTypeNotFound, "", ""),
	}

	return NewContextualError(base, ctx)
}

// serviceToCommand converts service name to command name
func serviceToCommand(service string) string {
	switch service {
	case "MAXIMUS Governance":
		return "maximus"
	case "Active Immune Core":
		return "immune"
	case "HITL Console":
		return "hitl"
	case "Consciousness":
		return "consciousness"
	default:
		return "system"
	}
}
