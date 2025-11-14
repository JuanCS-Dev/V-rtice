package diagnosticador

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/verticedev/vcli-go/internal/agents"
)

// ============================================================================
// INTEGRATION TESTS - These tests actually execute analysis
// ============================================================================

// setupTestGoProject creates a test Go project for analysis
func setupTestGoProject(t *testing.T) string {
	tmpDir := t.TempDir()

	// Create go.mod
	goMod := `module testproject

go 1.21
`
	if err := os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(goMod), 0644); err != nil {
		t.Fatalf("failed to create go.mod: %v", err)
	}

	// Create main.go
	mainGo := `package main

import (
	"fmt"
	"log"
)

func main() {
	fmt.Println("Hello, World!")
	processData([]int{1, 2, 3})
}

// processData processes a slice of integers
func processData(data []int) {
	for _, v := range data {
		log.Printf("Processing: %d\n", v)
	}
}

// Add performs addition
func Add(a, b int) int {
	return a + b
}

// Divide performs division (potential division by zero)
func Divide(a, b int) int {
	return a / b  // No error handling!
}
`
	if err := os.WriteFile(filepath.Join(tmpDir, "main.go"), []byte(mainGo), 0644); err != nil {
		t.Fatalf("failed to create main.go: %v", err)
	}

	// Create a test file
	testGo := `package main

import "testing"

func TestAdd(t *testing.T) {
	result := Add(2, 3)
	if result != 5 {
		t.Errorf("Add(2, 3) = %d; want 5", result)
	}
}
`
	if err := os.WriteFile(filepath.Join(tmpDir, "main_test.go"), []byte(testGo), 0644); err != nil {
		t.Fatalf("failed to create main_test.go: %v", err)
	}

	return tmpDir
}

// setupTestPythonProject creates a test Python project for analysis
func setupTestPythonProject(t *testing.T) string {
	tmpDir := t.TempDir()

	// Create main Python file
	mainPy := `#!/usr/bin/env python3
"""Main module for testing."""

def add(a, b):
    """Add two numbers."""
    return a + b

def divide(a, b):
    """Divide two numbers - no error handling!"""
    return a / b  # Potential division by zero

def process_data(data):
    """Process a list of data."""
    for item in data:
        print(f"Processing: {item}")

if __name__ == "__main__":
    print("Hello, World!")
    process_data([1, 2, 3])
`
	if err := os.WriteFile(filepath.Join(tmpDir, "main.py"), []byte(mainPy), 0644); err != nil {
		t.Fatalf("failed to create main.py: %v", err)
	}

	// Create test file
	testPy := `import unittest
from main import add

class TestMath(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == "__main__":
    unittest.main()
`
	if err := os.WriteFile(filepath.Join(tmpDir, "test_main.py"), []byte(testPy), 0644); err != nil {
		t.Fatalf("failed to create test_main.py: %v", err)
	}

	// Create requirements.txt
	requirements := `requests==2.28.0
flask==2.2.0
`
	if err := os.WriteFile(filepath.Join(tmpDir, "requirements.txt"), []byte(requirements), 0644); err != nil {
		t.Fatalf("failed to create requirements.txt: %v", err)
	}

	return tmpDir
}

// TestDiagnosticadorAgent_Execute_GoProject tests analysis of a Go project
func TestDiagnosticadorAgent_Execute_GoProject(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze Go project",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	// Verify output structure
	if output.Status != agents.StatusCompleted && output.Status != agents.StatusWaitingHITL {
		t.Errorf("unexpected status: %s", output.Status)
	}

	if output.AgentType != agents.AgentTypeDiagnosticador {
		t.Errorf("expected agent type Diagnosticador, got %s", output.AgentType)
	}

	// Check metrics
	if output.Metrics == nil {
		t.Fatal("expected metrics in output")
	}

	if _, exists := output.Metrics["lines_of_code"]; !exists {
		t.Error("expected lines_of_code metric")
	}

	// Check result
	if output.Result != nil {
		result, ok := output.Result.(*agents.DiagnosticResult)
		if ok {
			t.Logf("Analysis complete: %d LOC, %d security findings, %d performance issues",
				result.CodeQuality.LinesOfCode,
				len(result.SecurityFindings),
				len(result.PerformanceIssues))

			if result.Summary == "" {
				t.Error("expected summary in result")
			}
		}
	}

	t.Logf("Go project analysis duration: %v", output.Duration)
}

// TestDiagnosticadorAgent_Execute_PythonProject tests analysis of a Python project
func TestDiagnosticadorAgent_Execute_PythonProject(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestPythonProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze Python project",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	if output.Status != agents.StatusCompleted && output.Status != agents.StatusWaitingHITL {
		t.Errorf("unexpected status: %s", output.Status)
	}

	t.Logf("Python project analysis status: %s", output.Status)
}

// TestDiagnosticadorAgent_Execute_ClaudeCodeMode tests Claude Code integration
func TestDiagnosticadorAgent_Execute_ClaudeCodeMode(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	// Set Claude Code environment variable
	os.Setenv("CLAUDE_CODE", "true")
	defer os.Unsetenv("CLAUDE_CODE")

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze code in Claude Code mode",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	// In Claude Code mode, should return a prompt
	if output.ClaudePrompt == "" {
		t.Error("expected Claude prompt in output")
	}

	// Status should be WaitingHITL in Claude Code mode
	if output.Status != agents.StatusWaitingHITL {
		t.Logf("Note: Expected WaitingHITL status in Claude Code mode, got %s", output.Status)
	}

	t.Logf("Claude Code mode - prompt length: %d bytes", len(output.ClaudePrompt))
}

