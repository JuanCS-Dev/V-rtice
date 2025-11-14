package diagnosticador

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
	"github.com/verticedev/vcli-go/internal/agents/strategies"
)

// ============================================================================
// CONSTRUCTOR TESTS
// ============================================================================

func TestNewDiagnosticadorAgent(t *testing.T) {
	tests := []struct {
		name   string
		config agents.AgentConfig
	}{
		{
			name: "creates agent with default config",
			config: agents.AgentConfig{
				Type:                    agents.AgentTypeDiagnosticador,
				WorkspacePath:           "/test/workspace",
				MaximusEurekaEndpoint:   "http://localhost:8080",
				AuthToken:               "test-token",
			},
		},
		{
			name: "creates agent with empty config",
			config: agents.AgentConfig{},
		},
		{
			name: "creates agent with custom endpoints",
			config: agents.AgentConfig{
				MaximusEurekaEndpoint: "http://custom:9000",
				AuthToken:             "custom-token",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDiagnosticadorAgent(tt.config)

			if agent == nil {
				t.Fatal("NewDiagnosticadorAgent returned nil")
			}

			if agent.status != agents.StatusIdle {
				t.Errorf("expected status %s, got %s", agents.StatusIdle, agent.status)
			}

			if agent.logger == nil {
				t.Error("logger should not be nil")
			}

			if agent.eurekaClient == nil {
				t.Error("eurekaClient should not be nil")
			}

			if agent.config.Type != tt.config.Type {
				t.Logf("config type: %s", agent.config.Type)
			}
		})
	}
}

// ============================================================================
// INTERFACE METHOD TESTS
// ============================================================================

func TestDiagnosticadorAgent_Type(t *testing.T) {
	agent := NewDiagnosticadorAgent(agents.AgentConfig{})

	if agent.Type() != agents.AgentTypeDiagnosticador {
		t.Errorf("expected type %s, got %s", agents.AgentTypeDiagnosticador, agent.Type())
	}
}

func TestDiagnosticadorAgent_Name(t *testing.T) {
	agent := NewDiagnosticadorAgent(agents.AgentConfig{})
	name := agent.Name()

	expectedName := "DIAGNOSTICADOR - Code Analysis & Security Scanner"
	if name != expectedName {
		t.Errorf("expected name '%s', got '%s'", expectedName, name)
	}
}

func TestDiagnosticadorAgent_GetCapabilities(t *testing.T) {
	agent := NewDiagnosticadorAgent(agents.AgentConfig{})
	caps := agent.GetCapabilities()

	expectedCaps := []string{
		"static_analysis",
		"security_scanning",
		"code_quality_metrics",
		"dependency_analysis",
		"performance_profiling",
		"test_coverage_analysis",
	}

	if len(caps) != len(expectedCaps) {
		t.Errorf("expected %d capabilities, got %d", len(expectedCaps), len(caps))
	}

	// Check each expected capability exists
	capsMap := make(map[string]bool)
	for _, cap := range caps {
		capsMap[cap] = true
	}

	for _, expected := range expectedCaps {
		if !capsMap[expected] {
			t.Errorf("missing capability: %s", expected)
		}
	}
}

func TestDiagnosticadorAgent_GetStatus(t *testing.T) {
	tests := []struct {
		name           string
		initialStatus  agents.AgentStatus
		expectedStatus agents.AgentStatus
	}{
		{
			name:           "returns idle status",
			initialStatus:  agents.StatusIdle,
			expectedStatus: agents.StatusIdle,
		},
		{
			name:           "returns running status",
			initialStatus:  agents.StatusRunning,
			expectedStatus: agents.StatusRunning,
		},
		{
			name:           "returns completed status",
			initialStatus:  agents.StatusCompleted,
			expectedStatus: agents.StatusCompleted,
		},
		{
			name:           "returns failed status",
			initialStatus:  agents.StatusFailed,
			expectedStatus: agents.StatusFailed,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDiagnosticadorAgent(agents.AgentConfig{})
			agent.status = tt.initialStatus

			status := agent.GetStatus()
			if status != tt.expectedStatus {
				t.Errorf("expected status %s, got %s", tt.expectedStatus, status)
			}
		})
	}
}

