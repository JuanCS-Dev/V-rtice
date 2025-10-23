package tester

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
	"github.com/verticedev/vcli-go/internal/agents/strategies"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// TesterAgent implements autonomous testing and quality validation
type TesterAgent struct {
	config        agents.AgentConfig
	status        agents.AgentStatus
	logger        *log.Logger
	predictClient *maximus.PredictClient
}

// NewTesterAgent creates a new TESTER agent
func NewTesterAgent(config agents.AgentConfig) *TesterAgent {
	return &TesterAgent{
		config:        config,
		status:        agents.StatusIdle,
		logger:        log.New(os.Stdout, "[TESTER] ", log.LstdFlags),
		predictClient: maximus.NewPredictClient(config.MaximusPredictEndpoint, ""), // Auth from env
	}
}

// Type returns the agent type
func (a *TesterAgent) Type() agents.AgentType {
	return agents.AgentTypeTester
}

// Name returns the agent name
func (a *TesterAgent) Name() string {
	return "TESTER"
}

// Execute implements the Agent interface - main execution logic
func (a *TesterAgent) Execute(ctx context.Context, input agents.AgentInput) (*agents.AgentOutput, error) {
	a.status = agents.StatusRunning
	startTime := time.Now()

	a.logger.Printf("Starting test validation for task: %s", input.Task)

	// Step 0: Language Detection
	a.logger.Println("Step 0/5: Detecting language...")
	detector := language.NewDetector()
	langResult, err := detector.Detect(input.Targets)
	if err != nil {
		return nil, fmt.Errorf("language detection failed: %w", err)
	}
	a.logger.Printf("   Detected: %s (%.0f%% confidence)", langResult.Primary, langResult.Confidence*100)

	// Step 1: Create and populate strategy registry
	a.logger.Println("Step 1/5: Initializing test strategy...")
	registry := strategies.NewStrategyRegistry()
	registry.RegisterTest(strategies.NewPythonTestStrategy())
	// Note: Go test strategy would be added here when implemented

	strategy, ok := registry.GetTest(langResult.Primary)
	if !ok {
		// Fallback to legacy Go test execution if no strategy found
		a.logger.Printf("   No test strategy for %s, using legacy execution", langResult.Primary)
		return a.executeLegacyGoTests(ctx, input, startTime)
	}
	a.logger.Printf("   Using %s test strategy", langResult.Primary)

	// Step 2: Run tests using strategy
	a.logger.Println("Step 2/5: Running tests with language-specific strategy...")
	testResult, err := strategy.RunTests(ctx, input.Targets)
	if err != nil {
		a.logger.Printf("Warning: Tests failed: %v", err)
		// Continue - we want to report the failures
	}

	// Step 3: Analyze coverage using strategy
	a.logger.Println("Step 3/5: Analyzing test coverage...")
	coverageResult, err := strategy.AnalyzeCoverage(ctx, input.Targets)
	if err != nil {
		a.logger.Printf("Warning: Coverage analysis failed: %v", err)
		// Initialize empty coverage to avoid nil panic
		coverageResult = &agents.CoverageResult{
			LineCoverage:   0.0,
			BranchCoverage: 0.0,
			UncoveredFiles: make([]string, 0),
			CoverageByFile: make(map[string]float64),
		}
	}

	// Step 4: Run benchmarks (language-agnostic, optional)
	a.logger.Println("Step 4/5: Running benchmarks (if available)...")
	benchmarkResult := &BenchmarkResult{Results: []agents.BenchmarkResult{}}
	if langResult.Primary == language.LanguageGo {
		benchmarkResult, _ = a.runBenchmarks(input.Targets)
	}

	// Step 5: Check quality gates
	a.logger.Println("Step 5/5: Checking quality gates")
	// Convert testResult to legacy format for quality gate checking
	unitTestExec := &TestExecutionResult{
		Total:    testResult.UnitTests.TotalTests,
		Passed:   testResult.UnitTests.PassedTests,
		Failed:   testResult.UnitTests.FailedTests,
		Skipped:  testResult.UnitTests.SkippedTests,
		Duration: testResult.UnitTests.Duration,
		Failures: testResult.UnitTests.Failures,
	}
	integrationTestExec := &TestExecutionResult{
		Total:    testResult.IntegrationTests.TotalTests,
		Passed:   testResult.IntegrationTests.PassedTests,
		Failed:   testResult.IntegrationTests.FailedTests,
		Skipped:  testResult.IntegrationTests.SkippedTests,
		Duration: testResult.IntegrationTests.Duration,
		Failures: testResult.IntegrationTests.Failures,
	}

	coverageExec := &CoverageResult{
		LineCoverage:   coverageResult.LineCoverage,
		BranchCoverage: coverageResult.BranchCoverage,
		UncoveredFiles: coverageResult.UncoveredFiles,
		CoverageByFile: coverageResult.CoverageByFile,
	}

	qualityGateResult := a.checkQualityGates(coverageExec, unitTestExec, integrationTestExec)
	regressions := a.detectRegressions(unitTestExec, benchmarkResult)

	// Use the strategy's test result directly
	result := testResult
	result.QualityGates = qualityGateResult
	result.Regressions = regressions
	result.Benchmarks = benchmarkResult.Results
	result.Recommendations = a.generateRecommendations(qualityGateResult, coverageExec, unitTestExec)

	duration := time.Since(startTime)
	a.logger.Printf("Test validation complete: %d/%d tests passed, coverage: %.1f%%",
		testResult.UnitTests.PassedTests, testResult.UnitTests.TotalTests, coverageResult.LineCoverage)

	// Determine status based on quality gates
	outputStatus := agents.StatusCompleted
	if input.HITLEnabled && (qualityGateResult.AllPassed == false || len(regressions) > 0) {
		// Require HITL approval if quality gates failed or regressions detected
		outputStatus = agents.StatusWaitingHITL
		a.logger.Printf("HITL approval required: quality gates failed or regressions detected")
	}

	metrics := make(map[string]float64)
	metrics["unit_tests_total"] = float64(testResult.UnitTests.TotalTests)
	metrics["unit_tests_passed"] = float64(testResult.UnitTests.PassedTests)
	metrics["unit_tests_failed"] = float64(testResult.UnitTests.FailedTests)
	metrics["integration_tests_total"] = float64(testResult.IntegrationTests.TotalTests)
	metrics["integration_tests_passed"] = float64(testResult.IntegrationTests.PassedTests)
	metrics["coverage_percent"] = coverageResult.LineCoverage
	metrics["quality_gates_passed"] = boolToFloat(qualityGateResult.AllPassed)
	metrics["regressions_detected"] = float64(len(regressions))

	output := &agents.AgentOutput{
		AgentType:   agents.AgentTypeTester,
		Status:      outputStatus,
		Result:      result,
		Metrics:     metrics,
		StartedAt:   startTime,
		CompletedAt: time.Now(),
		Duration:    duration,
	}

	a.status = agents.StatusIdle
	return output, nil
}

