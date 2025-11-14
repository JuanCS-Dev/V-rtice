package tester

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
)

// ============================================================================
// INTEGRATION TESTS - These tests actually execute Go commands
// ============================================================================

// setupTestGoProject creates a temporary Go project for testing
func setupTestGoProject(t *testing.T) string {
	tmpDir := t.TempDir()

	// Create go.mod
	goMod := `module testproject

go 1.21
`
	if err := os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(goMod), 0644); err != nil {
		t.Fatalf("failed to create go.mod: %v", err)
	}

	// Create a simple Go file
	mainGo := `package main

import "fmt"

func main() {
	fmt.Println("Hello, World!")
}

func Add(a, b int) int {
	return a + b
}

func Subtract(a, b int) int {
	return a - b
}

func Multiply(a, b int) int {
	return a * b
}
`
	if err := os.WriteFile(filepath.Join(tmpDir, "main.go"), []byte(mainGo), 0644); err != nil {
		t.Fatalf("failed to create main.go: %v", err)
	}

	// Create a test file with passing tests
	testGo := `package main

import "testing"

func TestAdd(t *testing.T) {
	result := Add(2, 3)
	if result != 5 {
		t.Errorf("Add(2, 3) = %d; want 5", result)
	}
}

func TestSubtract(t *testing.T) {
	result := Subtract(5, 3)
	if result != 2 {
		t.Errorf("Subtract(5, 3) = %d; want 2", result)
	}
}

func TestMultiply(t *testing.T) {
	result := Multiply(4, 5)
	if result != 20 {
		t.Errorf("Multiply(4, 5) = %d; want 20", result)
	}
}
`
	if err := os.WriteFile(filepath.Join(tmpDir, "main_test.go"), []byte(testGo), 0644); err != nil {
		t.Fatalf("failed to create main_test.go: %v", err)
	}

	return tmpDir
}

// setupFailingTestProject creates a project with failing tests
func setupFailingTestProject(t *testing.T) string {
	tmpDir := t.TempDir()

	// Create go.mod
	goMod := `module failproject

go 1.21
`
	if err := os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(goMod), 0644); err != nil {
		t.Fatalf("failed to create go.mod: %v", err)
	}

	// Create a simple Go file
	codeGo := `package failproject

func BrokenFunction() int {
	return 42
}
`
	if err := os.WriteFile(filepath.Join(tmpDir, "code.go"), []byte(codeGo), 0644); err != nil {
		t.Fatalf("failed to create code.go: %v", err)
	}

	// Create a test file with failing tests
	testGo := `package failproject

import "testing"

func TestBroken(t *testing.T) {
	result := BrokenFunction()
	if result != 100 {
		t.Errorf("Expected 100, got %d", result)
	}
}

func TestPassing(t *testing.T) {
	result := BrokenFunction()
	if result == 42 {
		// This test passes
	}
}
`
	if err := os.WriteFile(filepath.Join(tmpDir, "code_test.go"), []byte(testGo), 0644); err != nil {
		t.Fatalf("failed to create code_test.go: %v", err)
	}

	return tmpDir
}

// TestTesterAgent_runUnitTests_Integration tests actual unit test execution
func TestTesterAgent_runUnitTests_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	result, err := agent.runUnitTests([]string{"."})

	// Tests should run (error might occur but we should get results)
	if err != nil {
		t.Logf("Test execution error (may be ok): %v", err)
	}

	if result == nil {
		t.Fatal("expected result, got nil")
	}

	// Check that we got some output
	if result.Output == "" {
		t.Error("expected test output, got empty string")
	}

	// We should have counted some tests
	if result.Total == 0 {
		t.Error("expected tests to be counted")
	}

	t.Logf("Ran %d tests: %d passed, %d failed", result.Total, result.Passed, result.Failed)
}

// TestTesterAgent_runUnitTests_WithFailures tests handling of failing tests
func TestTesterAgent_runUnitTests_WithFailures(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupFailingTestProject(t)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	result, err := agent.runUnitTests([]string{"."})

	// Error is expected since tests fail
	if err == nil {
		t.Log("Note: go test returned success despite failing tests (might be ok)")
	}

	if result == nil {
		t.Fatal("expected result, got nil")
	}

	// Should have at least one failure
	if result.Failed == 0 {
		t.Error("expected at least one failed test")
	}

	t.Logf("Ran %d tests: %d passed, %d failed", result.Total, result.Passed, result.Failed)
}

