package tools

import (
	"errors"
	"fmt"
	"strings"
	"sync"
	"testing"

	vcliErrors "github.com/verticedev/vcli-go/internal/errors"
)

// TestNewChecker tests the checker constructor
func TestNewChecker(t *testing.T) {
	checker := NewChecker()

	if checker == nil {
		t.Fatal("NewChecker() returned nil")
	}

	if checker.tools == nil {
		t.Error("NewChecker() did not initialize tools map")
	}

	if checker.cache == nil {
		t.Error("NewChecker() did not initialize cache map")
	}
}

// TestChecker_Register tests tool registration
func TestChecker_Register(t *testing.T) {
	tests := []struct {
		name        string
		toolName    string
		required    bool
		severity    vcliErrors.Severity
		installCmd  string
		wantErr     bool
		errContains string
	}{
		{
			name:       "register required tool",
			toolName:   "kubectl",
			required:   true,
			severity:   vcliErrors.SeverityFatal,
			installCmd: "curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl",
			wantErr:    false,
		},
		{
			name:       "register optional tool",
			toolName:   "gosec",
			required:   false,
			severity:   vcliErrors.SeverityWarn,
			installCmd: "go install github.com/securego/gosec/v2/cmd/gosec@latest",
			wantErr:    false,
		},
		{
			name:        "empty tool name",
			toolName:    "",
			required:    true,
			severity:    vcliErrors.SeverityFatal,
			installCmd:  "some command",
			wantErr:     true,
			errContains: "tool name cannot be empty",
		},
		{
			name:       "empty install command is allowed",
			toolName:   "python3",
			required:   true,
			severity:   vcliErrors.SeverityFatal,
			installCmd: "",
			wantErr:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			checker := NewChecker()

			err := checker.Register(tt.toolName, tt.required, tt.severity, tt.installCmd)

			if tt.wantErr {
				if err == nil {
					t.Error("Register() expected error but got nil")
					return
				}
				if !strings.Contains(err.Error(), tt.errContains) {
					t.Errorf("Register() error = %q, want to contain %q", err.Error(), tt.errContains)
				}
				return
			}

			if err != nil {
				t.Errorf("Register() unexpected error: %v", err)
				return
			}

			// Verify tool was registered
			if _, exists := checker.tools[tt.toolName]; !exists {
				t.Errorf("Register() did not add tool %q to registry", tt.toolName)
			}
		})
	}
}

// TestChecker_Check tests tool availability checking
func TestChecker_Check(t *testing.T) {
	tests := []struct {
		name         string
		toolName     string
		setupFunc    func(*Checker)
		expectAvail  bool
		expectErr    bool
		errSeverity  vcliErrors.Severity
	}{
		{
			name:     "check existing tool (go)",
			toolName: "go",
			setupFunc: func(c *Checker) {
				_ = c.Register("go", true, vcliErrors.SeverityFatal, "install from golang.org")
			},
			expectAvail: true,
			expectErr:   false,
		},
		{
			name:     "check non-existent required tool",
			toolName: "nonexistent-tool-12345",
			setupFunc: func(c *Checker) {
				_ = c.Register("nonexistent-tool-12345", true, vcliErrors.SeverityFatal, "install it somehow")
			},
			expectAvail: false,
			expectErr:   true,
			errSeverity: vcliErrors.SeverityFatal,
		},
		{
			name:     "check non-existent optional tool",
			toolName: "optional-missing-tool",
			setupFunc: func(c *Checker) {
				_ = c.Register("optional-missing-tool", false, vcliErrors.SeverityWarn, "go install example.com/tool@latest")
			},
			expectAvail: false,
			expectErr:   true,
			errSeverity: vcliErrors.SeverityWarn,
		},
		{
			name:        "check unregistered tool",
			toolName:    "unregistered-tool",
			setupFunc:   func(c *Checker) {},
			expectAvail: false,
			expectErr:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			checker := NewChecker()
			tt.setupFunc(checker)

			available, err := checker.Check(tt.toolName)

			if available != tt.expectAvail {
				t.Errorf("Check() available = %v, want %v", available, tt.expectAvail)
			}

			if tt.expectErr {
				if err == nil {
					t.Error("Check() expected error but got nil")
					return
				}

				// Verify error is ToolError
				var toolErr *vcliErrors.ToolError
				if !errors.As(err, &toolErr) {
					t.Errorf("Check() error should be *ToolError, got %T", err)
					return
				}

				// Verify severity if specified
				if tt.errSeverity != 0 && toolErr.Severity != tt.errSeverity {
					t.Errorf("Check() error severity = %v, want %v", toolErr.Severity, tt.errSeverity)
				}

				// Verify InstallGuide is set for registered tools
				if tt.toolName != "unregistered-tool" && toolErr.InstallGuide == "" {
					t.Error("Check() ToolError should have InstallGuide set")
				}
			} else {
				if err != nil {
					t.Errorf("Check() unexpected error: %v", err)
				}
			}
		})
	}
}