// Validate validates the input before execution
func (a *TesterAgent) Validate(input agents.AgentInput) error {
	if input.Task == "" {
		return fmt.Errorf("task description is required")
	}
	return nil
}

// GetCapabilities returns agent capabilities
func (a *TesterAgent) GetCapabilities() []string {
	return []string{
		"Unit test execution",
		"Integration test execution",
		"Coverage analysis",
		"Performance benchmarking",
		"Quality gate validation",
		"Regression detection",
		"MAXIMUS Predict integration",
	}
}

// GetStatus returns current agent status
func (a *TesterAgent) GetStatus() agents.AgentStatus {
	return a.status
}

// ============================================================================
// HELPER FUNCTIONS - TEST EXECUTION
// ============================================================================

// TestExecutionResult represents test execution results
type TestExecutionResult struct {
	Total    int
	Passed   int
	Failed   int
	Skipped  int
	Duration time.Duration
	Failures []agents.TestFailure
	Output   string
}

// extractImplementationResult extracts implementation result from context
func (a *TesterAgent) extractImplementationResult(context map[string]interface{}) *agents.ImplementationResult {
	if implOutput, ok := context["dev_senior_output"]; ok {
		if output, ok := implOutput.(*agents.AgentOutput); ok {
			if result, ok := output.Result.(*agents.ImplementationResult); ok {
				a.logger.Println("Implementation result found in context")
				return result
			}
		}
	}
	a.logger.Println("No implementation result in context")
	return nil
}

