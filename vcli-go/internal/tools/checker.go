// Package tools provides tool availability checking and registry
// Following Boris Cherny principles: "Make it impossible to use a tool that's not available"
package tools

import (
	"fmt"
	"os/exec"
	"sync"

	"github.com/verticedev/vcli-go/internal/errors"
)

// Tool represents a registered external tool
type Tool struct {
	// Name is the tool binary name
	Name string

	// Required indicates if this tool is mandatory for vcli-go to function
	Required bool

	// Severity indicates the error severity if tool is missing
	Severity errors.Severity

	// InstallCmd provides installation instructions
	InstallCmd string
}

// Checker provides thread-safe tool availability checking with caching
type Checker struct {
	// mu protects tools and cache maps
	mu sync.RWMutex

	// tools is the registry of known tools
	tools map[string]*Tool

	// cache stores availability check results to avoid repeated exec.LookPath calls
	cache map[string]bool
}

// NewChecker creates a new Checker instance
func NewChecker() *Checker {
	return &Checker{
		tools: make(map[string]*Tool),
		cache: make(map[string]bool),
	}
}

// Register adds a tool to the registry
// If the tool already exists, it will be overwritten
func (c *Checker) Register(name string, required bool, severity errors.Severity, installCmd string) error {
	if name == "" {
		return fmt.Errorf("tool name cannot be empty")
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	c.tools[name] = &Tool{
		Name:       name,
		Required:   required,
		Severity:   severity,
		InstallCmd: installCmd,
	}

	return nil
}

// Check verifies if a tool is available in PATH
// Returns (true, nil) if available
// Returns (false, ToolError) if not available
// Uses cache to avoid repeated system calls
func (c *Checker) Check(toolName string) (bool, error) {
	if toolName == "" {
		return false, errors.NewToolError(
			"",
			fmt.Errorf("tool name cannot be empty"),
			errors.SeverityError,
			"",
		)
	}

	// Check cache first
	c.mu.RLock()
	if cached, exists := c.cache[toolName]; exists {
		tool := c.tools[toolName]
		c.mu.RUnlock()

		// If cached as unavailable, return appropriate error
		if !cached && tool != nil {
			return false, errors.NewToolError(
				tool.Name,
				errors.ErrToolNotFound,
				tool.Severity,
				tool.InstallCmd,
			)
		}

		return cached, nil
	}
	c.mu.RUnlock()

	// Perform actual availability check
	_, err := exec.LookPath(toolName)
	available := err == nil

	// Update cache
	c.mu.Lock()
	c.cache[toolName] = available
	c.mu.Unlock()

	// If unavailable, construct appropriate error
	if !available {
		c.mu.RLock()
		tool, registered := c.tools[toolName]
		c.mu.RUnlock()

		if registered {
			return false, errors.NewToolError(
				tool.Name,
				errors.ErrToolNotFound,
				tool.Severity,
				tool.InstallCmd,
			)
		}

		// Unregistered tool - use default severity
		return false, errors.NewToolError(
			toolName,
			errors.ErrToolNotFound,
			errors.SeverityError,
			"",
		)
	}

	return true, nil
}

// CheckMultiple checks multiple tools and returns all errors
// This allows collecting all missing tools at once rather than failing fast
func (c *Checker) CheckMultiple(toolNames []string) []error {
	if len(toolNames) == 0 {
		return []error{}
	}

	var errs []error

	for _, toolName := range toolNames {
		if _, err := c.Check(toolName); err != nil {
			errs = append(errs, err)
		}
	}

	return errs
}

// IsAvailable is a convenience method that returns only the boolean
// Useful when you just need to know if a tool exists, without error details
func (c *Checker) IsAvailable(toolName string) bool {
	available, _ := c.Check(toolName)
	return available
}

// GetMissing returns a list of all checked tools that were not available
// Only includes tools that have been checked at least once
func (c *Checker) GetMissing() []string {
	c.mu.RLock()
	defer c.mu.RUnlock()

	var missing []string

	for toolName, available := range c.cache {
		if !available {
			missing = append(missing, toolName)
		}
	}

	return missing
}

// ClearCache clears the availability cache
// Useful when tools may have been installed during runtime
func (c *Checker) ClearCache() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.cache = make(map[string]bool)
}

// IsToolAvailable is a package-level helper for one-off checks
// For repeated checks, create a Checker instance to benefit from caching
func IsToolAvailable(toolName string) bool {
	_, err := exec.LookPath(toolName)
	return err == nil
}
