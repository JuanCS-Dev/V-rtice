package tools

import (
	"errors"
	"strings"
	"testing"

	vcliErrors "github.com/verticedev/vcli-go/internal/errors"
)

// TestDefaultRegistry tests the global registry instance
func TestDefaultRegistry(t *testing.T) {
	if DefaultRegistry == nil {
		t.Fatal("DefaultRegistry is nil")
	}

	if DefaultRegistry.checker == nil {
		t.Fatal("DefaultRegistry.checker is nil")
	}
}

// TestNewRegistry tests registry creation
func TestNewRegistry(t *testing.T) {
	registry := NewRegistry()

	if registry == nil {
		t.Fatal("NewRegistry() returned nil")
	}

	if registry.checker == nil {
		t.Error("NewRegistry() did not initialize checker")
	}
}

// TestRegistry_RegisterCore tests core tool registration
func TestRegistry_RegisterCore(t *testing.T) {
	registry := NewRegistry()

	// Register core tools
	registry.RegisterCore()

	// Verify known core tools are registered
	coreTools := []string{"kubectl", "python3", "go"}

	for _, toolName := range coreTools {
		// Check should not panic
		_, err := registry.Check(toolName)

		// Error is OK (tool might not be installed), but should be ToolError
		if err != nil {
			var toolErr *vcliErrors.ToolError
			if !isToolError(err) {
				t.Errorf("Check(%q) returned non-ToolError: %T", toolName, err)
			}

			// If it's a ToolError, verify it has install guide
			if errors.As(err, &toolErr) && toolErr.InstallGuide == "" {
				t.Errorf("Core tool %q should have InstallGuide", toolName)
			}
		}
	}
}

// TestRegistry_RegisterOptional tests optional tool registration
func TestRegistry_RegisterOptional(t *testing.T) {
	registry := NewRegistry()

	// Register optional tools
	registry.RegisterOptional()

	// Verify known optional tools are registered with warn severity
	optionalTools := []string{"gosec", "golangci-lint", "autopep8", "black"}

	for _, toolName := range optionalTools {
		_, err := registry.Check(toolName)

		if err != nil {
			var toolErr *vcliErrors.ToolError
			if isToolError(err) {
				// Get the actual ToolError
				_ = errors.As(err, &toolErr)

				// Optional tools should have Warn or Info severity, not Fatal
				if toolErr != nil && toolErr.Severity == vcliErrors.SeverityFatal {
					t.Errorf("Optional tool %q should not have Fatal severity", toolName)
				}
			}
		}
	}
}

// TestRegistry_CheckAll tests checking all registered tools
func TestRegistry_CheckAll(t *testing.T) {
	registry := NewRegistry()

	// Register some tools
	registry.RegisterCore()
	registry.RegisterOptional()

	// Check all
	results := registry.CheckAll()

	if len(results) == 0 {
		t.Error("CheckAll() returned no results after registering tools")
	}

	// Verify results structure
	for toolName, result := range results {
		if toolName == "" {
			t.Error("CheckAll() returned empty tool name")
		}

		if !result.Available && result.Error == nil {
			t.Errorf("CheckAll() tool %q unavailable but no error", toolName)
		}
	}
}

// TestRegistry_GetMissingRequired tests finding missing required tools
func TestRegistry_GetMissingRequired(t *testing.T) {
	registry := NewRegistry()

	// Register a known-missing required tool
	err := registry.checker.Register("definitely-does-not-exist-xyz", true, vcliErrors.SeverityFatal, "install it")
	if err != nil {
		t.Fatalf("Register() failed: %v", err)
	}

	// Check it
	_, _ = registry.Check("definitely-does-not-exist-xyz")

	// Get missing required tools
	missing := registry.GetMissingRequired()

	// Should include our missing tool
	found := false
	for _, toolName := range missing {
		if toolName == "definitely-does-not-exist-xyz" {
			found = true
			break
		}
	}

	if !found {
		t.Error("GetMissingRequired() did not include missing required tool")
	}
}

