package diagnosticador

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
	"github.com/verticedev/vcli-go/internal/agents/strategies"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// DiagnosticadorAgent performs code analysis and security scanning
type DiagnosticadorAgent struct {
	config agents.AgentConfig
	status agents.AgentStatus
	logger *log.Logger

	// MAXIMUS Eureka client for pattern detection
	eurekaClient *maximus.EurekaClient
}

// NewDiagnosticadorAgent creates a new DIAGNOSTICADOR agent
func NewDiagnosticadorAgent(config agents.AgentConfig) *DiagnosticadorAgent {
	return &DiagnosticadorAgent{
		config:       config,
		status:       agents.StatusIdle,
		logger:       log.New(os.Stdout, "[DIAGNOSTICADOR] ", log.LstdFlags),
		eurekaClient: maximus.NewEurekaClient(config.MaximusEurekaEndpoint, config.AuthToken),
	}
}

// Type returns the agent type
func (a *DiagnosticadorAgent) Type() agents.AgentType {
	return agents.AgentTypeDiagnosticador
}

// Name returns the agent name
func (a *DiagnosticadorAgent) Name() string {
	return "DIAGNOSTICADOR - Code Analysis & Security Scanner"
}

// GetCapabilities returns the agent's capabilities
func (a *DiagnosticadorAgent) GetCapabilities() []string {
	return []string{
		"static_analysis",
		"security_scanning",
		"code_quality_metrics",
		"dependency_analysis",
		"performance_profiling",
		"test_coverage_analysis",
	}
}

// GetStatus returns the current agent status
func (a *DiagnosticadorAgent) GetStatus() agents.AgentStatus {
	return a.status
}

// Validate checks if the agent can execute with the given input
func (a *DiagnosticadorAgent) Validate(input agents.AgentInput) error {
	if len(input.Targets) == 0 {
		return fmt.Errorf("no target paths specified for analysis")
	}

	// Check if targets exist
	for _, target := range input.Targets {
		if _, err := os.Stat(target); err != nil {
			return fmt.Errorf("target path does not exist: %s", target)
		}
	}

	return nil
}

// Execute runs the diagnosticador agent
func (a *DiagnosticadorAgent) Execute(ctx context.Context, input agents.AgentInput) (*agents.AgentOutput, error) {
	a.status = agents.StatusRunning
	startTime := time.Now()

	a.logger.Printf("Starting code analysis and security scan")
	a.logger.Printf("Targets: %v", input.Targets)

	output := &agents.AgentOutput{
		AgentType:  agents.AgentTypeDiagnosticador,
		Status:     agents.StatusRunning,
		Artifacts:  make([]string, 0),
		Metrics:    make(map[string]float64),
		Errors:     make([]string, 0),
		StartedAt:  startTime,
		Metadata:   make(map[string]interface{}),
	}

	// Step 0: Language Detection
	a.logger.Println("Step 0/3: Detecting language...")
	detector := language.NewDetector()
	langResult, err := detector.Detect(input.Targets)
	if err != nil {
		return nil, fmt.Errorf("language detection failed: %w", err)
	}
	a.logger.Printf("   Detected: %s (%.0f%% confidence)", langResult.Primary, langResult.Confidence*100)
	output.Metadata["detected_language"] = langResult.Primary
	output.Metadata["language_confidence"] = langResult.Confidence

	// Step 1: Create and populate strategy registry
	a.logger.Println("Step 1/3: Initializing analysis strategy...")
	registry := strategies.NewStrategyRegistry()
	registry.RegisterAnalysis(strategies.NewGoAnalysisStrategy())
	registry.RegisterAnalysis(strategies.NewPythonAnalysisStrategy())

	strategy, ok := registry.GetAnalysis(langResult.Primary)
	if !ok {
		return nil, fmt.Errorf("no analysis strategy for language: %s", langResult.Primary)
	}
	a.logger.Printf("   Using %s analysis strategy", langResult.Primary)

	// Step 2: Run language-specific analysis
	a.logger.Println("Step 2/3: Running language-specific analysis...")
	result, err := strategy.Analyze(ctx, input.Targets)
	if err != nil {
		output.Errors = append(output.Errors, fmt.Sprintf("analysis failed: %v", err))
		// Initialize empty result to avoid nil panic
		result = &agents.DiagnosticResult{
			SecurityFindings:  make([]agents.SecurityFinding, 0),
			PerformanceIssues: make([]agents.PerformanceIssue, 0),
			Recommendations:   make([]string, 0),
		}
	}

	// Step 3: Calculate code quality metrics (language-agnostic)
	a.logger.Println("Step 3/3: Calculating code quality metrics")
	if err := a.calculateMetrics(input.Targets, result); err != nil {
		output.Errors = append(output.Errors, fmt.Sprintf("metrics calculation failed: %v", err))
	}

	// Generate recommendations
	a.generateRecommendations(result)

	// Generate summary
	result.Summary = a.generateSummary(result)

	// Populate output
	output.Result = result
	output.Metrics["security_findings_count"] = float64(len(result.SecurityFindings))
	output.Metrics["performance_issues_count"] = float64(len(result.PerformanceIssues))
	output.Metrics["test_coverage_percent"] = result.TestCoverage.LineCoverage
	output.Metrics["lines_of_code"] = float64(result.CodeQuality.LinesOfCode)

	// Determine next agent
	if len(result.SecurityFindings) == 0 && len(result.PerformanceIssues) == 0 {
		output.NextAgent = agents.AgentTypeArquiteto
	} else {
		output.NextAgent = agents.AgentTypeDevSenior // Need fixes first
	}

	// Complete
	output.CompletedAt = time.Now()
	output.Duration = output.CompletedAt.Sub(output.StartedAt)
	output.Status = agents.StatusCompleted
	a.status = agents.StatusCompleted

	a.logger.Printf("Analysis complete: %d security findings, %d performance issues",
		len(result.SecurityFindings), len(result.PerformanceIssues))

	return output, nil
}