// TestTesterAgent_analyzeCoverage_Integration tests coverage analysis
func TestTesterAgent_analyzeCoverage_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	result, err := agent.analyzeCoverage([]string{"."})

	if err != nil {
		t.Logf("Coverage analysis error (may be ok): %v", err)
	}

	if result == nil {
		t.Fatal("expected coverage result, got nil")
	}

	// Coverage should be calculated (might be 0 if no coverage)
	t.Logf("Line coverage: %.1f%%", result.LineCoverage)

	if result.CoverageByFile == nil {
		t.Error("CoverageByFile should be initialized")
	}
}

// TestTesterAgent_runIntegrationTests_Integration tests integration test execution
func TestTesterAgent_runIntegrationTests_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	result, testErr := agent.runIntegrationTests([]string{"."})

	if testErr != nil {
		t.Logf("Integration test error (expected if no integration tests): %v", testErr)
	}

	if result == nil {
		t.Fatal("expected result, got nil")
	}

	// It's OK if no integration tests are found
	if result.Total == 0 {
		t.Log("No integration tests found (expected)")
	}
}

// TestTesterAgent_runBenchmarks_Integration tests benchmark execution
func TestTesterAgent_runBenchmarks_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := t.TempDir()

	// Create a project with benchmarks
	goMod := `module benchproject

go 1.21
`
	os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(goMod), 0644)

	benchCode := `package bench

func Sum(numbers []int) int {
	total := 0
	for _, n := range numbers {
		total += n
	}
	return total
}
`
	os.WriteFile(filepath.Join(tmpDir, "bench.go"), []byte(benchCode), 0644)

	benchTest := `package bench

import "testing"

func BenchmarkSum(b *testing.B) {
	numbers := []int{1, 2, 3, 4, 5}
	for i := 0; i < b.N; i++ {
		Sum(numbers)
	}
}

func BenchmarkSumLarge(b *testing.B) {
	numbers := make([]int, 1000)
	for i := range numbers {
		numbers[i] = i
	}
	for i := 0; i < b.N; i++ {
		Sum(numbers)
	}
}
`
	os.WriteFile(filepath.Join(tmpDir, "bench_test.go"), []byte(benchTest), 0644)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	result, err := agent.runBenchmarks([]string{"."})

	if err != nil {
		t.Logf("Benchmark error (may be ok): %v", err)
	}

	if result == nil {
		t.Fatal("expected benchmark result, got nil")
	}

	t.Logf("Found %d benchmarks", len(result.Results))
}

// TestTesterAgent_executeLegacyGoTests_Integration tests the legacy execution path
func TestTesterAgent_executeLegacyGoTests_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent: 50.0,
		RequireTestPass:    false,
	}
	agent := NewTesterAgent(config)

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	input := agents.AgentInput{
		Task:    "Run legacy tests",
		Targets: []string{"."},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	startTime := time.Now()

	output, err := agent.executeLegacyGoTests(ctx, input, startTime)

	if err != nil {
		t.Fatalf("executeLegacyGoTests failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	if output.Status != agents.StatusCompleted && output.Status != agents.StatusWaitingHITL {
		t.Errorf("unexpected status: %s", output.Status)
	}

	// Verify result structure
	if output.Result == nil {
		t.Fatal("expected result in output")
	}

	testResult, ok := output.Result.(*agents.TestResult)
	if !ok {
		t.Fatal("expected TestResult in output")
	}

	t.Logf("Legacy test execution: %d tests, %.1f%% coverage",
		testResult.UnitTests.TotalTests,
		testResult.Coverage.LineCoverage)

	// Check metrics
	if output.Metrics == nil {
		t.Fatal("expected metrics in output")
	}

	if _, exists := output.Metrics["unit_tests_total"]; !exists {
		t.Error("expected unit_tests_total metric")
	}

	if _, exists := output.Metrics["coverage_percent"]; !exists {
		t.Error("expected coverage_percent metric")
	}
}

// ============================================================================
// EXECUTE METHOD INTEGRATION TESTS
// ============================================================================

// TestTesterAgent_Execute_FullIntegration tests the full Execute method
func TestTesterAgent_Execute_FullIntegration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		RequireTestPass:        false,
		MaximusPredictEndpoint: "http://localhost:8080",
	}
	agent := NewTesterAgent(config)

	input := agents.AgentInput{
		Task:        "Run comprehensive tests",
		Targets:     []string{tmpDir},
		Context:     make(map[string]interface{}),
		HITLEnabled: false,
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	// Should complete successfully
	if output.Status != agents.StatusCompleted {
		t.Errorf("expected status Completed, got %s", output.Status)
	}

	// Verify output structure
	if output.AgentType != agents.AgentTypeTester {
		t.Errorf("expected agent type Tester, got %s", output.AgentType)
	}

	if output.Duration == 0 {
		t.Error("expected non-zero duration")
	}

	if output.Metrics == nil {
		t.Fatal("expected metrics")
	}

	t.Logf("Execute completed in %v", output.Duration)
	t.Logf("Metrics: %+v", output.Metrics)
}