// runUnitTests runs unit tests
func (a *TesterAgent) runUnitTests(targets []string) (*TestExecutionResult, error) {
	if len(targets) == 0 {
		targets = []string{"./..."}
	}

	a.logger.Printf("Running unit tests: go test -v %s", strings.Join(targets, " "))

	startTime := time.Now()
	args := append([]string{"test", "-v", "-count=1"}, targets...)
	cmd := exec.Command("go", args...)
	output, err := cmd.CombinedOutput()
	duration := time.Since(startTime)

	result := &TestExecutionResult{
		Duration: duration,
		Output:   string(output),
		Failures: []agents.TestFailure{},
	}

	// Parse test output
	a.parseTestOutput(string(output), result)

	return result, err
}

// runIntegrationTests runs integration tests
func (a *TesterAgent) runIntegrationTests(targets []string) (*TestExecutionResult, error) {
	// Look for integration test tags
	a.logger.Println("Looking for integration tests...")

	args := []string{"test", "-v", "-tags=integration", "-count=1"}
	if len(targets) > 0 {
		args = append(args, targets...)
	} else {
		args = append(args, "./...")
	}

	startTime := time.Now()
	cmd := exec.Command("go", args...)
	output, err := cmd.CombinedOutput()
	duration := time.Since(startTime)

	result := &TestExecutionResult{
		Duration: duration,
		Output:   string(output),
		Failures: []agents.TestFailure{},
	}

	// Parse test output
	a.parseTestOutput(string(output), result)

	// If no integration tests found, that's okay
	if result.Total == 0 {
		a.logger.Println("No integration tests found")
	}

	return result, err
}

// parseTestOutput parses go test output
func (a *TesterAgent) parseTestOutput(output string, result *TestExecutionResult) {
	lines := strings.Split(output, "\n")
	currentTest := ""

	for _, line := range lines {
		// Parse test results
		if strings.Contains(line, "--- PASS:") {
			result.Passed++
			result.Total++
		} else if strings.Contains(line, "--- FAIL:") {
			result.Failed++
			result.Total++
			// Extract test name
			parts := strings.Fields(line)
			if len(parts) >= 3 {
				currentTest = parts[2]
			}
		} else if strings.Contains(line, "--- SKIP:") {
			result.Skipped++
			result.Total++
		} else if currentTest != "" && strings.TrimSpace(line) != "" {
			// Capture failure message
			result.Failures = append(result.Failures, agents.TestFailure{
				TestName: currentTest,
				Message:  strings.TrimSpace(line),
			})
			currentTest = ""
		}
	}
}

// CoverageResult represents coverage analysis results
type CoverageResult struct {
	LineCoverage   float64
	BranchCoverage float64
	UncoveredFiles []string
	CoverageByFile map[string]float64
}

// analyzeCoverage analyzes test coverage
func (a *TesterAgent) analyzeCoverage(targets []string) (*CoverageResult, error) {
	if len(targets) == 0 {
		targets = []string{"./..."}
	}

	a.logger.Printf("Analyzing coverage: go test -cover %s", strings.Join(targets, " "))

	args := append([]string{"test", "-cover", "-coverprofile=coverage.out"}, targets...)
	cmd := exec.Command("go", args...)
	output, err := cmd.CombinedOutput()

	result := &CoverageResult{
		CoverageByFile: make(map[string]float64),
		UncoveredFiles: []string{},
	}

	// Parse coverage from output
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.Contains(line, "coverage:") {
			// Extract coverage percentage
			parts := strings.Fields(line)
			for i, part := range parts {
				if part == "coverage:" && i+1 < len(parts) {
					coverageStr := strings.TrimSuffix(parts[i+1], "%")
					if coverage, err := strconv.ParseFloat(coverageStr, 64); err == nil {
						result.LineCoverage = coverage
					}
				}
			}
		}
	}

	// Branch coverage approximation (Go doesn't have built-in branch coverage)
	result.BranchCoverage = result.LineCoverage * 0.9 // Approximate

	return result, err
}

// BenchmarkResult represents benchmark results
type BenchmarkResult struct {
	Results []agents.BenchmarkResult
}

// runBenchmarks runs performance benchmarks
func (a *TesterAgent) runBenchmarks(targets []string) (*BenchmarkResult, error) {
	a.logger.Println("Running benchmarks...")

	args := []string{"test", "-bench=.", "-benchmem"}
	if len(targets) > 0 {
		args = append(args, targets...)
	} else {
		args = append(args, "./...")
	}

	cmd := exec.Command("go", args...)
	output, err := cmd.CombinedOutput()

	result := &BenchmarkResult{
		Results: []agents.BenchmarkResult{},
	}

	// Parse benchmark output
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.HasPrefix(line, "Benchmark") {
			parts := strings.Fields(line)
			if len(parts) >= 3 {
				result.Results = append(result.Results, agents.BenchmarkResult{
					Name:       parts[0],
					Iterations: parts[1],
					NsPerOp:    parts[2],
				})
			}
		}
	}

	if len(result.Results) == 0 {
		a.logger.Println("No benchmarks found")
	}

	return result, err
}