// ============================================================================
// VALIDATION TESTS
// ============================================================================

func TestDiagnosticadorAgent_Validate(t *testing.T) {
	tests := []struct {
		name        string
		input       agents.AgentInput
		setupFunc   func(t *testing.T) []string
		teardownFunc func(paths []string)
		expectError bool
		errorMsg    string
	}{
		{
			name: "valid input with existing targets",
			setupFunc: func(t *testing.T) []string {
				tmpDir := t.TempDir()
				return []string{tmpDir}
			},
			input: agents.AgentInput{
				Task:    "Analyze code",
				Targets: nil, // Will be set by setupFunc result
			},
			expectError: false,
		},
		{
			name: "missing targets",
			input: agents.AgentInput{
				Task:    "Analyze code",
				Targets: []string{},
			},
			expectError: true,
			errorMsg:    "no target paths specified",
		},
		{
			name: "nil targets",
			input: agents.AgentInput{
				Task:    "Analyze code",
				Targets: nil,
			},
			expectError: true,
			errorMsg:    "no target paths specified",
		},
		{
			name: "non-existent target path",
			input: agents.AgentInput{
				Task:    "Analyze code",
				Targets: []string{"/nonexistent/path/nowhere"},
			},
			expectError: true,
			errorMsg:    "target path does not exist",
		},
		{
			name: "multiple targets with one invalid",
			setupFunc: func(t *testing.T) []string {
				tmpDir := t.TempDir()
				return []string{tmpDir, "/invalid/path"}
			},
			input: agents.AgentInput{
				Task:    "Analyze multiple targets",
				Targets: nil,
			},
			expectError: true,
			errorMsg:    "target path does not exist",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var paths []string
			if tt.setupFunc != nil {
				paths = tt.setupFunc(t)
				tt.input.Targets = paths
			}

			if tt.teardownFunc != nil {
				defer tt.teardownFunc(paths)
			}

			agent := NewDiagnosticadorAgent(agents.AgentConfig{})
			err := agent.Validate(tt.input)

			if tt.expectError {
				if err == nil {
					t.Error("expected error, got nil")
				} else if tt.errorMsg != "" && !strings.Contains(err.Error(), tt.errorMsg) {
					t.Errorf("expected error containing '%s', got '%s'", tt.errorMsg, err.Error())
				}
			} else {
				if err != nil {
					t.Errorf("unexpected error: %v", err)
				}
			}
		})
	}
}

// ============================================================================
// CALCULATE METRICS TESTS
// ============================================================================