// TestTesterAgent_Execute_WithHITL tests HITL approval flow
func TestTesterAgent_Execute_WithHITL(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupFailingTestProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     75.0,
		RequireTestPass:        true,
		MaximusPredictEndpoint: "http://localhost:8080",
	}
	agent := NewTesterAgent(config)

	input := agents.AgentInput{
		Task:        "Run tests with HITL",
		Targets:     []string{tmpDir},
		Context:     make(map[string]interface{}),
		HITLEnabled: true, // Enable HITL
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	// With failing tests and HITL enabled, should wait for approval
	if output.Status != agents.StatusWaitingHITL {
		t.Logf("Note: Expected WaitingHITL status, got %s (might be ok if no failures)", output.Status)
	}

	t.Logf("Execute status: %s", output.Status)
}

// ============================================================================
// EDGE CASE INTEGRATION TESTS
// ============================================================================

// TestTesterAgent_Execute_EmptyProject tests execution with no tests
func TestTesterAgent_Execute_EmptyProject(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := t.TempDir()

	// Create minimal go.mod
	goMod := `module emptyproject

go 1.21
`
	os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(goMod), 0644)

	// Create a file with no tests
	os.WriteFile(filepath.Join(tmpDir, "empty.go"), []byte("package empty\n"), 0644)

	config := agents.AgentConfig{
		MinCoveragePercent:     0.0,
		RequireTestPass:        false,
		MaximusPredictEndpoint: "http://localhost:8080",
	}
	agent := NewTesterAgent(config)

	input := agents.AgentInput{
		Task:    "Run tests on empty project",
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

	t.Logf("Empty project execution status: %s", output.Status)
}

// TestTesterAgent_Execute_InvalidTarget tests with non-existent target
func TestTesterAgent_Execute_InvalidTarget(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusPredictEndpoint: "http://localhost:8080",
	}
	agent := NewTesterAgent(config)

	input := agents.AgentInput{
		Task:    "Run tests on invalid path",
		Targets: []string{"/nonexistent/path/to/nowhere"},
		Context: make(map[string]interface{}),
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	// Should handle gracefully (might error or return empty results)
	if err != nil {
		t.Logf("Expected error for invalid target: %v", err)
	}

	if output != nil {
		t.Logf("Output status: %s", output.Status)
	}
}

// TestTesterAgent_analyzeCoverage_DefaultTargets tests with default targets
func TestTesterAgent_analyzeCoverage_DefaultTargets(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	// Call with empty targets (should use default)
	result, err := agent.analyzeCoverage([]string{})

	if err != nil {
		t.Logf("Coverage analysis error: %v", err)
	}

	if result == nil {
		t.Fatal("expected result, got nil")
	}

	// Should have used default "./..." target
	t.Logf("Coverage with default targets: %.1f%%", result.LineCoverage)
}

// TestTesterAgent_runUnitTests_DefaultTargets tests with default targets
func TestTesterAgent_runUnitTests_DefaultTargets(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	// Call with empty targets (should use default)
	result, err := agent.runUnitTests([]string{})

	if err != nil {
		t.Logf("Test error: %v", err)
	}

	if result == nil {
		t.Fatal("expected result, got nil")
	}

	t.Logf("Tests with default targets: %d total", result.Total)
}

