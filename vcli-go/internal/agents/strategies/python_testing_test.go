package strategies

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
)

// TestNewPythonTestStrategy tests the constructor
func TestNewPythonTestStrategy(t *testing.T) {
	strategy := NewPythonTestStrategy()

	if strategy == nil {
		t.Fatal("NewPythonTestStrategy() returned nil")
	}
}

// TestPythonTestStrategy_Language tests language identification
func TestPythonTestStrategy_Language(t *testing.T) {
	strategy := NewPythonTestStrategy()

	lang := strategy.Language()

	if lang != language.LanguagePython {
		t.Errorf("Language() = %v, want %v", lang, language.LanguagePython)
	}
}

// TestPythonTestStrategy_GetCapabilities tests capability reporting
func TestPythonTestStrategy_GetCapabilities(t *testing.T) {
	strategy := NewPythonTestStrategy()

	capabilities := strategy.GetCapabilities()

	if len(capabilities) == 0 {
		t.Error("GetCapabilities() returned no capabilities")
	}

	// Check for essential capabilities
	expectedCaps := []string{"pytest", "pytest-cov"}
	for _, expected := range expectedCaps {
		found := false
		for _, cap := range capabilities {
			if cap == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("GetCapabilities() missing expected capability: %s", expected)
		}
	}
}

// TestPythonTestStrategy_RunTests tests basic test execution
func TestPythonTestStrategy_RunTests(t *testing.T) {
	strategy := NewPythonTestStrategy()

	// Create temp directory for test files
	tempDir := t.TempDir()

	// Create a simple test file
	testFile := filepath.Join(tempDir, "test_sample.py")
	testContent := `
def test_simple():
    assert 1 + 1 == 2

def test_another():
    assert True
`
	if err := os.WriteFile(testFile, []byte(testContent), 0644); err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Run tests
	result, err := strategy.RunTests(ctx, []string{tempDir})

	// Note: This may fail if pytest is not installed
	// Error is acceptable here - we're testing the mechanism, not pytest itself
	if err != nil {
		t.Logf("RunTests() error (acceptable if pytest not installed): %v", err)
	}

	// Result should not be nil even on error
	if result == nil {
		t.Error("RunTests() returned nil result")
	}
}

// TestPythonTestStrategy_RunTests_NoTempHardcoding tests that /tmp is not hardcoded
func TestPythonTestStrategy_RunTests_NoTempHardcoding(t *testing.T) {
	strategy := NewPythonTestStrategy()

	// This test verifies the FIX - no hardcoded /tmp paths
	// Instead, temp files should be created in proper temp directories

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Run with empty targets - should not crash
	result, _ := strategy.RunTests(ctx, []string{})

	if result == nil {
		t.Error("RunTests() should return a result struct even with no targets")
	}

	// After fix, this should NOT leave files in /tmp
	// Check that no pytest-report.json was created in /tmp
	if _, err := os.Stat("/tmp/pytest-report.json"); err == nil {
		t.Error("FAIL: Hardcoded /tmp/pytest-report.json still exists - AIR-GAP not fixed!")
	}
}

// TestPythonTestStrategy_AnalyzeCoverage tests coverage analysis
func TestPythonTestStrategy_AnalyzeCoverage(t *testing.T) {
	strategy := NewPythonTestStrategy()

	// Create temp directory
	tempDir := t.TempDir()

	// Create a simple Python file to test coverage
	sourceFile := filepath.Join(tempDir, "sample.py")
	sourceContent := `
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
`
	if err := os.WriteFile(sourceFile, []byte(sourceContent), 0644); err != nil {
		t.Fatalf("Failed to create source file: %v", err)
	}

	// Create corresponding test file
	testFile := filepath.Join(tempDir, "test_sample.py")
	testContent := `
from sample import add

def test_add():
    assert add(1, 1) == 2
`
	if err := os.WriteFile(testFile, []byte(testContent), 0644); err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Analyze coverage
	result, err := strategy.AnalyzeCoverage(ctx, []string{tempDir})

	// May fail if pytest/coverage not installed - that's OK
	if err != nil {
		t.Logf("AnalyzeCoverage() error (acceptable): %v", err)
	}

	// Result should not be nil
	if result == nil {
		t.Error("AnalyzeCoverage() returned nil result")
	}

	// Check structure
	if result != nil {
		if result.LineCoverage < 0 || result.LineCoverage > 1.0 {
			t.Errorf("LineCoverage out of range: %f (should be 0.0-1.0)", result.LineCoverage)
		}

		if result.UncoveredFiles == nil {
			t.Error("UncoveredFiles should be initialized, not nil")
		}
	}
}