// calculateMetrics calculates code quality metrics (language-agnostic)
func (a *DiagnosticadorAgent) calculateMetrics(targets []string, result *agents.DiagnosticResult) error {
	var totalLines int

	for _, target := range targets {
		err := filepath.Walk(target, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			// Count lines for both Go and Python files
			if !info.IsDir() && (strings.HasSuffix(path, ".go") || strings.HasSuffix(path, ".py")) {
				// Skip common ignore patterns
				if strings.Contains(path, ".venv") ||
				   strings.Contains(path, "__pycache__") ||
				   strings.Contains(path, "node_modules") {
					return nil
				}

				data, err := os.ReadFile(path)
				if err == nil {
					lines := strings.Split(string(data), "\n")
					totalLines += len(lines)
				}
			}
			return nil
		})
		if err != nil {
			return err
		}
	}

	result.CodeQuality.LinesOfCode = totalLines
	result.CodeQuality.MaintainabilityIndex = 75.0 // Placeholder

	return nil
}

// generateRecommendations generates actionable recommendations
func (a *DiagnosticadorAgent) generateRecommendations(result *agents.DiagnosticResult) {
	if result.TestCoverage.LineCoverage < float64(a.config.MinCoveragePercent) {
		result.Recommendations = append(result.Recommendations,
			fmt.Sprintf("⚠️  Increase test coverage to at least %.0f%% (current: %.1f%%)",
				a.config.MinCoveragePercent, result.TestCoverage.LineCoverage))
	}

	if len(result.SecurityFindings) > 0 {
		criticalCount := 0
		for _, finding := range result.SecurityFindings {
			if finding.Severity == "critical" || finding.Severity == "high" {
				criticalCount++
			}
		}
		if criticalCount > 0 {
			result.Recommendations = append(result.Recommendations,
				fmt.Sprintf("🚨 Address %d critical/high security findings immediately", criticalCount))
		}
	}

	if result.Dependencies.Total > 50 {
		result.Recommendations = append(result.Recommendations,
			fmt.Sprintf("📦 Review dependency count (%d) - consider minimizing", result.Dependencies.Total))
	}
}

// generateSummary generates a summary of the analysis
func (a *DiagnosticadorAgent) generateSummary(result *agents.DiagnosticResult) string {
	summary := fmt.Sprintf("Code Analysis Complete:\n")
	summary += fmt.Sprintf("- Lines of Code: %d\n", result.CodeQuality.LinesOfCode)
	summary += fmt.Sprintf("- Test Coverage: %.1f%%\n", result.TestCoverage.LineCoverage)
	summary += fmt.Sprintf("- Security Findings: %d\n", len(result.SecurityFindings))
	summary += fmt.Sprintf("- Performance Issues: %d\n", len(result.PerformanceIssues))
	summary += fmt.Sprintf("- Dependencies: %d\n", result.Dependencies.Total)
	summary += fmt.Sprintf("- Recommendations: %d\n", len(result.Recommendations))

	return summary
}
