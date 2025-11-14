// Package tools provides a centralized registry for tool availability checking
// Following Boris Cherny principles: "Centralize tool management for consistency"
package tools

import (
	"fmt"
	"strings"

	"github.com/verticedev/vcli-go/internal/errors"
)

// CheckResult contains the result of a tool availability check
type CheckResult struct {
	Tool      string
	Available bool
	Error     error
}

// Registry provides centralized tool management and pre-flight validation
type Registry struct {
	checker *Checker
}

// DefaultRegistry is the global tool registry instance
// Initialize with RegisterCore() and RegisterOptional() before use
var DefaultRegistry = NewRegistry()

// NewRegistry creates a new Registry instance
func NewRegistry() *Registry {
	return &Registry{
		checker: NewChecker(),
	}
}

// RegisterCore registers all core required tools
// Core tools are essential for vcli-go to function
func (r *Registry) RegisterCore() {
	// Kubernetes tools
	_ = r.checker.Register(
		"kubectl",
		true,
		errors.SeverityFatal,
		"Install kubectl:\n  curl -LO \"https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\"\n  chmod +x kubectl\n  sudo mv kubectl /usr/local/bin/",
	)

	// Python tools
	_ = r.checker.Register(
		"python3",
		true,
		errors.SeverityFatal,
		"Install Python 3:\n  Ubuntu/Debian: sudo apt-get install python3\n  RHEL/CentOS: sudo yum install python3\n  macOS: brew install python3",
	)

	_ = r.checker.Register(
		"pip3",
		true,
		errors.SeverityFatal,
		"Install pip3:\n  Ubuntu/Debian: sudo apt-get install python3-pip\n  RHEL/CentOS: sudo yum install python3-pip\n  macOS: brew install python3 (includes pip)",
	)

	// Go tools
	_ = r.checker.Register(
		"go",
		true,
		errors.SeverityFatal,
		"Install Go:\n  Download from https://go.dev/dl/\n  Or use version manager: https://github.com/moovweb/gvm",
	)

	// Git for version control operations
	_ = r.checker.Register(
		"git",
		true,
		errors.SeverityFatal,
		"Install Git:\n  Ubuntu/Debian: sudo apt-get install git\n  RHEL/CentOS: sudo yum install git\n  macOS: brew install git",
	)
}

// RegisterOptional registers optional tools that enhance functionality
// Optional tools provide additional features but are not required
func (r *Registry) RegisterOptional() {
	// Go security and quality tools
	_ = r.checker.Register(
		"gosec",
		false,
		errors.SeverityWarn,
		"Install gosec (Go security checker):\n  go install github.com/securego/gosec/v2/cmd/gosec@latest",
	)

	_ = r.checker.Register(
		"golangci-lint",
		false,
		errors.SeverityWarn,
		"Install golangci-lint:\n  curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin",
	)

	_ = r.checker.Register(
		"staticcheck",
		false,
		errors.SeverityWarn,
		"Install staticcheck:\n  go install honnef.co/go/tools/cmd/staticcheck@latest",
	)

	// Python code quality tools
	_ = r.checker.Register(
		"black",
		false,
		errors.SeverityWarn,
		"Install black (Python formatter):\n  pip3 install black",
	)

	_ = r.checker.Register(
		"autopep8",
		false,
		errors.SeverityWarn,
		"Install autopep8 (Python formatter):\n  pip3 install autopep8",
	)

	_ = r.checker.Register(
		"pylint",
		false,
		errors.SeverityWarn,
		"Install pylint (Python linter):\n  pip3 install pylint",
	)

	// Testing tools
	_ = r.checker.Register(
		"pytest",
		false,
		errors.SeverityWarn,
		"Install pytest:\n  pip3 install pytest",
	)

	// Container tools
	_ = r.checker.Register(
		"docker",
		false,
		errors.SeverityInfo,
		"Install Docker:\n  Follow instructions at https://docs.docker.com/get-docker/",
	)

	_ = r.checker.Register(
		"helm",
		false,
		errors.SeverityInfo,
		"Install Helm:\n  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
	)
}

// Check verifies if a specific tool is available
func (r *Registry) Check(toolName string) (bool, error) {
	return r.checker.Check(toolName)
}

// CheckAll checks all registered tools and returns results
func (r *Registry) CheckAll() map[string]CheckResult {
	results := make(map[string]CheckResult)

	r.checker.mu.RLock()
	tools := make(map[string]*Tool)
	for name, tool := range r.checker.tools {
		tools[name] = tool
	}
	r.checker.mu.RUnlock()

	for toolName := range tools {
		available, err := r.Check(toolName)

		results[toolName] = CheckResult{
			Tool:      toolName,
			Available: available,
			Error:     err,
		}
	}

	return results
}

// CheckPreFlight performs pre-flight validation of required tools
// Returns errors only for required tools
func (r *Registry) CheckPreFlight() []error {
	var errs []error

	r.checker.mu.RLock()
	tools := make(map[string]*Tool)
	for name, tool := range r.checker.tools {
		if tool.Required {
			tools[name] = tool
		}
	}
	r.checker.mu.RUnlock()

	for toolName := range tools {
		if _, err := r.Check(toolName); err != nil {
			errs = append(errs, err)
		}
	}

	return errs
}

// GetMissingRequired returns list of missing required tools
// Only includes tools that have been checked and are required
func (r *Registry) GetMissingRequired() []string {
	var missing []string

	r.checker.mu.RLock()
	defer r.checker.mu.RUnlock()

	for toolName, available := range r.checker.cache {
		if !available {
			if tool, exists := r.checker.tools[toolName]; exists && tool.Required {
				missing = append(missing, toolName)
			}
		}
	}

	return missing
}

// FormatMissingTools creates a user-friendly error message for missing tools
func (r *Registry) FormatMissingTools() string {
	missing := r.checker.GetMissing()
	if len(missing) == 0 {
		return ""
	}

	var builder strings.Builder

	builder.WriteString("Missing tools detected:\n\n")

	r.checker.mu.RLock()
	defer r.checker.mu.RUnlock()

	for _, toolName := range missing {
		tool, exists := r.checker.tools[toolName]
		if !exists {
			continue
		}

		severity := "REQUIRED"
		if !tool.Required {
			severity = "OPTIONAL"
		}

		builder.WriteString(fmt.Sprintf("  [%s] %s\n", severity, tool.Name))

		if tool.InstallCmd != "" {
			// Indent install instructions
			lines := strings.Split(tool.InstallCmd, "\n")
			for _, line := range lines {
				builder.WriteString(fmt.Sprintf("    %s\n", line))
			}
		}

		builder.WriteString("\n")
	}

	return builder.String()
}

// IsAvailable is a convenience method that returns only availability status
func (r *Registry) IsAvailable(toolName string) bool {
	return r.checker.IsAvailable(toolName)
}

// ResetCache clears the availability cache
// Useful when tools may have been installed during runtime
func (r *Registry) ResetCache() {
	r.checker.ClearCache()
}

// init registers core and optional tools in the default registry
func init() {
	DefaultRegistry.RegisterCore()
	DefaultRegistry.RegisterOptional()
}
