package errors

import (
	"errors"
	"strings"
	"testing"
)

// TestNewConnectionErrorBuilder tests the connection error builder constructor
func TestNewConnectionErrorBuilder(t *testing.T) {
	builder := NewConnectionErrorBuilder("maximus", "http://localhost:8080")

	if builder.service != "maximus" {
		t.Errorf("service = %q, want %q", builder.service, "maximus")
	}
	if builder.endpoint != "http://localhost:8080" {
		t.Errorf("endpoint = %q, want %q", builder.endpoint, "http://localhost:8080")
	}
}

// TestConnectionErrorBuilder_WithOperation tests setting operation
func TestConnectionErrorBuilder_WithOperation(t *testing.T) {
	builder := NewConnectionErrorBuilder("atlas", "http://atlas:9000").
		WithOperation("GetDecision")

	if builder.operation != "GetDecision" {
		t.Errorf("operation = %q, want %q", builder.operation, "GetDecision")
	}
}

// TestConnectionErrorBuilder_WithCause tests setting cause
func TestConnectionErrorBuilder_WithCause(t *testing.T) {
	cause := errors.New("connection refused")
	builder := NewConnectionErrorBuilder("maba", "http://maba:8000").
		WithCause(cause)

	if builder.cause != cause {
		t.Error("cause not set correctly")
	}
}

// TestConnectionErrorBuilder_Build tests building the final error
func TestConnectionErrorBuilder_Build(t *testing.T) {
	cause := errors.New("dial tcp: connection refused")
	err := NewConnectionErrorBuilder("maximus", "http://localhost:8080").
		WithOperation("CreateWorkflow").
		WithCause(cause).
		Build()

	if err == nil {
		t.Fatal("Build() returned nil")
	}

	if err.VCLIError.Type != ErrorTypeConnection {
		t.Errorf("Type = %v, want %v", err.VCLIError.Type, ErrorTypeConnection)
	}

	if err.Context.Endpoint != "http://localhost:8080" {
		t.Errorf("Endpoint = %q, want %q", err.Context.Endpoint, "http://localhost:8080")
	}

	if err.Context.Operation != "CreateWorkflow" {
		t.Errorf("Operation = %q, want %q", err.Context.Operation, "CreateWorkflow")
	}

	if !strings.Contains(err.Context.HelpCommand, "troubleshoot") {
		t.Errorf("HelpCommand = %q, should contain 'troubleshoot'", err.Context.HelpCommand)
	}

	// Test unwrapping
	if !errors.Is(err.VCLIError, cause) {
		t.Error("Should be able to unwrap to cause")
	}
}

// TestConnectionErrorBuilder_BuildWithoutCause tests building without cause
func TestConnectionErrorBuilder_BuildWithoutCause(t *testing.T) {
	err := NewConnectionErrorBuilder("penelope", "http://penelope:8080").
		WithOperation("FetchData").
		Build()

	if err == nil {
		t.Fatal("Build() returned nil")
	}

	if err.VCLIError.Cause != nil {
		t.Error("Cause should be nil when not set")
	}
}

// TestConnectionErrorBuilder_MethodChaining tests fluent API
func TestConnectionErrorBuilder_MethodChaining(t *testing.T) {
	cause := errors.New("timeout")
	err := NewConnectionErrorBuilder("nis", "http://nis:7000").
		WithOperation("Analyze").
		WithCause(cause).
		Build()

	if err.Context.Operation != "Analyze" {
		t.Error("Method chaining: operation not set")
	}
	if !errors.Is(err.VCLIError, cause) {
		t.Error("Method chaining: cause not set")
	}
}

// TestNewAuthErrorBuilder tests the auth error builder constructor
func TestNewAuthErrorBuilder(t *testing.T) {
	builder := NewAuthErrorBuilder("hitl", "http://hitl:8000")

	if builder.service != "hitl" {
		t.Errorf("service = %q, want %q", builder.service, "hitl")
	}
	if builder.endpoint != "http://hitl:8000" {
		t.Errorf("endpoint = %q, want %q", builder.endpoint, "http://hitl:8000")
	}
}

// TestAuthErrorBuilder_WithOperation tests setting operation
func TestAuthErrorBuilder_WithOperation(t *testing.T) {
	builder := NewAuthErrorBuilder("maximus", "http://maximus:8080").
		WithOperation("Login")

	if builder.operation != "Login" {
		t.Errorf("operation = %q, want %q", builder.operation, "Login")
	}
}

// TestAuthErrorBuilder_WithCause tests setting cause
func TestAuthErrorBuilder_WithCause(t *testing.T) {
	cause := errors.New("invalid token")
	builder := NewAuthErrorBuilder("atlas", "http://atlas:9000").
		WithCause(cause)

	if builder.cause != cause {
		t.Error("cause not set correctly")
	}
}