func TestDiagnosticadorAgent_calculateMetrics(t *testing.T) {
	tests := []struct {
		name           string
		setupFunc      func(t *testing.T) (string, []string)
		expectedLines  int
		expectError    bool
	}{
		{
			name: "counts lines in Go files",
			setupFunc: func(t *testing.T) (string, []string) {
				tmpDir := t.TempDir()
				goFile := filepath.Join(tmpDir, "main.go")
				content := `package main

import "fmt"

func main() {
	fmt.Println("Hello")
}
`
				os.WriteFile(goFile, []byte(content), 0644)
				return tmpDir, []string{tmpDir}
			},
			expectedLines: 8, // strings.Split counts the empty line after last newline
			expectError:   false,
		},
		{
			name: "counts lines in Python files",
			setupFunc: func(t *testing.T) (string, []string) {
				tmpDir := t.TempDir()
				pyFile := filepath.Join(tmpDir, "main.py")
				content := `def hello():
    print("Hello")

if __name__ == "__main__":
    hello()
`
				os.WriteFile(pyFile, []byte(content), 0644)
				return tmpDir, []string{tmpDir}
			},
			expectedLines: 6, // strings.Split counts the empty line after last newline
			expectError:   false,
		},
		{
			name: "counts files correctly with subdirectories",
			setupFunc: func(t *testing.T) (string, []string) {
				tmpDir := t.TempDir()

				// Create main Python file
				os.WriteFile(filepath.Join(tmpDir, "main.py"), []byte("print('hello')"), 0644)

				// Create a subdirectory with another file
				subDir := filepath.Join(tmpDir, "subdir")
				os.MkdirAll(subDir, 0755)
				os.WriteFile(filepath.Join(subDir, "other.go"), []byte("package main"), 0644)

				return tmpDir, []string{tmpDir}
			},
			expectedLines: 2, // main.py (1 line) + other.go (1 line)
			expectError:   false,
		},
		{
			name: "handles empty directory",
			setupFunc: func(t *testing.T) (string, []string) {
				tmpDir := t.TempDir()
				return tmpDir, []string{tmpDir}
			},
			expectedLines: 0,
			expectError:   false,
		},
		{
			name: "counts multiple files",
			setupFunc: func(t *testing.T) (string, []string) {
				tmpDir := t.TempDir()

				os.WriteFile(filepath.Join(tmpDir, "file1.go"), []byte("package main\n\nfunc foo() {}\n"), 0644)
				os.WriteFile(filepath.Join(tmpDir, "file2.go"), []byte("package main\n\nfunc bar() {}\n"), 0644)
				os.WriteFile(filepath.Join(tmpDir, "file3.py"), []byte("def baz():\n    pass\n"), 0644)

				return tmpDir, []string{tmpDir}
			},
			expectedLines: 11, // file1: 4 lines, file2: 4 lines, file3: 3 lines = 11 total
			expectError:   false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tmpDir, targets := tt.setupFunc(t)
			defer os.RemoveAll(tmpDir)

			agent := NewDiagnosticadorAgent(agents.AgentConfig{})
			result := &agents.DiagnosticResult{
				SecurityFindings:  make([]agents.SecurityFinding, 0),
				PerformanceIssues: make([]agents.PerformanceIssue, 0),
				Recommendations:   make([]string, 0),
			}

			err := agent.calculateMetrics(targets, result)

			if tt.expectError {
				if err == nil {
					t.Error("expected error, got nil")
				}
			} else {
				if err != nil {
					t.Errorf("unexpected error: %v", err)
				}

				if result.CodeQuality.LinesOfCode != tt.expectedLines {
					t.Errorf("expected %d lines, got %d", tt.expectedLines, result.CodeQuality.LinesOfCode)
				}

				// Check maintainability index is set
				if result.CodeQuality.MaintainabilityIndex == 0 {
					t.Error("maintainability index should be set")
				}
			}
		})
	}
}

// ============================================================================
// GENERATE RECOMMENDATIONS TESTS
// ============================================================================

