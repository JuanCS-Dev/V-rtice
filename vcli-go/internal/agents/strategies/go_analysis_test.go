package strategies

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
)

// TestNewGoAnalysisStrategy tests constructor
func TestNewGoAnalysisStrategy(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	if strategy == nil {
		t.Fatal("NewGoAnalysisStrategy() returned nil")
	}
}

// TestGoAnalysisStrategy_Language tests language identification
func TestGoAnalysisStrategy_Language(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	lang := strategy.Language()

	if lang != language.LanguageGo {
		t.Errorf("Language() = %v, want %v", lang, language.LanguageGo)
	}
}

// TestGoAnalysisStrategy_GetCapabilities tests capability reporting
func TestGoAnalysisStrategy_GetCapabilities(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	capabilities := strategy.GetCapabilities()

	if len(capabilities) == 0 {
		t.Error("GetCapabilities() returned no capabilities")
	}

	// Check for essential capabilities
	expectedCaps := []string{"go_vet", "gosec", "golangci-lint"}
	for _, expected := range expectedCaps {
		found := false
		for _, cap := range capabilities {
			if strings.Contains(cap, expected) {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("GetCapabilities() missing %q", expected)
		}
	}
}

// TestGoAnalysisStrategy_Analyze tests basic analysis
func TestGoAnalysisStrategy_Analyze(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Analyze current package (should work since we're in Go project)
	result, err := strategy.Analyze(ctx, []string{"."})

	// Should not error even if some tools are missing (graceful degradation)
	if err != nil {
		t.Errorf("Analyze() error: %v", err)
	}

	if result == nil {
		t.Fatal("Analyze() returned nil result")
	}

	// Result should have initialized slices
	if result.SecurityFindings == nil {
		t.Error("SecurityFindings should be initialized")
	}

	if result.PerformanceIssues == nil {
		t.Error("PerformanceIssues should be initialized")
	}

	if result.Recommendations == nil {
		t.Error("Recommendations should be initialized")
	}
}

// TestGoAnalysisStrategy_Analyze_GracefulDegradation tests missing tools
func TestGoAnalysisStrategy_Analyze_GracefulDegradation(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Run analysis - should NOT crash even if gosec/golangci-lint missing
	result, err := strategy.Analyze(ctx, []string{"."})

	// KEY TEST: Even if tools are missing, should return result (not error)
	if err != nil {
		t.Errorf("Analyze() should handle missing tools gracefully: %v", err)
	}

	if result == nil {
		t.Fatal("Analyze() should return result even if tools missing")
	}

	t.Logf("Analysis completed with %d security findings, %d recommendations",
		len(result.SecurityFindings), len(result.Recommendations))
}

// TestGoAnalysisStrategy_Analyze_EmptyTargets tests edge case
func TestGoAnalysisStrategy_Analyze_EmptyTargets(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx := context.Background()

	// Analyze with no targets
	result, err := strategy.Analyze(ctx, []string{})

	// Should not crash
	if err != nil {
		t.Errorf("Analyze() with empty targets error: %v", err)
	}

	if result == nil {
		t.Error("Analyze() should return result even with empty targets")
	}
}

// TestGoAnalysisStrategy_Analyze_ContextCancellation tests context handling
func TestGoAnalysisStrategy_Analyze_ContextCancellation(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	// Create already-cancelled context
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	// Run analysis
	result, err := strategy.Analyze(ctx, []string{"."})

	// Context cancellation is acceptable
	if err != nil {
		t.Logf("Analyze() with cancelled context: %v", err)
	}

	// Should still return a result (graceful degradation)
	if result == nil {
		t.Error("Analyze() should return result even with cancelled context")
	}
}

// TestGoAnalysisStrategy_Analyze_InvalidTargets tests error handling
func TestGoAnalysisStrategy_Analyze_InvalidTargets(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Analyze non-existent path
	result, err := strategy.Analyze(ctx, []string{"/nonexistent/path"})

	// Should not panic - graceful degradation
	if err != nil {
		t.Logf("Analyze() with invalid target: %v", err)
	}

	if result == nil {
		t.Error("Analyze() should return result even with invalid targets")
	}
}

// TestGoAnalysisStrategy_RunGoVet tests go vet execution
func TestGoAnalysisStrategy_RunGoVet(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	result := &agents.DiagnosticResult{
		SecurityFindings:  make([]agents.SecurityFinding, 0),
		PerformanceIssues: make([]agents.PerformanceIssue, 0),
		Recommendations:   make([]string, 0),
	}

	// Run go vet on current package
	err := strategy.runGoVet(ctx, []string{"."}, result)

	// Should not error (returns nil even on issues)
	if err != nil {
		t.Errorf("runGoVet() error: %v", err)
	}

	// May or may not have recommendations depending on code quality
	t.Logf("go vet found %d recommendations", len(result.Recommendations))
}

// TestGoAnalysisStrategy_RunLinter tests linter execution
func TestGoAnalysisStrategy_RunLinter(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	result := &agents.DiagnosticResult{
		SecurityFindings:  make([]agents.SecurityFinding, 0),
		PerformanceIssues: make([]agents.PerformanceIssue, 0),
		Recommendations:   make([]string, 0),
	}

	// Run linter - may not be installed
	err := strategy.runLinter(ctx, []string{"."}, result)

	// Should not error even if tool missing (graceful degradation)
	if err != nil {
		t.Logf("runLinter() returned (acceptable if tool missing): %v", err)
	}

	t.Logf("golangci-lint found %d recommendations", len(result.Recommendations))
}

// TestGoAnalysisStrategy_RunSecurityScan tests gosec execution
func TestGoAnalysisStrategy_RunSecurityScan(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	result := &agents.DiagnosticResult{
		SecurityFindings:  make([]agents.SecurityFinding, 0),
		PerformanceIssues: make([]agents.PerformanceIssue, 0),
		Recommendations:   make([]string, 0),
	}

	// Run security scan - may not be installed
	err := strategy.runSecurityScan(ctx, []string{"."}, result)

	// Should not error even if tool missing (graceful degradation)
	if err != nil {
		t.Logf("runSecurityScan() returned (acceptable if tool missing): %v", err)
	}

	t.Logf("gosec found %d security findings", len(result.SecurityFindings))
}

// TestGoAnalysisStrategy_Integration tests realistic workflow
func TestGoAnalysisStrategy_Integration(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Full analysis on current package
	result, err := strategy.Analyze(ctx, []string{"."})

	if err != nil {
		t.Fatalf("Integration test failed: %v", err)
	}

	if result == nil {
		t.Fatal("Integration test: nil result")
	}

	// Log results
	t.Logf("Integration test complete:")
	t.Logf("  Security findings: %d", len(result.SecurityFindings))
	t.Logf("  Performance issues: %d", len(result.PerformanceIssues))
	t.Logf("  Recommendations: %d", len(result.Recommendations))

	// Verify structure
	if result.SecurityFindings == nil || result.PerformanceIssues == nil || result.Recommendations == nil {
		t.Error("Result should have all slices initialized")
	}
}

// TestGoAnalysisStrategy_MultipleTargets tests analyzing multiple packages
func TestGoAnalysisStrategy_MultipleTargets(t *testing.T) {
	strategy := NewGoAnalysisStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Analyze multiple targets
	targets := []string{".", "./..."}
	result, err := strategy.Analyze(ctx, targets)

	if err != nil {
		t.Errorf("Analyze() with multiple targets error: %v", err)
	}

	if result == nil {
		t.Error("Analyze() should return result for multiple targets")
	}
}