// TestDiagnosticadorAgent_Execute_VCLIMode tests vcli-go mode (non-Claude Code)
func TestDiagnosticadorAgent_Execute_VCLIMode(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	// Ensure we're in VCLI mode
	os.Unsetenv("CLAUDE_CODE")
	os.Setenv("VCLI_RUNTIME", "vcli-go")
	defer os.Unsetenv("VCLI_RUNTIME")

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze code in VCLI mode",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	// In VCLI mode, should use strategies
	if output.Result == nil {
		t.Error("expected result in output for VCLI mode")
	}

	t.Logf("VCLI mode analysis status: %s", output.Status)
}

// TestDiagnosticadorAgent_Execute_EmptyProject tests empty project handling
func TestDiagnosticadorAgent_Execute_EmptyProject(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := t.TempDir()

	// Create minimal structure
	os.WriteFile(filepath.Join(tmpDir, "empty.txt"), []byte(""), 0644)

	config := agents.AgentConfig{
		MinCoveragePercent:     0.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze empty project",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	// Should handle gracefully
	if err != nil {
		t.Logf("Execute error on empty project: %v", err)
	}

	if output != nil {
		t.Logf("Empty project analysis status: %s", output.Status)
	}
}

// TestDiagnosticadorAgent_Execute_MultipleTargets tests multiple target paths
func TestDiagnosticadorAgent_Execute_MultipleTargets(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir1 := setupTestGoProject(t)
	tmpDir2 := setupTestPythonProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     30.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze multiple targets",
		Targets: []string{tmpDir1, tmpDir2},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	t.Logf("Multiple targets analysis status: %s", output.Status)
}

// TestDiagnosticadorAgent_Execute_InvalidTarget tests error handling
func TestDiagnosticadorAgent_Execute_InvalidTarget(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	config := agents.AgentConfig{
		MaximusEurekaEndpoint: "http://localhost:8080",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze invalid target",
		Targets: []string{"/absolutely/nonexistent/path"},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	// Should error during validation or execution
	if err != nil {
		t.Logf("Expected error for invalid target: %v", err)
	}

	if output != nil && output.Status == agents.StatusFailed {
		t.Log("Agent properly failed on invalid target")
	}
}

// TestDiagnosticadorAgent_calculateMetrics_Integration tests metrics with real files
func TestDiagnosticadorAgent_calculateMetrics_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	agent := NewDiagnosticadorAgent(agents.AgentConfig{})
	result := &agents.DiagnosticResult{
		SecurityFindings:  make([]agents.SecurityFinding, 0),
		PerformanceIssues: make([]agents.PerformanceIssue, 0),
		Recommendations:   make([]string, 0),
	}

	err := agent.calculateMetrics([]string{tmpDir}, result)

	if err != nil {
		t.Fatalf("calculateMetrics failed: %v", err)
	}

	if result.CodeQuality.LinesOfCode == 0 {
		t.Error("expected lines of code to be counted")
	}

	t.Logf("Calculated metrics: %d LOC, %.1f maintainability",
		result.CodeQuality.LinesOfCode,
		result.CodeQuality.MaintainabilityIndex)
}

// TestDiagnosticadorAgent_Execute_WithStrategyError tests error handling in strategies
func TestDiagnosticadorAgent_Execute_WithStrategyError(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Create a project that might cause strategy errors
	tmpDir := t.TempDir()

	// Create an invalid Go file
	invalidGo := `package broken

this is not valid go code!
`
	os.WriteFile(filepath.Join(tmpDir, "broken.go"), []byte(invalidGo), 0644)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze broken code",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	// Should handle errors gracefully
	if err != nil {
		t.Logf("Execute error on broken code (expected): %v", err)
	}

	if output != nil {
		t.Logf("Analysis status for broken code: %s", output.Status)

		if len(output.Errors) > 0 {
			t.Logf("Errors captured: %v", output.Errors)
		}
	}
}

// TestDiagnosticadorAgent_Execute_NextAgent tests next agent determination
func TestDiagnosticadorAgent_Execute_NextAgent(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze and determine next agent",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	// Should determine next agent based on findings
	if output.NextAgent != "" {
		t.Logf("Next agent determined: %s", output.NextAgent)

		// Validate it's a known agent type
		validAgents := []agents.AgentType{
			agents.AgentTypeArquiteto,
			agents.AgentTypeDevSenior,
		}

		found := false
		for _, validAgent := range validAgents {
			if output.NextAgent == validAgent {
				found = true
				break
			}
		}

		if !found {
			t.Errorf("unexpected next agent: %s", output.NextAgent)
		}
	}
}

// TestDiagnosticadorAgent_Execute_ContextCancellation tests context handling
func TestDiagnosticadorAgent_Execute_ContextCancellation(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MaximusEurekaEndpoint: "http://localhost:8080",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze with cancelled context",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	// Create and immediately cancel context
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	output, err := agent.Execute(ctx, input)

	// Should handle cancellation gracefully
	if err != nil {
		t.Logf("Execute error with cancelled context: %v", err)
	}

	if output != nil {
		t.Logf("Output status: %s", output.Status)
	}
}

// TestDiagnosticadorAgent_Execute_Metadata tests metadata population
func TestDiagnosticadorAgent_Execute_Metadata(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusEurekaEndpoint:  "http://localhost:8080",
		AuthToken:              "test-token",
	}
	agent := NewDiagnosticadorAgent(config)

	input := agents.AgentInput{
		Task:    "Analyze and check metadata",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	// Check metadata
	if output.Metadata == nil {
		t.Fatal("expected metadata in output")
	}

	if _, exists := output.Metadata["detected_language"]; !exists {
		t.Error("expected detected_language in metadata")
	}

	if _, exists := output.Metadata["language_confidence"]; !exists {
		t.Error("expected language_confidence in metadata")
	}

	t.Logf("Metadata: %+v", output.Metadata)
}