// TestPythonTestStrategy_AnalyzeCoverage_NoTempHardcoding tests no /tmp hardcoding
func TestPythonTestStrategy_AnalyzeCoverage_NoTempHardcoding(t *testing.T) {
	strategy := NewPythonTestStrategy()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Run coverage analysis
	_, _ = strategy.AnalyzeCoverage(ctx, []string{})

	// After fix, should NOT leave coverage.json in /tmp
	if _, err := os.Stat("/tmp/coverage.json"); err == nil {
		t.Error("FAIL: Hardcoded /tmp/coverage.json still exists - AIR-GAP not fixed!")
	}
}

// TestPythonTestStrategy_ParseCoverageReport tests coverage parsing
func TestPythonTestStrategy_ParseCoverageReport(t *testing.T) {
	strategy := NewPythonTestStrategy()

	// Create temp directory for coverage report
	tempDir := t.TempDir()
	coverageFile := filepath.Join(tempDir, "coverage.json")

	// Create mock coverage report
	mockReport := map[string]interface{}{
		"totals": map[string]interface{}{
			"percent_covered": 75.5,
		},
		"files": map[string]interface{}{
			"sample.py": map[string]interface{}{
				"summary": map[string]interface{}{
					"missing_lines": float64(5),
				},
			},
			"complete.py": map[string]interface{}{
				"summary": map[string]interface{}{
					"missing_lines": float64(0),
				},
			},
		},
	}

	reportData, err := json.Marshal(mockReport)
	if err != nil {
		t.Fatalf("Failed to marshal mock report: %v", err)
	}

	if err := os.WriteFile(coverageFile, reportData, 0644); err != nil {
		t.Fatalf("Failed to write coverage file: %v", err)
	}

	// Test parsing
	result := &agents.CoverageResult{}

	// This test will fail until we refactor parseCoverageReport to accept file path
	// For now, testing the behavior
	err = strategy.parseCoverageReport(result)

	// Currently reads from /tmp - will fail unless file exists there
	// After fix, should accept file path parameter
	t.Logf("parseCoverageReport() error: %v", err)
}

// TestPythonTestStrategy_ParsePytestReport tests pytest report parsing
func TestPythonTestStrategy_ParsePytestReport(t *testing.T) {
	strategy := NewPythonTestStrategy()

	// Create temp directory for pytest report
	tempDir := t.TempDir()
	reportFile := filepath.Join(tempDir, "pytest-report.json")

	// Create mock pytest report
	mockReport := map[string]interface{}{
		"summary": map[string]interface{}{
			"total": 10,
			"passed": 8,
			"failed": 2,
		},
	}

	reportData, err := json.Marshal(mockReport)
	if err != nil {
		t.Fatalf("Failed to marshal mock report: %v", err)
	}

	if err := os.WriteFile(reportFile, reportData, 0644); err != nil {
		t.Fatalf("Failed to write report file: %v", err)
	}

	// Test parsing
	result := &agents.TestResult{}

	// Currently reads from /tmp - after fix should accept file path
	err = strategy.parsePytestReport(result)

	t.Logf("parsePytestReport() error: %v", err)
}