// TestRegistry_CheckPreFlight tests pre-flight validation
func TestRegistry_CheckPreFlight(t *testing.T) {
	registry := NewRegistry()

	// Register mix of tools
	_ = registry.checker.Register("go", true, vcliErrors.SeverityFatal, "install go")
	_ = registry.checker.Register("missing-required", true, vcliErrors.SeverityFatal, "install it")
	_ = registry.checker.Register("missing-optional", false, vcliErrors.SeverityWarn, "install it")

	errs := registry.CheckPreFlight()

	// Should have at least the missing required tool
	if len(errs) == 0 {
		t.Error("CheckPreFlight() expected errors for missing required tool")
	}

	// All errors should be ToolErrors
	for _, err := range errs {
		if !isToolError(err) {
			t.Errorf("CheckPreFlight() error should be ToolError, got %T", err)
		}
	}

	// Should only include required tools
	for _, err := range errs {
		var toolErr *vcliErrors.ToolError
		if errors.As(err, &toolErr) {
			if strings.Contains(toolErr.Tool, "optional") {
				t.Error("CheckPreFlight() should only check required tools")
			}
		}
	}
}

// TestRegistry_FormatMissingTools tests error message formatting
func TestRegistry_FormatMissingTools(t *testing.T) {
	registry := NewRegistry()

	// Register and check some tools
	_ = registry.checker.Register("go", true, vcliErrors.SeverityFatal, "install from golang.org")
	_ = registry.checker.Register("missing-tool", true, vcliErrors.SeverityFatal, "curl -L install-url.sh | sh")

	_, _ = registry.Check("go")
	_, _ = registry.Check("missing-tool")

	message := registry.FormatMissingTools()

	// Should be non-empty if there are missing tools
	if message == "" && len(registry.checker.GetMissing()) > 0 {
		t.Error("FormatMissingTools() returned empty string with missing tools")
	}

	// If there are missing tools, message should include install instructions
	missing := registry.checker.GetMissing()
	if len(missing) > 0 && !strings.Contains(message, "missing-tool") {
		t.Error("FormatMissingTools() should mention missing tool names")
	}
}

// TestRegistry_Check tests individual tool checking through registry
func TestRegistry_Check(t *testing.T) {
	registry := NewRegistry()

	// Register a tool
	err := registry.checker.Register("go", true, vcliErrors.SeverityFatal, "install go")
	if err != nil {
		t.Fatalf("Register() failed: %v", err)
	}

	// Check it
	available, checkErr := registry.Check("go")

	// go should be available on this system
	if !available {
		t.Logf("Note: go not available on this system: %v", checkErr)
	}

	// Error should be ToolError if not available
	if checkErr != nil && !isToolError(checkErr) {
		t.Errorf("Check() error should be ToolError, got %T", checkErr)
	}
}

// TestRegistry_IsAvailable tests availability checking
func TestRegistry_IsAvailable(t *testing.T) {
	registry := NewRegistry()

	tests := []struct {
		name     string
		toolName string
		want     bool
	}{
		{"go is available", "go", true},
		{"python3 is available", "python3", true},
		{"nonexistent tool", "definitely-not-a-real-tool-xyz", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := registry.IsAvailable(tt.toolName)

			if got != tt.want {
				t.Errorf("IsAvailable(%q) = %v, want %v", tt.toolName, got, tt.want)
			}
		})
	}
}

// TestRegistry_ResetCache tests cache invalidation
func TestRegistry_ResetCache(t *testing.T) {
	registry := NewRegistry()

	// Check a tool to populate cache
	_, _ = registry.Check("go")

	// Verify cache has entries
	cacheSizeBefore := len(registry.checker.cache)
	if cacheSizeBefore == 0 {
		t.Fatal("Cache was not populated")
	}

	// Reset cache
	registry.ResetCache()

	// Verify cache is empty
	cacheSizeAfter := len(registry.checker.cache)
	if cacheSizeAfter != 0 {
		t.Errorf("ResetCache() did not clear cache, size = %d", cacheSizeAfter)
	}
}

// TestCheckResult tests the CheckResult struct
func TestCheckResult(t *testing.T) {
	t.Run("available tool", func(t *testing.T) {
		result := CheckResult{
			Tool:      "go",
			Available: true,
			Error:     nil,
		}

		if !result.Available {
			t.Error("Available should be true")
		}

		if result.Error != nil {
			t.Error("Error should be nil for available tool")
		}
	})

	t.Run("unavailable tool", func(t *testing.T) {
		err := vcliErrors.NewToolError("gosec", vcliErrors.ErrToolNotFound, vcliErrors.SeverityWarn, "go install gosec")

		result := CheckResult{
			Tool:      "gosec",
			Available: false,
			Error:     err,
		}

		if result.Available {
			t.Error("Available should be false")
		}

		if result.Error == nil {
			t.Error("Error should not be nil for unavailable tool")
		}
	})
}