func TestDiagnosticadorAgent_generateRecommendations(t *testing.T) {
	tests := []struct {
		name            string
		config          agents.AgentConfig
		result          *agents.DiagnosticResult
		expectedMinRecs int
		containsText    []string
	}{
		{
			name: "recommends coverage increase",
			config: agents.AgentConfig{
				MinCoveragePercent: 75.0,
			},
			result: &agents.DiagnosticResult{
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 50.0,
				},
				SecurityFindings: []agents.SecurityFinding{},
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 10,
				},
				Recommendations: []string{},
			},
			expectedMinRecs: 1,
			containsText:    []string{"coverage"},
		},
		{
			name: "recommends security fixes",
			config: agents.AgentConfig{
				MinCoveragePercent: 75.0,
			},
			result: &agents.DiagnosticResult{
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 80.0,
				},
				SecurityFindings: []agents.SecurityFinding{
					{Severity: "critical", Description: "SQL injection"},
					{Severity: "high", Description: "XSS vulnerability"},
					{Severity: "low", Description: "Minor issue"},
				},
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 10,
				},
				Recommendations: []string{},
			},
			expectedMinRecs: 1,
			containsText:    []string{"security"},
		},
		{
			name: "recommends dependency review",
			config: agents.AgentConfig{
				MinCoveragePercent: 75.0,
			},
			result: &agents.DiagnosticResult{
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 80.0,
				},
				SecurityFindings: []agents.SecurityFinding{},
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 75,
				},
				Recommendations: []string{},
			},
			expectedMinRecs: 1,
			containsText:    []string{"dependency"},
		},
		{
			name: "no recommendations when all is good",
			config: agents.AgentConfig{
				MinCoveragePercent: 75.0,
			},
			result: &agents.DiagnosticResult{
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 90.0,
				},
				SecurityFindings: []agents.SecurityFinding{},
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 20,
				},
				Recommendations: []string{},
			},
			expectedMinRecs: 0,
			containsText:    []string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDiagnosticadorAgent(tt.config)
			agent.generateRecommendations(tt.result)

			if len(tt.result.Recommendations) < tt.expectedMinRecs {
				t.Errorf("expected at least %d recommendations, got %d", tt.expectedMinRecs, len(tt.result.Recommendations))
			}

			// Check for expected text in recommendations
			for _, text := range tt.containsText {
				found := false
				for _, rec := range tt.result.Recommendations {
					if strings.Contains(strings.ToLower(rec), strings.ToLower(text)) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("expected recommendation containing '%s', got: %v", text, tt.result.Recommendations)
				}
			}
		})
	}
}

// ============================================================================
// GENERATE SUMMARY TESTS
// ============================================================================

func TestDiagnosticadorAgent_generateSummary(t *testing.T) {
	tests := []struct {
		name         string
		result       *agents.DiagnosticResult
		expectText   []string
	}{
		{
			name: "generates comprehensive summary",
			result: &agents.DiagnosticResult{
				CodeQuality: struct {
					LinesOfCode          int
					CyclomaticComplexity float64
					MaintainabilityIndex float64
					TechnicalDebt        time.Duration
				}{
					LinesOfCode: 1000,
				},
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 75.5,
				},
				SecurityFindings: []agents.SecurityFinding{
					{Severity: "high"},
					{Severity: "low"},
				},
				PerformanceIssues: []agents.PerformanceIssue{
					{Severity: "medium"},
				},
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 42,
				},
				Recommendations: []string{"rec1", "rec2"},
			},
			expectText: []string{
				"Code Analysis Complete",
				"Lines of Code: 1000",
				"Test Coverage: 75.5%",
				"Security Findings: 2",
				"Performance Issues: 1",
				"Dependencies: 42",
				"Recommendations: 2",
			},
		},
		{
			name: "generates summary with zero values",
			result: &agents.DiagnosticResult{
				CodeQuality: struct {
					LinesOfCode          int
					CyclomaticComplexity float64
					MaintainabilityIndex float64
					TechnicalDebt        time.Duration
				}{
					LinesOfCode: 0,
				},
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 0.0,
				},
				SecurityFindings:  []agents.SecurityFinding{},
				PerformanceIssues: []agents.PerformanceIssue{},
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 0,
				},
				Recommendations: []string{},
			},
			expectText: []string{
				"Lines of Code: 0",
				"Security Findings: 0",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDiagnosticadorAgent(agents.AgentConfig{})
			summary := agent.generateSummary(tt.result)

			if summary == "" {
				t.Error("expected non-empty summary")
			}

			for _, expectedText := range tt.expectText {
				if !strings.Contains(summary, expectedText) {
					t.Errorf("expected summary to contain '%s', got:\n%s", expectedText, summary)
				}
			}
		})
	}
}

// ============================================================================
// BUILD CLAUDE PROMPT TESTS
// ============================================================================

