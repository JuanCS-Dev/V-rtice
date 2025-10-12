// Package sandbox implements Layer 3 (Sandboxing) of Guardian Zero Trust Security.
//
// "Where can you operate?" - Controlling the scope and boundaries of operations.
//
// Provides:
// - Namespace isolation
// - Resource quotas and limits
// - Path validation (whitelist/blacklist)
// - Safe execution context
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)
// Date: 2025-10-12
package sandbox

import (
	"errors"
	"fmt"
	"path/filepath"
	"strings"
	"time"
)

// Sandbox provides isolated execution environment.
type Sandbox struct {
	config          *SandboxConfig
	resourceLimiter *ResourceLimiter
	pathValidator   *PathValidator
}

// SandboxConfig configures sandbox behavior.
type SandboxConfig struct {
	// Namespace restrictions
	AllowedNamespaces   []string // Whitelisted namespaces
	ForbiddenNamespaces []string // Blacklisted namespaces (takes precedence)
	DefaultNamespace    string   // Default if none specified

	// Path restrictions
	AllowedPaths   []string // Whitelisted paths
	ForbiddenPaths []string // Blacklisted paths

	// Resource limits
	MaxCPU     string        // e.g., "100m" (millicores)
	MaxMemory  string        // e.g., "128Mi"
	MaxStorage string        // e.g., "1Gi"
	Timeout    time.Duration // Max execution time

	// Isolation settings
	NetworkIsolation bool // Restrict network access
	ReadOnly         bool // Enforce read-only filesystem
	DropCapabilities bool // Drop Linux capabilities
}

// ExecutionContext defines the context for command execution.
type ExecutionContext struct {
	// Command details
	CommandString string
	Namespace     string
	WorkDir       string

	// Environment
	Environment map[string]string

	// Security
	ReadOnly     bool
	Capabilities []string // Linux capabilities to retain

	// Resource constraints
	CPULimit    string
	MemoryLimit string
	Timeout     time.Duration
}

// ExecutionResult contains the outcome of sandboxed execution.
type ExecutionResult struct {
	Success     bool
	Output      string
	Error       error
	ExitCode    int
	Duration    time.Duration
	Violations  []string // Any sandbox violations detected
	DryRun      bool     // If true, command was simulated only
}

// ValidationResult contains path/namespace validation outcome.
type ValidationResult struct {
	Valid   bool
	Reason  string
	Allowed bool
}

// NewSandbox creates a new sandbox with configuration.
func NewSandbox(config *SandboxConfig) (*Sandbox, error) {
	if config == nil {
		return nil, errors.New("sandbox config cannot be nil")
	}

	// Set defaults
	if config.DefaultNamespace == "" {
		config.DefaultNamespace = "default"
	}
	if config.Timeout == 0 {
		config.Timeout = 30 * time.Second // Default 30s timeout
	}
	if config.MaxCPU == "" {
		config.MaxCPU = "100m" // 100 millicores
	}
	if config.MaxMemory == "" {
		config.MaxMemory = "128Mi"
	}

	return &Sandbox{
		config:          config,
		resourceLimiter: NewResourceLimiter(config),
		pathValidator:   NewPathValidator(config),
	}, nil
}

// ValidateNamespace checks if a namespace is allowed.
func (s *Sandbox) ValidateNamespace(namespace string) *ValidationResult {
	// Empty namespace defaults to configured default
	if namespace == "" {
		namespace = s.config.DefaultNamespace
	}

	// Check forbidden list first (blacklist takes precedence)
	for _, forbidden := range s.config.ForbiddenNamespaces {
		if namespace == forbidden || forbidden == "*" {
			return &ValidationResult{
				Valid:   false,
				Reason:  fmt.Sprintf("namespace '%s' is forbidden", namespace),
				Allowed: false,
			}
		}
	}

	// If whitelist exists, namespace must be in it
	if len(s.config.AllowedNamespaces) > 0 {
		for _, allowed := range s.config.AllowedNamespaces {
			if namespace == allowed || allowed == "*" {
				return &ValidationResult{
					Valid:   true,
					Reason:  fmt.Sprintf("namespace '%s' is allowed", namespace),
					Allowed: true,
				}
			}
		}

		// Not in whitelist
		return &ValidationResult{
			Valid:   false,
			Reason:  fmt.Sprintf("namespace '%s' not in whitelist", namespace),
			Allowed: false,
		}
	}

	// No whitelist configured - allow by default (but check blacklist)
	return &ValidationResult{
		Valid:   true,
		Reason:  fmt.Sprintf("namespace '%s' allowed (no whitelist configured)", namespace),
		Allowed: true,
	}
}

// ValidatePath checks if a file path is allowed.
func (s *Sandbox) ValidatePath(path string) *ValidationResult {
	return s.pathValidator.Validate(path)
}