// TestRegistry_Integration tests realistic workflow
func TestRegistry_Integration(t *testing.T) {
	t.Run("kubectl command workflow", func(t *testing.T) {
		registry := NewRegistry()
		registry.RegisterCore()

		// Pre-flight check
		errs := registry.CheckPreFlight()

		// Collect missing required tools
		var missingRequired []string
		for _, err := range errs {
			var toolErr *vcliErrors.ToolError
			if errors.As(err, &toolErr) {
				if toolErr.Severity == vcliErrors.SeverityFatal {
					missingRequired = append(missingRequired, toolErr.Tool)
				}
			}
		}

		// If kubectl is missing and required, should be in the list
		if !registry.IsAvailable("kubectl") {
			found := false
			for _, tool := range missingRequired {
				if tool == "kubectl" {
					found = true
					break
				}
			}

			// This is informational - kubectl might not be installed
			t.Logf("kubectl not available: %v", found)
		}
	})

	t.Run("formatter workflow", func(t *testing.T) {
		registry := NewRegistry()
		registry.RegisterOptional()

		// Check formatters
		blackAvailable := registry.IsAvailable("black")
		autopep8Available := registry.IsAvailable("autopep8")

		// Should have at least one formatter or graceful degradation
		if !blackAvailable && !autopep8Available {
			t.Log("No Python formatters available - would need graceful degradation")
		}
	})
}

// TestRegistry_DefaultRegistryUsage tests using the global instance
func TestRegistry_DefaultRegistryUsage(t *testing.T) {
	// Reset default registry for clean test
	DefaultRegistry = NewRegistry()
	DefaultRegistry.RegisterCore()

	// Use global instance
	available := DefaultRegistry.IsAvailable("go")

	if !available {
		t.Log("go not available via DefaultRegistry")
	}

	// Should not panic
	results := DefaultRegistry.CheckAll()

	if len(results) == 0 {
		t.Error("DefaultRegistry.CheckAll() returned no results after RegisterCore()")
	}
}

// Helper function to check if error is ToolError
func isToolError(err error) bool {
	if err == nil {
		return false
	}
	_, ok := err.(*vcliErrors.ToolError)
	return ok
}

// TestRegistry_EdgeCases tests edge cases
func TestRegistry_EdgeCases(t *testing.T) {
	t.Run("check before register", func(t *testing.T) {
		registry := NewRegistry()

		// Check unregistered tool
		_, err := registry.Check("unregistered-tool-xyz")

		// Should return error even if not registered
		if err == nil {
			t.Error("Check() on unregistered missing tool should return error")
		}
	})

	t.Run("double RegisterCore", func(t *testing.T) {
		registry := NewRegistry()

		// Should not panic
		registry.RegisterCore()
		registry.RegisterCore()
	})

	t.Run("double RegisterOptional", func(t *testing.T) {
		registry := NewRegistry()

		// Should not panic
		registry.RegisterOptional()
		registry.RegisterOptional()
	})

	t.Run("CheckAll on empty registry", func(t *testing.T) {
		registry := NewRegistry()

		results := registry.CheckAll()

		// Should return empty map
		if len(results) != 0 {
			t.Errorf("CheckAll() on empty registry should return empty map, got %d results", len(results))
		}
	})

	t.Run("GetMissingRequired before any checks", func(t *testing.T) {
		registry := NewRegistry()
		registry.RegisterCore()

		missing := registry.GetMissingRequired()

		// Should return empty slice (nothing checked yet)
		if len(missing) != 0 {
			t.Errorf("GetMissingRequired() before checks should return empty, got %d", len(missing))
		}
	})

	t.Run("FormatMissingTools with no missing", func(t *testing.T) {
		registry := NewRegistry()

		message := registry.FormatMissingTools()

		// Should handle gracefully (empty or informational message)
		if message != "" {
			t.Logf("FormatMissingTools() with no missing tools: %q", message)
		}
	})
}