// TestChecker_CheckWithCache tests that repeated checks use cache
func TestChecker_CheckWithCache(t *testing.T) {
	checker := NewChecker()
	_ = checker.Register("go", true, vcliErrors.SeverityFatal, "install from golang.org")

	// First check
	avail1, err1 := checker.Check("go")
	if err1 != nil {
		t.Fatalf("First Check() failed: %v", err1)
	}

	// Second check should use cache
	avail2, err2 := checker.Check("go")
	if err2 != nil {
		t.Fatalf("Second Check() failed: %v", err2)
	}

	if avail1 != avail2 {
		t.Error("Cached check returned different result")
	}

	// Verify cache was populated
	checker.mu.RLock()
	cached, exists := checker.cache["go"]
	checker.mu.RUnlock()

	if !exists {
		t.Error("Check() did not populate cache")
	}

	if cached != avail1 {
		t.Error("Cached value does not match check result")
	}
}

// TestChecker_CheckMultiple tests checking multiple tools
func TestChecker_CheckMultiple(t *testing.T) {
	checker := NewChecker()

	// Register multiple tools
	tools := []struct {
		name       string
		required   bool
		severity   vcliErrors.Severity
		installCmd string
	}{
		{"go", true, vcliErrors.SeverityFatal, "install from golang.org"},
		{"python3", true, vcliErrors.SeverityFatal, "install from python.org"},
		{"gosec", false, vcliErrors.SeverityWarn, "go install github.com/securego/gosec/v2/cmd/gosec@latest"},
		{"nonexistent-xyz", false, vcliErrors.SeverityWarn, "install somehow"},
	}

	for _, tool := range tools {
		if err := checker.Register(tool.name, tool.required, tool.severity, tool.installCmd); err != nil {
			t.Fatalf("Register(%q) failed: %v", tool.name, err)
		}
	}

	errs := checker.CheckMultiple([]string{"go", "python3", "gosec", "nonexistent-xyz"})

	// Should have at least one error (nonexistent-xyz)
	if len(errs) == 0 {
		t.Error("CheckMultiple() expected at least one error for nonexistent-xyz")
	}

	// All errors should be ToolErrors
	for _, err := range errs {
		var toolErr *vcliErrors.ToolError
		if !errors.As(err, &toolErr) {
			t.Errorf("CheckMultiple() error should be *ToolError, got %T: %v", err, err)
		}
	}

	// Check that available tools don't have errors
	for _, err := range errs {
		var toolErr *vcliErrors.ToolError
		if errors.As(err, &toolErr) {
			if toolErr.Tool == "go" || toolErr.Tool == "python3" {
				// These should be available, so shouldn't error
				// (unless they're truly not in PATH on this system)
				t.Logf("Note: %s reported as unavailable: %v", toolErr.Tool, err)
			}
		}
	}
}

// TestChecker_Concurrent tests thread safety
func TestChecker_Concurrent(t *testing.T) {
	checker := NewChecker()

	// Register some tools
	tools := []string{"go", "python3", "kubectl", "gosec", "docker"}
	for _, tool := range tools {
		_ = checker.Register(tool, false, vcliErrors.SeverityWarn, fmt.Sprintf("install %s", tool))
	}

	var wg sync.WaitGroup
	concurrency := 50

	// Launch concurrent checks
	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(iteration int) {
			defer wg.Done()

			// Check each tool
			for _, tool := range tools {
				_, _ = checker.Check(tool)
			}

			// Also try to register during concurrent checks
			newTool := fmt.Sprintf("tool-%d", iteration)
			_ = checker.Register(newTool, false, vcliErrors.SeverityInfo, "install it")
		}(i)
	}

	// Should not panic or race
	wg.Wait()
}

// TestChecker_IsAvailable tests the IsAvailable helper
func TestChecker_IsAvailable(t *testing.T) {
	tests := []struct {
		name     string
		toolName string
		want     bool
	}{
		{"go is available", "go", true},
		{"python3 is available", "python3", true},
		{"nonexistent tool is not available", "definitely-does-not-exist-xyz", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			checker := NewChecker()
			got := checker.IsAvailable(tt.toolName)

			if got != tt.want {
				t.Errorf("IsAvailable(%q) = %v, want %v", tt.toolName, got, tt.want)
			}
		})
	}
}

