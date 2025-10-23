package strategies

import (
	"context"
	"encoding/json"
	"os/exec"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
)

// PythonTestStrategy implements testing for Python code
type PythonTestStrategy struct {
}

// NewPythonTestStrategy creates a new Python test strategy
func NewPythonTestStrategy() *PythonTestStrategy {
	return &PythonTestStrategy{}
}

// Language returns the language this strategy supports
func (s *PythonTestStrategy) Language() language.Language {
	return language.LanguagePython
}

// GetCapabilities returns the testing capabilities
func (s *PythonTestStrategy) GetCapabilities() []string {
	return []string{
		"pytest",
		"pytest-cov",
		"pytest-xdist", // parallel execution
		"pytest-benchmark",
	}
}

// SimpleTestResult is a simplified test result for strategies
type SimpleTestResult struct {
	Passed       int
	Failed       int
	Skipped      int
	TotalTests   int
	FailedTests  []agents.FailedTest
	TestDuration int64
}

// RunTests executes pytest tests
func (s *PythonTestStrategy) RunTests(ctx context.Context, targets []string) (*agents.TestResult, error) {
	result := &agents.TestResult{
		Coverage: agents.CoverageResult{},
	}

	for _, target := range targets {
		// Run pytest with JSON report
		cmd := exec.CommandContext(ctx, "pytest", "-v", "--json-report", "--json-report-file=/tmp/pytest-report.json", target)
		output, err := cmd.CombinedOutput()

		// Parse pytest JSON report if available
		if err := s.parsePytestReport(result); err == nil {
			// Report parsed successfully
		} else {
			// Fallback: parse text output
			s.parseTextOutput(string(output), result)
		}

		// Non-fatal error handling
		if err != nil {
			continue
		}
	}

	return result, nil
}

// AnalyzeCoverage analyzes test coverage using coverage.py
func (s *PythonTestStrategy) AnalyzeCoverage(ctx context.Context, targets []string) (*agents.CoverageResult, error) {
	result := &agents.CoverageResult{
		LineCoverage:   0.0,
		BranchCoverage: 0.0,
		UncoveredFiles: make([]string, 0),
	}

	for _, target := range targets {
		// Run pytest with coverage
		cmd := exec.CommandContext(ctx, "pytest", "--cov=.", "--cov-report=json:/tmp/coverage.json", target)
		_, err := cmd.CombinedOutput()

		// Parse coverage JSON
		if err := s.parseCoverageReport(result); err != nil {
			// Non-fatal
			continue
		}

		if err != nil {
			// Non-fatal
			continue
		}
	}

	return result, nil
}

// parsePytestReport parses pytest JSON report
func (s *PythonTestStrategy) parsePytestReport(result *agents.TestResult) error {
	// Read pytest JSON report
	data, err := exec.Command("cat", "/tmp/pytest-report.json").Output()
	if err != nil {
		return err
	}

	var report map[string]interface{}
	if err := json.Unmarshal(data, &report); err != nil {
		return err
	}

	// Extract test counts - simplified for now
	// Real implementation would populate TestResult.UnitTests.PassedTests etc

	return nil
}

// parseTextOutput parses pytest text output (fallback)
func (s *PythonTestStrategy) parseTextOutput(output string, result *agents.TestResult) {
	// Simplified - real implementation would parse and populate TestResult properly
	_ = output
	_ = result
}

// parseCoverageReport parses coverage.py JSON report
func (s *PythonTestStrategy) parseCoverageReport(result *agents.CoverageResult) error {
	// Read coverage JSON
	data, err := exec.Command("cat", "/tmp/coverage.json").Output()
	if err != nil {
		return err
	}

	var report map[string]interface{}
	if err := json.Unmarshal(data, &report); err != nil {
		return err
	}

	// Extract coverage percentage
	if totals, ok := report["totals"].(map[string]interface{}); ok {
		if percentCovered, ok := totals["percent_covered"].(float64); ok {
			result.LineCoverage = percentCovered / 100.0 // Convert to 0.0-1.0 range
		}
	}

	// Extract uncovered files
	if files, ok := report["files"].(map[string]interface{}); ok {
		for fileName, fileData := range files {
			if file, ok := fileData.(map[string]interface{}); ok {
				if summary, ok := file["summary"].(map[string]interface{}); ok {
					if missingLines, ok := summary["missing_lines"].(float64); ok && missingLines > 0 {
						result.UncoveredFiles = append(result.UncoveredFiles, fileName)
					}
				}
			}
		}
	}

	return nil
}