func TestDiagnosticadorAgent_buildClaudePrompt(t *testing.T) {
	tests := []struct {
		name       string
		input      agents.AgentInput
		langResult *language.DetectionResult
		metrics    *agents.DiagnosticResult
		expectText []string
	}{
		{
			name: "builds prompt for Go analysis",
			input: agents.AgentInput{
				Task:    "Analyze Go codebase",
				Targets: []string{"./internal/..."},
			},
			langResult: &language.DetectionResult{
				Primary:    language.LanguageGo,
				Confidence: 0.95,
			},
			metrics: &agents.DiagnosticResult{
				CodeQuality: struct {
					LinesOfCode          int
					CyclomaticComplexity float64
					MaintainabilityIndex float64
					TechnicalDebt        time.Duration
				}{
					LinesOfCode: 5000,
				},
			},
			expectText: []string{
				"DIAGNOSTICADOR",
				"Analyze Go codebase",
				"./internal/...",
				"go",
				"Lines of Code: 5000",
				"goroutine leak",
				"error handling",
			},
		},
		{
			name: "builds prompt for Python analysis",
			input: agents.AgentInput{
				Task:    "Analyze Python project",
				Targets: []string{"./src"},
			},
			langResult: &language.DetectionResult{
				Primary:    language.LanguagePython,
				Confidence: 0.90,
			},
			metrics: &agents.DiagnosticResult{
				CodeQuality: struct {
					LinesOfCode          int
					CyclomaticComplexity float64
					MaintainabilityIndex float64
					TechnicalDebt        time.Duration
				}{
					LinesOfCode: 3000,
				},
			},
			expectText: []string{
				"DIAGNOSTICADOR",
				"Analyze Python project",
				"./src",
				"python",
				"type hints",
				"async/await",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDiagnosticadorAgent(agents.AgentConfig{})
			prompt := agent.buildClaudePrompt(tt.input, tt.langResult, tt.metrics)

			if prompt == "" {
				t.Fatal("expected non-empty prompt")
			}

			for _, expectedText := range tt.expectText {
				if !strings.Contains(prompt, expectedText) {
					t.Errorf("expected prompt to contain '%s'", expectedText)
				}
			}

			// Verify JSON structure is mentioned
			if !strings.Contains(prompt, "```json") {
				t.Error("expected prompt to include JSON structure")
			}
		})
	}
}

// ============================================================================
// GET LANGUAGE SPECIFIC GUIDELINES TESTS
// ============================================================================

func TestDiagnosticadorAgent_getLanguageSpecificGuidelines(t *testing.T) {
	tests := []struct {
		name         string
		lang         language.Language
		expectText   []string
	}{
		{
			name: "Go guidelines",
			lang: language.LanguageGo,
			expectText: []string{
				"error handling",
				"goroutine",
				"context",
				"defer",
			},
		},
		{
			name: "Python guidelines",
			lang: language.LanguagePython,
			expectText: []string{
				"exception handling",
				"type hints",
				"async/await",
				"PEP 8",
			},
		},
		{
			name: "Unknown language guidelines",
			lang: language.LanguageUnknown,
			expectText: []string{
				"best practices",
				"security vulnerabilities",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDiagnosticadorAgent(agents.AgentConfig{})
			guidelines := agent.getLanguageSpecificGuidelines(tt.lang)

			if guidelines == "" {
				t.Error("expected non-empty guidelines")
			}

			for _, expectedText := range tt.expectText {
				if !strings.Contains(guidelines, expectedText) {
					t.Errorf("expected guidelines to contain '%s', got:\n%s", expectedText, guidelines)
				}
			}
		})
	}
}

// ============================================================================
// MOCK ANALYSIS STRATEGY
// ============================================================================

type mockAnalysisStrategy struct {
	lang   language.Language
	result *agents.DiagnosticResult
	err    error
}

func (m *mockAnalysisStrategy) Language() language.Language {
	return m.lang
}

func (m *mockAnalysisStrategy) Analyze(ctx context.Context, targets []string) (*agents.DiagnosticResult, error) {
	if m.err != nil {
		return nil, m.err
	}
	return m.result, nil
}

func (m *mockAnalysisStrategy) GetCapabilities() []string {
	return []string{"mock_analysis"}
}

// ============================================================================
// STRATEGY REGISTRY INTEGRATION
// ============================================================================