// TestChecker_GetMissing tests retrieving missing tools
func TestChecker_GetMissing(t *testing.T) {
	checker := NewChecker()

	// Register mix of available and unavailable tools
	_ = checker.Register("go", true, vcliErrors.SeverityFatal, "install go")
	_ = checker.Register("nonexistent-abc", true, vcliErrors.SeverityFatal, "install abc")
	_ = checker.Register("nonexistent-def", false, vcliErrors.SeverityWarn, "install def")

	// Check all tools
	_, _ = checker.Check("go")
	_, _ = checker.Check("nonexistent-abc")
	_, _ = checker.Check("nonexistent-def")

	missing := checker.GetMissing()

	// Should contain the nonexistent tools
	if len(missing) < 2 {
		t.Errorf("GetMissing() returned %d tools, expected at least 2", len(missing))
	}

	// Verify missing tools are in the list
	foundAbc := false
	foundDef := false
	for _, tool := range missing {
		if tool == "nonexistent-abc" {
			foundAbc = true
		}
		if tool == "nonexistent-def" {
			foundDef = true
		}
	}

	if !foundAbc {
		t.Error("GetMissing() did not include nonexistent-abc")
	}
	if !foundDef {
		t.Error("GetMissing() did not include nonexistent-def")
	}

	// Should NOT contain available tools
	for _, tool := range missing {
		if tool == "go" {
			t.Error("GetMissing() incorrectly included available tool 'go'")
		}
	}
}

// TestChecker_ClearCache tests cache clearing
func TestChecker_ClearCache(t *testing.T) {
	checker := NewChecker()
	_ = checker.Register("go", true, vcliErrors.SeverityFatal, "install go")

	// Check to populate cache
	_, _ = checker.Check("go")

	// Verify cache has entry
	checker.mu.RLock()
	cacheSize := len(checker.cache)
	checker.mu.RUnlock()

	if cacheSize == 0 {
		t.Fatal("Cache was not populated")
	}

	// Clear cache
	checker.ClearCache()

	// Verify cache is empty
	checker.mu.RLock()
	cacheSize = len(checker.cache)
	checker.mu.RUnlock()

	if cacheSize != 0 {
		t.Errorf("ClearCache() did not clear cache, size = %d", cacheSize)
	}
}

// TestIsToolAvailable tests the package-level helper function
func TestIsToolAvailable(t *testing.T) {
	tests := []struct {
		name     string
		toolName string
		want     bool
	}{
		{"go is available", "go", true},
		{"python3 is available", "python3", true},
		{"sh is available", "sh", true},
		{"nonexistent tool", "absolutely-does-not-exist-12345", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsToolAvailable(tt.toolName)

			if got != tt.want {
				t.Errorf("IsToolAvailable(%q) = %v, want %v", tt.toolName, got, tt.want)
			}
		})
	}
}

// TestChecker_EdgeCases tests edge cases for robustness
func TestChecker_EdgeCases(t *testing.T) {
	t.Run("double register same tool", func(t *testing.T) {
		checker := NewChecker()

		err1 := checker.Register("go", true, vcliErrors.SeverityFatal, "install go")
		if err1 != nil {
			t.Fatalf("First Register() failed: %v", err1)
		}

		// Second registration should succeed (overwrites)
		err2 := checker.Register("go", false, vcliErrors.SeverityWarn, "different install")
		if err2 != nil {
			t.Errorf("Second Register() failed: %v", err2)
		}

		// Verify it was overwritten
		tool, exists := checker.tools["go"]
		if !exists {
			t.Fatal("Tool not found after double register")
		}

		if tool.Required {
			t.Error("Second Register() did not overwrite Required field")
		}
	})

	t.Run("check empty string", func(t *testing.T) {
		checker := NewChecker()

		_, err := checker.Check("")
		if err == nil {
			t.Error("Check(\"\") should return error")
		}
	})

	t.Run("CheckMultiple with empty slice", func(t *testing.T) {
		checker := NewChecker()

		errs := checker.CheckMultiple([]string{})
		if len(errs) != 0 {
			t.Errorf("CheckMultiple([]) should return empty slice, got %d errors", len(errs))
		}
	})

	t.Run("CheckMultiple with nil slice", func(t *testing.T) {
		checker := NewChecker()

		errs := checker.CheckMultiple(nil)
		if len(errs) != 0 {
			t.Errorf("CheckMultiple(nil) should return empty slice, got %d errors", len(errs))
		}
	})

	t.Run("GetMissing before any checks", func(t *testing.T) {
		checker := NewChecker()

		missing := checker.GetMissing()
		if len(missing) != 0 {
			t.Errorf("GetMissing() before any checks should return empty slice, got %d items", len(missing))
		}
	})
}

// Benchmark_Check benchmarks the Check method
func Benchmark_Check(b *testing.B) {
	checker := NewChecker()
	_ = checker.Register("go", true, vcliErrors.SeverityFatal, "install go")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = checker.Check("go")
	}
}

// Benchmark_Check_Cached benchmarks cached checks
func Benchmark_Check_Cached(b *testing.B) {
	checker := NewChecker()
	_ = checker.Register("go", true, vcliErrors.SeverityFatal, "install go")

	// Warm up cache
	_, _ = checker.Check("go")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = checker.Check("go")
	}
}

// Benchmark_IsToolAvailable benchmarks the package helper
func Benchmark_IsToolAvailable(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = IsToolAvailable("go")
	}
}
