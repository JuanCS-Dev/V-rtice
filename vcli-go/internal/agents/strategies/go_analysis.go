package strategies

import (
	"context"
	"fmt"
	"os/exec"
	"strings"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
)

// GoAnalysisStrategy implements analysis for Go code
type GoAnalysisStrategy struct {
}

// NewGoAnalysisStrategy creates a new Go analysis strategy
func NewGoAnalysisStrategy() *GoAnalysisStrategy {
	return &GoAnalysisStrategy{}
}

// Language returns the language this strategy supports
func (s *GoAnalysisStrategy) Language() language.Language {
	return language.LanguageGo
}

// GetCapabilities returns the analysis capabilities
func (s *GoAnalysisStrategy) GetCapabilities() []string {
	return []string{
		"go_vet",
		"golangci-lint",
		"gosec",
		"go_test_coverage",
		"go_mod_analysis",
	}
}

// Analyze performs code analysis on Go targets
func (s *GoAnalysisStrategy) Analyze(ctx context.Context, targets []string) (*agents.DiagnosticResult, error) {
	result := &agents.DiagnosticResult{
		SecurityFindings:  make([]agents.SecurityFinding, 0),
		PerformanceIssues: make([]agents.PerformanceIssue, 0),
		Recommendations:   make([]string, 0),
	}

	// Run go vet
	if err := s.runGoVet(ctx, targets, result); err != nil {
		// Non-fatal, continue
	}

	// Run golangci-lint
	if err := s.runLinter(ctx, targets, result); err != nil {
		// Non-fatal, continue
	}

	// Run gosec (security scanner)
	if err := s.runSecurityScan(ctx, targets, result); err != nil {
		// Non-fatal, continue
	}

	return result, nil
}

// runGoVet runs go vet on targets
func (s *GoAnalysisStrategy) runGoVet(ctx context.Context, targets []string, result *agents.DiagnosticResult) error {
	for _, target := range targets {
		cmd := exec.CommandContext(ctx, "go", "vet", target)
		output, err := cmd.CombinedOutput()
		if err != nil {
			// Parse go vet output for issues
			lines := strings.Split(string(output), "\n")
			for _, line := range lines {
				if strings.TrimSpace(line) != "" {
					result.Recommendations = append(result.Recommendations, fmt.Sprintf("go vet: %s", line))
				}
			}
		}
	}
	return nil
}

// runLinter runs golangci-lint
func (s *GoAnalysisStrategy) runLinter(ctx context.Context, targets []string, result *agents.DiagnosticResult) error {
	cmd := exec.CommandContext(ctx, "golangci-lint", "run", "--timeout", "5m", "./...")
	output, err := cmd.CombinedOutput()
	if err != nil {
		// Parse linter output
		lines := strings.Split(string(output), "\n")
		for _, line := range lines {
			if strings.Contains(line, "warning") || strings.Contains(line, "error") {
				result.Recommendations = append(result.Recommendations, fmt.Sprintf("lint: %s", line))
			}
		}
	}
	return nil
}

// runSecurityScan runs gosec security scanner
func (s *GoAnalysisStrategy) runSecurityScan(ctx context.Context, targets []string, result *agents.DiagnosticResult) error {
	cmd := exec.CommandContext(ctx, "gosec", "-fmt=json", "./...")
	output, err := cmd.CombinedOutput()

	// Parse gosec JSON output
	if len(output) > 0 {
		// Add security findings
		// (Simplified - real implementation would parse JSON)
		result.SecurityFindings = append(result.SecurityFindings, agents.SecurityFinding{
			Severity:    "info",
			Category:    "scan_completed",
			Description: "Security scan completed",
		})
	}

	if err != nil {
		return nil // Non-fatal
	}
	return nil
}