// TestAuthErrorBuilder_Build tests building the final error
func TestAuthErrorBuilder_Build(t *testing.T) {
	cause := errors.New("401 Unauthorized")
	err := NewAuthErrorBuilder("HITL Console", "http://localhost:8000").
		WithOperation("Login").
		WithCause(cause).
		Build()

	if err == nil {
		t.Fatal("Build() returned nil")
	}

	if err.VCLIError.Type != ErrorTypeAuth {
		t.Errorf("Type = %v, want %v", err.VCLIError.Type, ErrorTypeAuth)
	}

	if err.Context.Endpoint != "http://localhost:8000" {
		t.Errorf("Endpoint = %q, want %q", err.Context.Endpoint, "http://localhost:8000")
	}

	if err.Context.Operation != "Login" {
		t.Errorf("Operation = %q, want %q", err.Context.Operation, "Login")
	}

	if !strings.Contains(err.Context.HelpCommand, "hitl") {
		t.Errorf("HelpCommand = %q, should contain 'hitl'", err.Context.HelpCommand)
	}

	// Test unwrapping
	if !errors.Is(err.VCLIError, cause) {
		t.Error("Should be able to unwrap to cause")
	}
}

// TestAuthErrorBuilder_BuildWithoutCause tests building without cause
func TestAuthErrorBuilder_BuildWithoutCause(t *testing.T) {
	err := NewAuthErrorBuilder("maba", "http://maba:8000").
		WithOperation("ValidateToken").
		Build()

	if err == nil {
		t.Fatal("Build() returned nil")
	}

	if err.VCLIError.Cause != nil {
		t.Error("Cause should be nil when not set")
	}
}

// TestNewValidationErrorBuilder tests the validation error builder constructor
func TestNewValidationErrorBuilder(t *testing.T) {
	builder := NewValidationErrorBuilder()

	if builder == nil {
		t.Fatal("NewValidationErrorBuilder() returned nil")
	}
}

// TestValidationErrorBuilder_WithField tests setting field
func TestValidationErrorBuilder_WithField(t *testing.T) {
	builder := NewValidationErrorBuilder().WithField("username")

	if builder.field != "username" {
		t.Errorf("field = %q, want %q", builder.field, "username")
	}
}

// TestValidationErrorBuilder_WithValue tests setting value
func TestValidationErrorBuilder_WithValue(t *testing.T) {
	builder := NewValidationErrorBuilder().WithValue("invalid@")

	if builder.value != "invalid@" {
		t.Errorf("value = %q, want %q", builder.value, "invalid@")
	}
}

// TestValidationErrorBuilder_WithMessage tests setting message
func TestValidationErrorBuilder_WithMessage(t *testing.T) {
	builder := NewValidationErrorBuilder().WithMessage("custom error")

	if builder.message != "custom error" {
		t.Errorf("message = %q, want %q", builder.message, "custom error")
	}
}

// TestValidationErrorBuilder_Build tests building validation errors
func TestValidationErrorBuilder_Build(t *testing.T) {
	tests := []struct {
		name    string
		builder *ValidationErrorBuilder
		wantMsg string
	}{
		{
			name:    "with field and value",
			builder: NewValidationErrorBuilder().WithField("email").WithValue("notanemail"),
			wantMsg: "Invalid value 'notanemail' for field 'email'",
		},
		{
			name:    "with field only",
			builder: NewValidationErrorBuilder().WithField("password"),
			wantMsg: "Validation failed for field 'password'",
		},
		{
			name:    "with custom message",
			builder: NewValidationErrorBuilder().WithMessage("Custom validation error"),
			wantMsg: "Custom validation error",
		},
		{
			name:    "empty builder",
			builder: NewValidationErrorBuilder(),
			wantMsg: "Validation failed",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.builder.Build()

			if err == nil {
				t.Fatal("Build() returned nil")
			}

			if err.VCLIError.Type != ErrorTypeValidation {
				t.Errorf("Type = %v, want %v", err.VCLIError.Type, ErrorTypeValidation)
			}

			if err.VCLIError.Message != tt.wantMsg {
				t.Errorf("Message = %q, want %q", err.VCLIError.Message, tt.wantMsg)
			}

			if !strings.Contains(err.Context.HelpCommand, "examples") {
				t.Errorf("HelpCommand = %q, should contain 'examples'", err.Context.HelpCommand)
			}
		})
	}
}

// TestValidationErrorBuilder_MethodChaining tests fluent API
func TestValidationErrorBuilder_MethodChaining(t *testing.T) {
	err := NewValidationErrorBuilder().
		WithField("port").
		WithValue("99999").
		Build()

	if !strings.Contains(err.VCLIError.Message, "port") {
		t.Error("Method chaining: field not set")
	}
	if !strings.Contains(err.VCLIError.Message, "99999") {
		t.Error("Method chaining: value not set")
	}
}