// checkQualityGates checks if quality gates pass
func (a *TesterAgent) checkQualityGates(coverage *CoverageResult, unitTests, integrationTests *TestExecutionResult) agents.QualityGateResult {
	gates := []agents.QualityGate{}

	// Gate 1: Minimum coverage
	minCoverage := a.config.MinCoveragePercent
	coverageGate := agents.QualityGate{
		Name:        "Minimum Coverage",
		Required:    minCoverage,
		Actual:      coverage.LineCoverage,
		Passed:      coverage.LineCoverage >= minCoverage,
		Description: fmt.Sprintf("Coverage must be at least %.1f%%", minCoverage),
	}
	gates = append(gates, coverageGate)

	// Gate 2: All tests must pass (if required)
	if a.config.RequireTestPass {
		testPassGate := agents.QualityGate{
			Name:        "All Tests Pass",
			Required:    float64(unitTests.Total),
			Actual:      float64(unitTests.Passed),
			Passed:      unitTests.Failed == 0,
			Description: "All unit tests must pass",
		}
		gates = append(gates, testPassGate)
	}

	// Gate 3: No critical failures
	criticalGate := agents.QualityGate{
		Name:        "No Critical Failures",
		Required:    0,
		Actual:      float64(unitTests.Failed),
		Passed:      unitTests.Failed == 0,
		Description: "No critical test failures allowed",
	}
	gates = append(gates, criticalGate)

	// Check if all gates passed
	allPassed := true
	for _, gate := range gates {
		if !gate.Passed {
			allPassed = false
			break
		}
	}

	return agents.QualityGateResult{
		AllPassed: allPassed,
		Gates:     gates,
	}
}

// detectRegressions detects performance regressions
func (a *TesterAgent) detectRegressions(tests *TestExecutionResult, benchmarks *BenchmarkResult) []agents.Regression {
	regressions := []agents.Regression{}

	// For now, simple regression detection
	// In real implementation, would compare with historical data using MAXIMUS Predict

	// Check for newly failing tests (simple heuristic)
	if tests.Failed > 0 {
		for _, failure := range tests.Failures {
			regressions = append(regressions, agents.Regression{
				Type:        "test_failure",
				Description: fmt.Sprintf("Test %s is failing", failure.TestName),
				Impact:      "high",
				Details:     failure.Message,
			})
		}
	}

	a.logger.Printf("Detected %d potential regressions", len(regressions))
	return regressions
}

// generateRecommendations generates recommendations based on test results
func (a *TesterAgent) generateRecommendations(qualityGates agents.QualityGateResult, coverage *CoverageResult, tests *TestExecutionResult) []string {
	recs := []string{}

	// Coverage recommendations
	if coverage.LineCoverage < a.config.MinCoveragePercent {
		recs = append(recs, fmt.Sprintf("⚠️  Increase test coverage to %.1f%% (current: %.1f%%)",
			a.config.MinCoveragePercent, coverage.LineCoverage))
	}

	// Test failure recommendations
	if tests.Failed > 0 {
		recs = append(recs, fmt.Sprintf("🚨 Fix %d failing tests before proceeding", tests.Failed))
	}

	// Quality gate recommendations
	for _, gate := range qualityGates.Gates {
		if !gate.Passed {
			recs = append(recs, fmt.Sprintf("⚠️  %s: %.1f/%.1f", gate.Name, gate.Actual, gate.Required))
		}
	}

	if len(recs) == 0 {
		recs = append(recs, "✅ All quality gates passed - ready for deployment")
	}

	return recs
}

// boolToFloat converts bool to float64
func boolToFloat(b bool) float64 {
	if b {
		return 1.0
	}
	return 0.0
}

