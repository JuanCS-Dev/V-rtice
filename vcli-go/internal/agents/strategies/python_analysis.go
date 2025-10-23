package strategies

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
)

// PythonAnalysisStrategy implements analysis for Python code
type PythonAnalysisStrategy struct {
}

// NewPythonAnalysisStrategy creates a new Python analysis strategy
func NewPythonAnalysisStrategy() *PythonAnalysisStrategy {
	return &PythonAnalysisStrategy{}
}

// Language returns the language this strategy supports
func (s *PythonAnalysisStrategy) Language() language.Language {
	return language.LanguagePython
}

// GetCapabilities returns the analysis capabilities
func (s *PythonAnalysisStrategy) GetCapabilities() []string {
	return []string{
		"pylint",
		"flake8",
		"bandit",       // security
		"mypy",         // type checking
		"pytest",       // testing
		"coverage.py",  // coverage analysis
	}
}

// Analyze performs code analysis on Python targets
func (s *PythonAnalysisStrategy) Analyze(ctx context.Context, targets []string) (*agents.DiagnosticResult, error) {
	result := &agents.DiagnosticResult{
		SecurityFindings:  make([]agents.SecurityFinding, 0),
		PerformanceIssues: make([]agents.PerformanceIssue, 0),
		Recommendations:   make([]string, 0),
	}

	// Run pylint (code quality)
	if err := s.runPylint(ctx, targets, result); err != nil {
		// Non-fatal, continue
	}

	// Run flake8 (style guide)
	if err := s.runFlake8(ctx, targets, result); err != nil {
		// Non-fatal, continue
	}

	// Run bandit (security scanner)
	if err := s.runBandit(ctx, targets, result); err != nil {
		// Non-fatal, continue
	}

	// Run mypy (type checking)
	if err := s.runMypy(ctx, targets, result); err != nil {
		// Non-fatal, continue
	}

	return result, nil
}

// runPylint runs pylint on Python code
func (s *PythonAnalysisStrategy) runPylint(ctx context.Context, targets []string, result *agents.DiagnosticResult) error {
	for _, target := range targets {
		cmd := exec.CommandContext(ctx, "pylint", "--output-format=json", target)
		output, err := cmd.CombinedOutput()

		if len(output) > 0 {
			// Parse pylint JSON output
			var issues []map[string]interface{}
			if err := json.Unmarshal(output, &issues); err == nil {
				for _, issue := range issues {
					message := fmt.Sprintf("pylint: %s - %s (line %v)",
						issue["type"],
						issue["message"],
						issue["line"])
					result.Recommendations = append(result.Recommendations, message)
				}
			}
		}

		if err != nil {
			// Pylint returns non-zero if issues found - not fatal
			continue
		}
	}
	return nil
}

// runFlake8 runs flake8 style checker
func (s *PythonAnalysisStrategy) runFlake8(ctx context.Context, targets []string, result *agents.DiagnosticResult) error {
	for _, target := range targets {
		cmd := exec.CommandContext(ctx, "flake8", "--format=json", target)
		output, err := cmd.CombinedOutput()

		if len(output) > 0 {
			// Parse flake8 output
			lines := strings.Split(string(output), "\n")
			for _, line := range lines {
				if strings.TrimSpace(line) != "" {
					result.Recommendations = append(result.Recommendations, fmt.Sprintf("flake8: %s", line))
				}
			}
		}

		if err != nil {
			// Non-fatal
			continue
		}
	}
	return nil
}

// runBandit runs bandit security scanner
func (s *PythonAnalysisStrategy) runBandit(ctx context.Context, targets []string, result *agents.DiagnosticResult) error {
	for _, target := range targets {
		cmd := exec.CommandContext(ctx, "bandit", "-f", "json", "-r", target)
		output, err := cmd.CombinedOutput()

		if len(output) > 0 {
			// Parse bandit JSON output
			var banditResult map[string]interface{}
			if err := json.Unmarshal(output, &banditResult); err == nil {
				// Extract security findings
				if results, ok := banditResult["results"].([]interface{}); ok {
					for _, r := range results {
						if finding, ok := r.(map[string]interface{}); ok {
							severity := "low"
							if sev, ok := finding["issue_severity"].(string); ok {
								severity = strings.ToLower(sev)
							}

							description := "Unknown security issue"
							if desc, ok := finding["issue_text"].(string); ok {
								description = desc
							}

							result.SecurityFindings = append(result.SecurityFindings, agents.SecurityFinding{
								Severity:    severity,
								Category:    "bandit",
								Description: description,
								FilePath:    fmt.Sprintf("%v", finding["filename"]),
							})
						}
					}
				}
			}
		}

		if err != nil {
			// Non-fatal
			continue
		}
	}
	return nil
}

// runMypy runs mypy type checker
func (s *PythonAnalysisStrategy) runMypy(ctx context.Context, targets []string, result *agents.DiagnosticResult) error {
	for _, target := range targets {
		cmd := exec.CommandContext(ctx, "mypy", "--json-report", "/dev/null", target)
		output, err := cmd.CombinedOutput()

		if len(output) > 0 {
			// Parse mypy output
			lines := strings.Split(string(output), "\n")
			for _, line := range lines {
				if strings.Contains(line, "error") || strings.Contains(line, "warning") {
					result.Recommendations = append(result.Recommendations, fmt.Sprintf("mypy: %s", line))
				}
			}
		}

		if err != nil {
			// Non-fatal
			continue
		}
	}
	return nil
}