// Execute runs a command in the sandbox (simulation for v1.0).
func (s *Sandbox) Execute(execCtx *ExecutionContext) (*ExecutionResult, error) {
	if execCtx == nil {
		return nil, errors.New("execution context cannot be nil")
	}

	violations := []string{}

	// Validate namespace
	nsValidation := s.ValidateNamespace(execCtx.Namespace)
	if !nsValidation.Valid {
		violations = append(violations, nsValidation.Reason)
	}

	// Validate working directory path
	if execCtx.WorkDir != "" {
		pathValidation := s.ValidatePath(execCtx.WorkDir)
		if !pathValidation.Valid {
			violations = append(violations, pathValidation.Reason)
		}
	}

	// Validate resource limits
	if err := s.resourceLimiter.Validate(execCtx); err != nil {
		violations = append(violations, err.Error())
	}

	// If violations found, deny execution
	if len(violations) > 0 {
		return &ExecutionResult{
			Success:    false,
			Error:      fmt.Errorf("sandbox violations detected: %d violations", len(violations)),
			Violations: violations,
			DryRun:     true, // Mark as simulation
		}, nil
	}

	// For v1.0: Simulate successful execution
	// Real implementation would use containerization/namespacing
	return &ExecutionResult{
		Success:    true,
		Output:     fmt.Sprintf("Command would execute in namespace '%s' with constraints", execCtx.Namespace),
		Violations: []string{},
		DryRun:     true, // v1.0 simulates only
		Duration:   time.Millisecond * 100,
	}, nil
}

// DryRun validates without executing.
func (s *Sandbox) DryRun(execCtx *ExecutionContext) (*ExecutionResult, error) {
	result, err := s.Execute(execCtx)
	if result != nil {
		result.DryRun = true
	}
	return result, err
}

// GetConfig returns the sandbox configuration.
func (s *Sandbox) GetConfig() *SandboxConfig {
	return s.config
}

// IsNamespaceAllowed is a convenience method.
func (s *Sandbox) IsNamespaceAllowed(namespace string) bool {
	return s.ValidateNamespace(namespace).Allowed
}

// IsPathAllowed is a convenience method.
func (s *Sandbox) IsPathAllowed(path string) bool {
	return s.ValidatePath(path).Allowed
}

// PathValidator validates file system paths.
type PathValidator struct {
	allowedPaths   []string
	forbiddenPaths []string
}

// NewPathValidator creates a path validator.
func NewPathValidator(config *SandboxConfig) *PathValidator {
	return &PathValidator{
		allowedPaths:   config.AllowedPaths,
		forbiddenPaths: config.ForbiddenPaths,
	}
}

// Validate checks if a path is allowed.
func (pv *PathValidator) Validate(path string) *ValidationResult {
	// Clean path
	path = filepath.Clean(path)

	// Check forbidden paths first
	for _, forbidden := range pv.forbiddenPaths {
		if strings.HasPrefix(path, forbidden) || path == forbidden {
			return &ValidationResult{
				Valid:   false,
				Reason:  fmt.Sprintf("path '%s' is forbidden", path),
				Allowed: false,
			}
		}
	}

	// If whitelist exists, path must match
	if len(pv.allowedPaths) > 0 {
		for _, allowed := range pv.allowedPaths {
			if strings.HasPrefix(path, allowed) || path == allowed {
				return &ValidationResult{
					Valid:   true,
					Reason:  fmt.Sprintf("path '%s' is allowed", path),
					Allowed: true,
				}
			}
		}

		// Not in whitelist
		return &ValidationResult{
			Valid:   false,
			Reason:  fmt.Sprintf("path '%s' not in whitelist", path),
			Allowed: false,
		}
	}

	// No whitelist - allow by default
	return &ValidationResult{
		Valid:   true,
		Reason:  fmt.Sprintf("path '%s' allowed", path),
		Allowed: true,
	}
}

// ResourceLimiter validates and enforces resource limits.
type ResourceLimiter struct {
	maxCPU     string
	maxMemory  string
	maxStorage string
	timeout    time.Duration
}

// NewResourceLimiter creates a resource limiter.
func NewResourceLimiter(config *SandboxConfig) *ResourceLimiter {
	return &ResourceLimiter{
		maxCPU:     config.MaxCPU,
		maxMemory:  config.MaxMemory,
		maxStorage: config.MaxStorage,
		timeout:    config.Timeout,
	}
}

// Validate checks if execution context respects resource limits.
func (rl *ResourceLimiter) Validate(execCtx *ExecutionContext) error {
	// Check timeout
	if execCtx.Timeout > rl.timeout {
		return fmt.Errorf("timeout %v exceeds limit %v", execCtx.Timeout, rl.timeout)
	}

	// Check CPU limit
	if execCtx.CPULimit != "" && !rl.isWithinLimit(execCtx.CPULimit, rl.maxCPU) {
		return fmt.Errorf("CPU limit %s exceeds maximum %s", execCtx.CPULimit, rl.maxCPU)
	}

	// Check memory limit
	if execCtx.MemoryLimit != "" && !rl.isWithinLimit(execCtx.MemoryLimit, rl.maxMemory) {
		return fmt.Errorf("memory limit %s exceeds maximum %s", execCtx.MemoryLimit, rl.maxMemory)
	}

	return nil
}

// isWithinLimit checks if requested limit is within allowed limit.
// Simplified for v1.0 - real impl would parse units properly.
func (rl *ResourceLimiter) isWithinLimit(requested, maximum string) bool {
	// Simplified: just string comparison
	// Real implementation would parse m/Mi/Gi units
	return len(requested) <= len(maximum)
}

// GetMaxTimeout returns the maximum allowed timeout.
func (rl *ResourceLimiter) GetMaxTimeout() time.Duration {
	return rl.timeout
}