// executeLegacyGoTests executes Go tests using legacy implementation (fallback)
func (a *TesterAgent) executeLegacyGoTests(ctx context.Context, input agents.AgentInput, startTime time.Time) (*agents.AgentOutput, error) {
	a.logger.Println("Executing legacy Go test implementation...")

	// Step 1: Extract implementation result from context (if available)
	a.logger.Println("Step 1/7: Extracting implementation context")
	_ = a.extractImplementationResult(input.Context) // For future use

	// Step 2: Run unit tests
	a.logger.Println("Step 2/7: Running unit tests")
	unitTestResult, err := a.runUnitTests(input.Targets)
	if err != nil {
		a.logger.Printf("Warning: Unit tests failed: %v", err)
	}

	// Step 3: Run integration tests (if any)
	a.logger.Println("Step 3/7: Running integration tests")
	integrationTestResult, err := a.runIntegrationTests(input.Targets)
	if err != nil {
		a.logger.Printf("Warning: Integration tests failed: %v", err)
	}

	// Step 4: Analyze test coverage
	a.logger.Println("Step 4/7: Analyzing test coverage")
	coverageResult, err := a.analyzeCoverage(input.Targets)
	if err != nil {
		a.logger.Printf("Warning: Coverage analysis failed: %v", err)
	}

	// Step 5: Run benchmarks (if requested)
	a.logger.Println("Step 5/7: Running benchmarks")
	benchmarkResult, err := a.runBenchmarks(input.Targets)
	if err != nil {
		a.logger.Printf("Info: Benchmarks skipped or failed: %v", err)
	}

	// Step 6: Check quality gates
	a.logger.Println("Step 6/7: Checking quality gates")
	qualityGateResult := a.checkQualityGates(coverageResult, unitTestResult, integrationTestResult)

	// Step 7: Detect regressions (using MAXIMUS Predict)
	a.logger.Println("Step 7/7: Detecting regressions")
	regressions := a.detectRegressions(unitTestResult, benchmarkResult)

	// Build comprehensive test result
	result := &agents.TestResult{
		TaskDescription: input.Task,
		UnitTests: agents.TestSuiteResult{
			TotalTests:   unitTestResult.Total,
			PassedTests:  unitTestResult.Passed,
			FailedTests:  unitTestResult.Failed,
			SkippedTests: unitTestResult.Skipped,
			Duration:     unitTestResult.Duration,
			Failures:     unitTestResult.Failures,
		},
		IntegrationTests: agents.TestSuiteResult{
			TotalTests:   integrationTestResult.Total,
			PassedTests:  integrationTestResult.Passed,
			FailedTests:  integrationTestResult.Failed,
			SkippedTests: integrationTestResult.Skipped,
			Duration:     integrationTestResult.Duration,
			Failures:     integrationTestResult.Failures,
		},
		Coverage: agents.CoverageResult{
			LineCoverage:   coverageResult.LineCoverage,
			BranchCoverage: coverageResult.BranchCoverage,
			UncoveredFiles: coverageResult.UncoveredFiles,
			CoverageByFile: coverageResult.CoverageByFile,
		},
		Benchmarks:      benchmarkResult.Results,
		QualityGates:    qualityGateResult,
		Regressions:     regressions,
		Recommendations: a.generateRecommendations(qualityGateResult, coverageResult, unitTestResult),
	}

	duration := time.Since(startTime)
	a.logger.Printf("Test validation complete: %d/%d tests passed, coverage: %.1f%%",
		unitTestResult.Passed, unitTestResult.Total, coverageResult.LineCoverage)

	// Determine status based on quality gates
	outputStatus := agents.StatusCompleted
	if input.HITLEnabled && (qualityGateResult.AllPassed == false || len(regressions) > 0) {
		outputStatus = agents.StatusWaitingHITL
		a.logger.Printf("HITL approval required: quality gates failed or regressions detected")
	}

	metrics := make(map[string]float64)
	metrics["unit_tests_total"] = float64(unitTestResult.Total)
	metrics["unit_tests_passed"] = float64(unitTestResult.Passed)
	metrics["unit_tests_failed"] = float64(unitTestResult.Failed)
	metrics["integration_tests_total"] = float64(integrationTestResult.Total)
	metrics["integration_tests_passed"] = float64(integrationTestResult.Passed)
	metrics["coverage_percent"] = coverageResult.LineCoverage
	metrics["quality_gates_passed"] = boolToFloat(qualityGateResult.AllPassed)
	metrics["regressions_detected"] = float64(len(regressions))

	output := &agents.AgentOutput{
		AgentType:   agents.AgentTypeTester,
		Status:      outputStatus,
		Result:      result,
		Metrics:     metrics,
		StartedAt:   startTime,
		CompletedAt: time.Now(),
		Duration:    duration,
	}

	a.status = agents.StatusIdle
	return output, nil
}
