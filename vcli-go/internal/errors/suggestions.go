package errors

import (
	"fmt"
	"strings"
)

// Suggestion represents a recovery suggestion
type Suggestion struct {
	Description string
	Command     string // Optional command to run
}

// ErrorContext contains additional context about an error
type ErrorContext struct {
	Endpoint    string
	Operation   string
	Resource    string
	Suggestions []Suggestion
	HelpCommand string // Command to get more help
}

// ContextualError extends VCLIError with context and suggestions
type ContextualError struct {
	*VCLIError
	Context ErrorContext
}

// Error implements the error interface with rich formatting
func (e *ContextualError) Error() string {
	return e.VCLIError.Error()
}

// Format returns a formatted, user-friendly error message with suggestions
func (e *ContextualError) Format() string {
	var b strings.Builder

	// Header
	b.WriteString(fmt.Sprintf("❌ %s Error", e.Type))
	if e.Service != "" {
		b.WriteString(fmt.Sprintf(": %s", e.Service))
	}
	b.WriteString("\n\n")

	// Main message
	b.WriteString(e.Message)
	b.WriteString("\n")

	// Context details
	if e.Context.Endpoint != "" {
		b.WriteString(fmt.Sprintf("Endpoint: %s\n", e.Context.Endpoint))
	}
	if e.Context.Operation != "" {
		b.WriteString(fmt.Sprintf("Operation: %s\n", e.Context.Operation))
	}
	if e.Context.Resource != "" {
		b.WriteString(fmt.Sprintf("Resource: %s\n", e.Context.Resource))
	}

	// Cause (if available)
	if e.Cause != nil {
		b.WriteString(fmt.Sprintf("Cause: %v\n", e.Cause))
	}

	// Suggestions
	if len(e.Context.Suggestions) > 0 {
		b.WriteString("\n💡 Suggestions:\n")
		for i, suggestion := range e.Context.Suggestions {
			b.WriteString(fmt.Sprintf("  %d. %s\n", i+1, suggestion.Description))
			if suggestion.Command != "" {
				b.WriteString(fmt.Sprintf("     $ %s\n", suggestion.Command))
			}
		}
	}

	// Help command
	if e.Context.HelpCommand != "" {
		b.WriteString(fmt.Sprintf("\nNeed help? Run: %s\n", e.Context.HelpCommand))
	}

	return b.String()
}

// NewContextualError creates a contextual error with suggestions
func NewContextualError(base *VCLIError, ctx ErrorContext) *ContextualError {
	return &ContextualError{
		VCLIError: base,
		Context:   ctx,
	}
}

// GetSuggestionsFor returns common suggestions for an error type
func GetSuggestionsFor(errType ErrorType, service, endpoint string) []Suggestion {
	switch errType {
	case ErrorTypeConnection:
		return connectionSuggestions(service, endpoint)
	case ErrorTypeTimeout:
		return timeoutSuggestions(service)
	case ErrorTypeAuth:
		return authSuggestions(service)
	case ErrorTypeValidation:
		return validationSuggestions()
	case ErrorTypeNotFound:
		return notFoundSuggestions()
	case ErrorTypeUnavailable:
		return unavailableSuggestions(service)
	default:
		return []Suggestion{}
	}
}

func connectionSuggestions(service, endpoint string) []Suggestion {
	suggestions := []Suggestion{
		{
			Description: fmt.Sprintf("Verify %s service is running", service),
			Command:     fmt.Sprintf("systemctl status %s", strings.ToLower(strings.ReplaceAll(service, " ", "-"))),
		},
		{
			Description: "Check endpoint configuration",
			Command:     "vcli configure show",
		},
	}

	if endpoint != "" {
		suggestions = append(suggestions, Suggestion{
			Description: "Test connectivity",
			Command:     fmt.Sprintf("curl %s/health", endpoint),
		})
	}

	suggestions = append(suggestions, Suggestion{
		Description: "Check network connectivity and firewall rules",
	})

	return suggestions
}

func timeoutSuggestions(service string) []Suggestion {
	return []Suggestion{
		{
			Description: fmt.Sprintf("Verify %s service is responsive", service),
		},
		{
			Description: "Check service logs for performance issues",
			Command:     fmt.Sprintf("journalctl -u %s -n 50", strings.ToLower(strings.ReplaceAll(service, " ", "-"))),
		},
		{
			Description: "Increase timeout if operation is expected to take longer",
			Command:     "vcli <command> --timeout=60s",
		},
		{
			Description: "Check network latency",
			Command:     "ping <service-host>",
		},
	}
}

func authSuggestions(service string) []Suggestion {
	suggestions := []Suggestion{
		{
			Description: "Verify your credentials are correct",
		},
	}

	if service == "HITL Console" {
		suggestions = append(suggestions, Suggestion{
			Description: "Login again to refresh token",
			Command:     "vcli hitl login --username <your-username>",
		})
	}

	suggestions = append(suggestions, Suggestion{
		Description: "Check if your account has required permissions",
	})

	return suggestions
}

func validationSuggestions() []Suggestion {
	return []Suggestion{
		{
			Description: "Check command syntax and required flags",
			Command:     "vcli <command> --help",
		},
		{
			Description: "Verify input data format and values",
		},
		{
			Description: "Review command examples",
			Command:     "vcli examples",
		},
	}
}

func notFoundSuggestions() []Suggestion {
	return []Suggestion{
		{
			Description: "Verify resource name and namespace are correct",
		},
		{
			Description: "List available resources",
			Command:     "vcli <resource-type> list",
		},
		{
			Description: "Check if resource was deleted or moved",
		},
	}
}

func unavailableSuggestions(service string) []Suggestion {
	return []Suggestion{
		{
			Description: fmt.Sprintf("Verify %s service is running and healthy", service),
			Command:     fmt.Sprintf("systemctl status %s", strings.ToLower(strings.ReplaceAll(service, " ", "-"))),
		},
		{
			Description: "Check service health endpoint",
			Command:     "vcli <service> health",
		},
		{
			Description: "Wait a moment and retry (service may be restarting)",
		},
		{
			Description: "Check service logs for errors",
			Command:     fmt.Sprintf("journalctl -u %s -n 100", strings.ToLower(strings.ReplaceAll(service, " ", "-"))),
		},
	}
}