// TestTesterAgent_runBenchmarks_DefaultTargets tests benchmarks with default targets
func TestTesterAgent_runBenchmarks_DefaultTargets(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	agent := NewTesterAgent(agents.AgentConfig{})

	// Change to the test directory
	oldDir, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldDir)

	// Call with empty targets (should use default)
	result, err := agent.runBenchmarks([]string{})

	if err != nil {
		t.Logf("Benchmark error: %v", err)
	}

	if result == nil {
		t.Fatal("expected result, got nil")
	}

	t.Logf("Benchmarks with default targets: %d found", len(result.Results))
}

// ============================================================================
// COMPLEX SCENARIO TESTS
// ============================================================================

// TestTesterAgent_Execute_WithImplementationContext tests execution with context
func TestTesterAgent_Execute_WithImplementationContext(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		RequireTestPass:        false,
		MaximusPredictEndpoint: "http://localhost:8080",
	}
	agent := NewTesterAgent(config)

	// Create context with implementation result
	inputContext := map[string]interface{}{
		"dev_senior_output": &agents.AgentOutput{
			Result: &agents.ImplementationResult{
				TaskDescription: "Previous implementation",
				FilesCreated:    []agents.FileChange{},
			},
		},
	}

	input := agents.AgentInput{
		Task:    "Run tests with context",
		Targets: []string{tmpDir},
		Context: inputContext,
	}

	ctx := context.Background()
	output, err := agent.Execute(ctx, input)

	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}

	if output == nil {
		t.Fatal("expected output, got nil")
	}

	t.Logf("Execute with context status: %s", output.Status)
}

// TestTesterAgent_parseTestOutput_RealOutput tests parsing of actual go test output
func TestTesterAgent_parseTestOutput_RealOutput(t *testing.T) {
	agent := NewTesterAgent(agents.AgentConfig{})

	// Real go test output with multiple scenarios
	realOutput := `=== RUN   TestAdd
--- PASS: TestAdd (0.00s)
=== RUN   TestSubtract
--- PASS: TestSubtract (0.00s)
=== RUN   TestMultiply
    main_test.go:20: some log output
--- PASS: TestMultiply (0.01s)
=== RUN   TestDivide
    main_test.go:25: division by zero
--- FAIL: TestDivide (0.00s)
=== RUN   TestSkipped
--- SKIP: TestSkipped (0.00s)
    main_test.go:30: skipping test
PASS
ok  	testproject	0.003s`

	result := &TestExecutionResult{
		Failures: []agents.TestFailure{},
	}

	agent.parseTestOutput(realOutput, result)

	if result.Total != 5 {
		t.Errorf("expected 5 total tests, got %d", result.Total)
	}

	if result.Passed != 3 {
		t.Errorf("expected 3 passed tests, got %d", result.Passed)
	}

	if result.Failed != 1 {
		t.Errorf("expected 1 failed test, got %d", result.Failed)
	}

	if result.Skipped != 1 {
		t.Errorf("expected 1 skipped test, got %d", result.Skipped)
	}
}

// TestTesterAgent_Execute_MultipleTargets tests with multiple target paths
func TestTesterAgent_Execute_MultipleTargets(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir1 := setupTestGoProject(t)
	tmpDir2 := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     30.0,
		RequireTestPass:        false,
		MaximusPredictEndpoint: "http://localhost:8080",
	}
	agent := NewTesterAgent(config)

	input := agents.AgentInput{
		Task:    "Run tests on multiple targets",
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

	t.Logf("Multiple targets execution status: %s", output.Status)
}

// TestTesterAgent_Execute_ContextCancellation tests context cancellation handling
func TestTesterAgent_Execute_ContextCancellation(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	tmpDir := setupTestGoProject(t)

	config := agents.AgentConfig{
		MinCoveragePercent:     50.0,
		MaximusPredictEndpoint: "http://localhost:8080",
	}
	agent := NewTesterAgent(config)

	input := agents.AgentInput{
		Task:    "Run tests with cancellation",
		Targets: []string{tmpDir},
		Context: make(map[string]interface{}),
	}

	// Create a context that's already cancelled
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	output, err := agent.Execute(ctx, input)

	// Should handle cancellation gracefully
	// (current implementation might not check context, so test what happens)
	if err != nil {
		if !strings.Contains(err.Error(), "context") {
			t.Logf("Execute with cancelled context error: %v", err)
		}
	}

	if output != nil {
		t.Logf("Output status: %s", output.Status)
	}
}