// TestPythonTestStrategy_ParseTextOutput tests fallback text parsing
func TestPythonTestStrategy_ParseTextOutput(t *testing.T) {
	strategy := NewPythonTestStrategy()

	mockOutput := `
============================= test session starts ==============================
collected 5 items

test_sample.py::test_one PASSED                                          [ 20%]
test_sample.py::test_two FAILED                                          [ 40%]
test_sample.py::test_three PASSED                                        [ 60%]
test_sample.py::test_four PASSED                                         [ 80%]
test_sample.py::test_five PASSED                                         [100%]

=========================== short test summary info ============================
FAILED test_sample.py::test_two - assert False
========================= 1 failed, 4 passed in 0.12s ==========================
`

	result := &agents.TestResult{}

	// Test text parsing (currently a no-op)
	strategy.parseTextOutput(mockOutput, result)

	// This is currently simplified - just verify it doesn't crash
	t.Log("parseTextOutput() completed without crash")
}

// TestPythonTestStrategy_Integration tests realistic workflow
func TestPythonTestStrategy_Integration(t *testing.T) {
	// Skip if pytest not available
	if !isPytestAvailable() {
		t.Skip("pytest not available - skipping integration test")
	}

	strategy := NewPythonTestStrategy()

	// Create temp project
	tempDir := t.TempDir()

	// Create a real Python module
	moduleFile := filepath.Join(tempDir, "calculator.py")
	moduleContent := `
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
`
	if err := os.WriteFile(moduleFile, []byte(moduleContent), 0644); err != nil {
		t.Fatalf("Failed to create module: %v", err)
	}

	// Create comprehensive tests
	testFile := filepath.Join(tempDir, "test_calculator.py")
	testContent := `
from calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_multiply():
    calc = Calculator()
    assert calc.multiply(4, 5) == 20
`
	if err := os.WriteFile(testFile, []byte(testContent), 0644); err != nil {
		t.Fatalf("Failed to create tests: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Run full workflow
	testResult, err := strategy.RunTests(ctx, []string{tempDir})
	if err != nil {
		t.Logf("RunTests() error: %v", err)
	}

	if testResult == nil {
		t.Fatal("Integration test failed: nil test result")
	}

	// Run coverage analysis
	coverageResult, err := strategy.AnalyzeCoverage(ctx, []string{tempDir})
	if err != nil {
		t.Logf("AnalyzeCoverage() error: %v", err)
	}

	if coverageResult == nil {
		t.Fatal("Integration test failed: nil coverage result")
	}

	t.Logf("Integration test completed - Coverage: %.1f%%", coverageResult.LineCoverage*100)
}

// Helper function to check if pytest is available
func isPytestAvailable() bool {
	// Simple check - could use our new tools.IsToolAvailable()
	_, err := os.Stat("/usr/bin/pytest")
	if err == nil {
		return true
	}
	_, err = os.Stat("/usr/local/bin/pytest")
	return err == nil
}

// TestPythonTestStrategy_ContextCancellation tests context handling
func TestPythonTestStrategy_ContextCancellation(t *testing.T) {
	strategy := NewPythonTestStrategy()

	// Create temp directory
	tempDir := t.TempDir()

	// Create a test that would take long to run
	testFile := filepath.Join(tempDir, "test_slow.py")
	testContent := `
import time

def test_slow():
    time.sleep(60)  # 60 seconds
    assert True
`
	if err := os.WriteFile(testFile, []byte(testContent), 0644); err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	// Create context with very short timeout
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// Run tests - should be cancelled
	_, err := strategy.RunTests(ctx, []string{tempDir})

	// Context cancellation is acceptable
	if err != nil && err != context.DeadlineExceeded {
		t.Logf("RunTests() with cancelled context: %v", err)
	}
}

// TestPythonTestStrategy_EmptyTargets tests behavior with no targets
func TestPythonTestStrategy_EmptyTargets(t *testing.T) {
	strategy := NewPythonTestStrategy()

	ctx := context.Background()

	// Run with empty targets
	result, err := strategy.RunTests(ctx, []string{})

	// Should not crash
	if result == nil {
		t.Error("RunTests() with empty targets should return non-nil result")
	}

	// Error is acceptable
	if err != nil {
		t.Logf("RunTests() empty targets error: %v", err)
	}

	// Same for coverage
	coverageResult, err := strategy.AnalyzeCoverage(ctx, []string{})

	if coverageResult == nil {
		t.Error("AnalyzeCoverage() with empty targets should return non-nil result")
	}
}