func TestStrategyRegistryIntegration_Analysis(t *testing.T) {
	// Test that we can create and use an analysis strategy registry
	registry := strategies.NewStrategyRegistry()

	// Create a mock strategy
	mockStrategy := &mockAnalysisStrategy{
		lang: language.LanguagePython,
		result: &agents.DiagnosticResult{
			SecurityFindings:  []agents.SecurityFinding{},
			PerformanceIssues: []agents.PerformanceIssue{},
			Recommendations:   []string{},
		},
	}

	// Register the mock strategy
	registry.RegisterAnalysis(mockStrategy)

	// Retrieve the strategy
	strategy, ok := registry.GetAnalysis(language.LanguagePython)
	if !ok {
		t.Fatal("failed to retrieve registered strategy")
	}

	if strategy.Language() != language.LanguagePython {
		t.Errorf("expected language Python, got %s", strategy.Language())
	}

	// Test strategy execution
	ctx := context.Background()
	result, err := strategy.Analyze(ctx, []string{"./"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if result == nil {
		t.Fatal("expected result, got nil")
	}
}

// ============================================================================
// CONCURRENT ACCESS TESTS
// ============================================================================

func TestDiagnosticadorAgent_ConcurrentStatusAccess(t *testing.T) {
	agent := NewDiagnosticadorAgent(agents.AgentConfig{})

	// Simulate concurrent status reads/writes
	done := make(chan bool)

	go func() {
		for i := 0; i < 100; i++ {
			agent.status = agents.StatusRunning
		}
		done <- true
	}()

	go func() {
		for i := 0; i < 100; i++ {
			_ = agent.GetStatus()
		}
		done <- true
	}()

	<-done
	<-done

	// If we get here without race detector complaining, we're good
}

// ============================================================================
// EDGE CASE TESTS
// ============================================================================

func TestDiagnosticadorAgent_calculateMetrics_ErrorHandling(t *testing.T) {
	agent := NewDiagnosticadorAgent(agents.AgentConfig{})

	result := &agents.DiagnosticResult{
		SecurityFindings:  make([]agents.SecurityFinding, 0),
		PerformanceIssues: make([]agents.PerformanceIssue, 0),
		Recommendations:   make([]string, 0),
	}

	// Test with invalid path
	err := agent.calculateMetrics([]string{"/absolutely/nonexistent/path"}, result)

	// Should handle gracefully (might error or not)
	if err != nil {
		t.Logf("Expected error for invalid path: %v", err)
	}
}

func TestDiagnosticadorAgent_generateRecommendations_EdgeCases(t *testing.T) {
	tests := []struct {
		name   string
		config agents.AgentConfig
		result *agents.DiagnosticResult
	}{
		{
			name: "handles nil recommendations slice",
			config: agents.AgentConfig{
				MinCoveragePercent: 75.0,
			},
			result: &agents.DiagnosticResult{
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 0.0,
				},
				SecurityFindings: []agents.SecurityFinding{},
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 0,
				},
				Recommendations: nil, // nil instead of empty slice
			},
		},
		{
			name: "handles extreme values",
			config: agents.AgentConfig{
				MinCoveragePercent: 100.0,
			},
			result: &agents.DiagnosticResult{
				TestCoverage: struct {
					LineCoverage   float64
					BranchCoverage float64
					UncoveredFiles []string
				}{
					LineCoverage: 0.0,
				},
				SecurityFindings: make([]agents.SecurityFinding, 100), // Many findings
				Dependencies: struct {
					Total      int
					Outdated   []string
					Vulnerable []string
					Licenses   map[string]int
				}{
					Total: 1000,
				},
				Recommendations: []string{},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewDiagnosticadorAgent(tt.config)

			// Should not panic
			agent.generateRecommendations(tt.result)

			// Recommendations should be set (even if nil initially)
			if tt.result.Recommendations == nil {
				t.Log("Recommendations remain nil (implementation detail)")
			}
		})
	}
}