// TestNewNotFoundErrorBuilder tests the not found error builder constructor
func TestNewNotFoundErrorBuilder(t *testing.T) {
	builder := NewNotFoundErrorBuilder("pod", "nginx")

	if builder.resourceType != "pod" {
		t.Errorf("resourceType = %q, want %q", builder.resourceType, "pod")
	}
	if builder.resourceName != "nginx" {
		t.Errorf("resourceName = %q, want %q", builder.resourceName, "nginx")
	}
}

// TestNotFoundErrorBuilder_WithNamespace tests setting namespace
func TestNotFoundErrorBuilder_WithNamespace(t *testing.T) {
	builder := NewNotFoundErrorBuilder("deployment", "app").
		WithNamespace("production")

	if builder.namespace != "production" {
		t.Errorf("namespace = %q, want %q", builder.namespace, "production")
	}
}

// TestNotFoundErrorBuilder_Build tests building the final error
func TestNotFoundErrorBuilder_Build(t *testing.T) {
	tests := []struct {
		name           string
		resourceType   string
		resourceName   string
		namespace      string
		wantResource   string
		wantInMessage  []string
	}{
		{
			name:          "without namespace",
			resourceType:  "service",
			resourceName:  "api",
			namespace:     "",
			wantResource:  "service/api",
			wantInMessage: []string{"service/api", "not found"},
		},
		{
			name:          "with namespace",
			resourceType:  "pod",
			resourceName:  "nginx",
			namespace:     "kube-system",
			wantResource:  "pod/kube-system/nginx",
			wantInMessage: []string{"pod/kube-system/nginx", "not found"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			builder := NewNotFoundErrorBuilder(tt.resourceType, tt.resourceName)
			if tt.namespace != "" {
				builder = builder.WithNamespace(tt.namespace)
			}

			err := builder.Build()

			if err == nil {
				t.Fatal("Build() returned nil")
			}

			if err.VCLIError.Type != ErrorTypeNotFound {
				t.Errorf("Type = %v, want %v", err.VCLIError.Type, ErrorTypeNotFound)
			}

			if err.Context.Resource != tt.wantResource {
				t.Errorf("Resource = %q, want %q", err.Context.Resource, tt.wantResource)
			}

			for _, want := range tt.wantInMessage {
				if !strings.Contains(err.VCLIError.Message, want) {
					t.Errorf("Message = %q, want to contain %q", err.VCLIError.Message, want)
				}
			}
		})
	}
}

// TestNotFoundErrorBuilder_MethodChaining tests fluent API
func TestNotFoundErrorBuilder_MethodChaining(t *testing.T) {
	err := NewNotFoundErrorBuilder("configmap", "settings").
		WithNamespace("default").
		Build()

	if !strings.Contains(err.Context.Resource, "configmap") {
		t.Error("Method chaining: resource type not set")
	}
	if !strings.Contains(err.Context.Resource, "settings") {
		t.Error("Method chaining: resource name not set")
	}
	if !strings.Contains(err.Context.Resource, "default") {
		t.Error("Method chaining: namespace not set")
	}
}

// TestServiceToCommand tests the service name to command mapping
func TestServiceToCommand(t *testing.T) {
	tests := []struct {
		service string
		want    string
	}{
		{"MAXIMUS Governance", "maximus"},
		{"Active Immune Core", "immune"},
		{"HITL Console", "hitl"},
		{"Consciousness", "consciousness"},
		{"Unknown Service", "system"},
		{"", "system"},
	}

	for _, tt := range tests {
		t.Run(tt.service, func(t *testing.T) {
			got := serviceToCommand(tt.service)
			if got != tt.want {
				t.Errorf("serviceToCommand(%q) = %q, want %q", tt.service, got, tt.want)
			}
		})
	}
}

// TestBuilders_Integration tests all builders working together
func TestBuilders_Integration(t *testing.T) {
	// Connection error
	connErr := NewConnectionErrorBuilder("maximus", "http://localhost:8080").
		WithOperation("HealthCheck").
		WithCause(errors.New("connection refused")).
		Build()

	if connErr.VCLIError.Type != ErrorTypeConnection {
		t.Error("Connection builder produced wrong error type")
	}

	// Auth error
	authErr := NewAuthErrorBuilder("hitl", "http://localhost:8000").
		WithOperation("Login").
		Build()

	if authErr.VCLIError.Type != ErrorTypeAuth {
		t.Error("Auth builder produced wrong error type")
	}

	// Validation error
	valErr := NewValidationErrorBuilder().
		WithField("email").
		WithValue("invalid").
		Build()

	if valErr.VCLIError.Type != ErrorTypeValidation {
		t.Error("Validation builder produced wrong error type")
	}

	// Not found error
	notFoundErr := NewNotFoundErrorBuilder("pod", "nginx").
		WithNamespace("default").
		Build()

	if notFoundErr.VCLIError.Type != ErrorTypeNotFound {
		t.Error("NotFound builder produced wrong error type")
	}
}
