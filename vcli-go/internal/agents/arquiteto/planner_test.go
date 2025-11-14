package arquiteto

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
)

// TestNewArquitetoAgent tests agent initialization
func TestNewArquitetoAgent(t *testing.T) {
	tests := []struct {
		name   string
		config agents.AgentConfig
	}{
		{
			name: "with_minimal_config",
			config: agents.AgentConfig{
				Type:                   agents.AgentTypeArquiteto,
				WorkspacePath:          "/tmp/test",
				MaximusOraculoEndpoint: "http://localhost:8080",
			},
		},
		{
			name: "with_full_config",
			config: agents.AgentConfig{
				Type:                   agents.AgentTypeArquiteto,
				WorkspacePath:          "/tmp/test",
				MaximusOraculoEndpoint: "http://localhost:8080",
				AuthToken:              "test-token",
				MinCoveragePercent:     80.0,
				RequireSecurityScan:    true,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			agent := NewArquitetoAgent(tt.config)

			if agent == nil {
				t.Fatal("NewArquitetoAgent returned nil")
			}

			if agent.config.Type != tt.config.Type {
				t.Errorf("config.Type = %v, want %v", agent.config.Type, tt.config.Type)
			}

			if agent.status != agents.StatusIdle {
				t.Errorf("status = %v, want %v", agent.status, agents.StatusIdle)
			}

			if agent.logger == nil {
				t.Error("logger is nil")
			}

			if agent.oraculoClient == nil {
				t.Error("oraculoClient is nil")
			}
		})
	}
}

// TestType tests the Type method
func TestType(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	if got := agent.Type(); got != agents.AgentTypeArquiteto {
		t.Errorf("Type() = %v, want %v", got, agents.AgentTypeArquiteto)
	}
}

// TestName tests the Name method
func TestName(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	name := agent.Name()
	if name == "" {
		t.Error("Name() returned empty string")
	}

	if !strings.Contains(name, "ARQUITETO") {
		t.Errorf("Name() = %q, want to contain 'ARQUITETO'", name)
	}
}

// TestGetCapabilities tests the GetCapabilities method
func TestGetCapabilities(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	caps := agent.GetCapabilities()
	if len(caps) == 0 {
		t.Error("GetCapabilities() returned empty slice")
	}

	expectedCaps := []string{
		"architecture_planning",
		"adr_generation",
		"risk_assessment",
		"integration_test_design",
		"implementation_planning",
	}

	for _, expected := range expectedCaps {
		found := false
		for _, cap := range caps {
			if cap == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("GetCapabilities() missing capability %q", expected)
		}
	}
}

// TestGetStatus tests the GetStatus method
func TestGetStatus(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	if got := agent.GetStatus(); got != agents.StatusIdle {
		t.Errorf("GetStatus() = %v, want %v", got, agents.StatusIdle)
	}

	// Simulate status change
	agent.status = agents.StatusRunning
	if got := agent.GetStatus(); got != agents.StatusRunning {
		t.Errorf("GetStatus() = %v, want %v", got, agents.StatusRunning)
	}
}

// TestValidate tests the Validate method
func TestValidate(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	tests := []struct {
		name    string
		input   agents.AgentInput
		wantErr bool
	}{
		{
			name: "valid_input",
			input: agents.AgentInput{
				Task:    "Design user authentication system",
				Targets: []string{"./pkg/auth"},
				Context: make(map[string]interface{}),
			},
			wantErr: false,
		},
		{
			name: "empty_task",
			input: agents.AgentInput{
				Task:    "",
				Targets: []string{"./pkg/auth"},
				Context: make(map[string]interface{}),
			},
			wantErr: true,
		},
		{
			name: "with_diagnosticador_context",
			input: agents.AgentInput{
				Task: "Refactor authentication",
				Context: map[string]interface{}{
					"diagnosticador_output": &agents.AgentOutput{
						Result: &agents.DiagnosticResult{},
					},
				},
			},
			wantErr: false,
		},
		{
			name: "without_diagnosticador_context",
			input: agents.AgentInput{
				Task:    "Create new feature",
				Context: make(map[string]interface{}),
			},
			wantErr: false, // Should warn but not error
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := agent.Validate(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("Validate() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// TestExtractDiagnosticContext tests the extractDiagnosticContext method
func TestExtractDiagnosticContext(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	tests := []struct {
		name     string
		context  map[string]interface{}
		wantKeys []string
	}{
		{
			name: "with_full_diagnostic_result",
			context: map[string]interface{}{
				"diagnosticador_output": &agents.AgentOutput{
					Result: &agents.DiagnosticResult{
						SecurityFindings: []agents.SecurityFinding{
							{Severity: "high", Description: "SQL injection"},
						},
						PerformanceIssues: []agents.PerformanceIssue{
							{Severity: "medium", Description: "Slow query"},
						},
						TestCoverage: struct {
							LineCoverage   float64
							BranchCoverage float64
							UncoveredFiles []string
						}{
							LineCoverage: 75.5,
						},
						Dependencies: struct {
							Total      int
							Outdated   []string
							Vulnerable []string
							Licenses   map[string]int
						}{
							Total: 42,
						},
					},
				},
			},
			wantKeys: []string{"security_findings", "performance_issues", "test_coverage", "dependencies"},
		},
		{
			name:     "without_diagnostic_result",
			context:  map[string]interface{}{},
			wantKeys: []string{},
		},
		{
			name: "with_invalid_output_type",
			context: map[string]interface{}{
				"diagnosticador_output": "not an AgentOutput",
			},
			wantKeys: []string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := agent.extractDiagnosticContext(tt.context)

			if result == nil {
				t.Fatal("extractDiagnosticContext returned nil")
			}

			for _, key := range tt.wantKeys {
				if _, ok := result[key]; !ok {
					t.Errorf("extractDiagnosticContext() missing key %q", key)
				}
			}
		})
	}
}

// TestBuildADRContext tests the buildADRContext method
func TestBuildADRContext(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	tests := []struct {
		name        string
		input       agents.AgentInput
		diagContext map[string]interface{}
		wantContain []string
	}{
		{
			name: "with_security_findings",
			input: agents.AgentInput{
				Task: "Implement feature X",
			},
			diagContext: map[string]interface{}{
				"security_findings": []agents.SecurityFinding{
					{Severity: "high", Description: "XSS vulnerability"},
					{Severity: "medium", Description: "Weak encryption"},
				},
			},
			wantContain: []string{"Implement feature X", "Security Considerations", "2 findings"},
		},
		{
			name: "with_performance_issues",
			input: agents.AgentInput{
				Task: "Optimize API",
			},
			diagContext: map[string]interface{}{
				"performance_issues": []agents.PerformanceIssue{
					{Severity: "high", Description: "N+1 query"},
				},
			},
			wantContain: []string{"Optimize API", "Performance Considerations", "1 issues"},
		},
		{
			name: "with_test_coverage",
			input: agents.AgentInput{
				Task: "Add tests",
			},
			diagContext: map[string]interface{}{
				"test_coverage": 65.5,
			},
			wantContain: []string{"Add tests", "Test Coverage", "65.5"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := agent.buildADRContext(tt.input, tt.diagContext)

			if result == "" {
				t.Error("buildADRContext returned empty string")
			}

			for _, want := range tt.wantContain {
				if !strings.Contains(result, want) {
					t.Errorf("buildADRContext() missing %q, got %q", want, result)
				}
			}
		})
	}
}

// TestBuildADRDecision tests the buildADRDecision method
func TestBuildADRDecision(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	tests := []struct {
		name        string
		input       agents.AgentInput
		diagContext map[string]interface{}
		wantContain []string
	}{
		{
			name: "basic_decision",
			input: agents.AgentInput{
				Task: "Create microservice",
			},
			diagContext: map[string]interface{}{},
			wantContain: []string{"Implement", "Create microservice", "VÉRTICE", "Padrão Pagani"},
		},
		{
			name: "with_security_findings",
			input: agents.AgentInput{
				Task: "Secure API",
			},
			diagContext: map[string]interface{}{
				"security_findings": []agents.SecurityFinding{
					{Severity: "critical", Description: "Auth bypass"},
				},
			},
			wantContain: []string{"security findings"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := agent.buildADRDecision(tt.input, tt.diagContext)

			if result == "" {
				t.Error("buildADRDecision returned empty string")
			}

			for _, want := range tt.wantContain {
				if !strings.Contains(result, want) {
					t.Errorf("buildADRDecision() missing %q", want)
				}
			}
		})
	}
}

// TestBuildADRConsequences tests the buildADRConsequences method
func TestBuildADRConsequences(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	tests := []struct {
		name        string
		input       agents.AgentInput
		diagContext map[string]interface{}
		minCount    int
		wantContain []string
	}{
		{
			name: "basic_consequences",
			input: agents.AgentInput{
				Task: "Add feature",
			},
			diagContext: map[string]interface{}{},
			minCount:    3,
			wantContain: []string{"VÉRTICE"},
		},
		{
			name: "with_low_coverage",
			input: agents.AgentInput{
				Task: "Refactor code",
			},
			diagContext: map[string]interface{}{
				"test_coverage": 60.0,
			},
			minCount:    4,
			wantContain: []string{"test coverage"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := agent.buildADRConsequences(tt.input, tt.diagContext)

			if len(result) < tt.minCount {
				t.Errorf("buildADRConsequences() returned %d consequences, want at least %d",
					len(result), tt.minCount)
			}

			found := false
			for _, cons := range result {
				for _, want := range tt.wantContain {
					if strings.Contains(cons, want) {
						found = true
						break
					}
				}
			}

			if len(tt.wantContain) > 0 && !found {
				t.Errorf("buildADRConsequences() missing expected content: %v", tt.wantContain)
			}
		})
	}
}

// TestGenerateADRs tests the generateADRs method
func TestGenerateADRs(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task: "Implement authentication system",
	}

	tests := []struct {
		name        string
		diagContext map[string]interface{}
		wantMinADRs int
	}{
		{
			name:        "minimal_context",
			diagContext: map[string]interface{}{},
			wantMinADRs: 3, // Main ADR, integration, testing
		},
		{
			name: "with_diagnostic_context",
			diagContext: map[string]interface{}{
				"security_findings": []agents.SecurityFinding{},
			},
			wantMinADRs: 3,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			plan := &agents.ArchitecturePlan{
				PlanID: "test-plan",
				ADRs:   make([]agents.ADR, 0),
			}

			err := agent.generateADRs(ctx, input, tt.diagContext, plan)
			if err != nil {
				t.Errorf("generateADRs() error = %v", err)
			}

			if len(plan.ADRs) < tt.wantMinADRs {
				t.Errorf("generateADRs() generated %d ADRs, want at least %d",
					len(plan.ADRs), tt.wantMinADRs)
			}

			// Verify ADR structure
			for i, adr := range plan.ADRs {
				if adr.ID == "" {
					t.Errorf("ADR[%d].ID is empty", i)
				}
				if adr.Title == "" {
					t.Errorf("ADR[%d].Title is empty", i)
				}
				if adr.Context == "" {
					t.Errorf("ADR[%d].Context is empty", i)
				}
				if adr.Decision == "" {
					t.Errorf("ADR[%d].Decision is empty", i)
				}
				if adr.Status == "" {
					t.Errorf("ADR[%d].Status is empty", i)
				}
			}
		})
	}
}

// TestAssessRisks tests the assessRisks method
func TestAssessRisks(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task: "Deploy new microservice",
	}

	tests := []struct {
		name        string
		diagContext map[string]interface{}
		wantMinRisks int
		wantHighRisk bool
	}{
		{
			name:         "minimal_risks",
			diagContext:  map[string]interface{}{},
			wantMinRisks: 1, // At least integration risk
			wantHighRisk: false,
		},
		{
			name: "with_critical_security_findings",
			diagContext: map[string]interface{}{
				"security_findings": []agents.SecurityFinding{
					{Severity: "critical", Description: "SQL injection"},
					{Severity: "high", Description: "XSS"},
				},
			},
			wantMinRisks: 2,
			wantHighRisk: true,
		},
		{
			name: "with_low_coverage",
			diagContext: map[string]interface{}{
				"test_coverage": 45.0,
			},
			wantMinRisks: 2,
			wantHighRisk: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			plan := &agents.ArchitecturePlan{
				PlanID: "test-plan",
				Risks:  make([]agents.Risk, 0),
			}

			err := agent.assessRisks(ctx, input, tt.diagContext, plan)
			if err != nil {
				t.Errorf("assessRisks() error = %v", err)
			}

			if len(plan.Risks) < tt.wantMinRisks {
				t.Errorf("assessRisks() generated %d risks, want at least %d",
					len(plan.Risks), tt.wantMinRisks)
			}

			// Verify risk structure
			hasHighRisk := false
			for i, risk := range plan.Risks {
				if risk.Severity == "" {
					t.Errorf("Risk[%d].Severity is empty", i)
				}
				if risk.Category == "" {
					t.Errorf("Risk[%d].Category is empty", i)
				}
				if risk.Description == "" {
					t.Errorf("Risk[%d].Description is empty", i)
				}
				if risk.Impact == "" {
					t.Errorf("Risk[%d].Impact is empty", i)
				}
				if risk.Mitigation == "" {
					t.Errorf("Risk[%d].Mitigation is empty", i)
				}
				if risk.Probability < 0 || risk.Probability > 1 {
					t.Errorf("Risk[%d].Probability = %f, want in range [0, 1]", i, risk.Probability)
				}

				if risk.Severity == "high" {
					hasHighRisk = true
				}
			}

			if tt.wantHighRisk && !hasHighRisk {
				t.Error("assessRisks() should have identified high severity risk")
			}
		})
	}
}

// TestGenerateImplementationPlan tests the generateImplementationPlan method
func TestGenerateImplementationPlan(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task: "Create REST API",
	}

	tests := []struct {
		name         string
		diagContext  map[string]interface{}
		wantMinSteps int
	}{
		{
			name:         "basic_plan",
			diagContext:  map[string]interface{}{},
			wantMinSteps: 2, // At least implementation and testing
		},
		{
			name: "with_security_findings",
			diagContext: map[string]interface{}{
				"security_findings": []agents.SecurityFinding{
					{Severity: "high", Description: "Auth issue"},
				},
			},
			wantMinSteps: 3, // Security fixes + implementation + testing
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			plan := &agents.ArchitecturePlan{
				PlanID: "test-plan",
				Steps:  make([]agents.ImplementationStep, 0),
			}

			err := agent.generateImplementationPlan(ctx, input, tt.diagContext, plan)
			if err != nil {
				t.Errorf("generateImplementationPlan() error = %v", err)
			}

			if len(plan.Steps) < tt.wantMinSteps {
				t.Errorf("generateImplementationPlan() generated %d steps, want at least %d",
					len(plan.Steps), tt.wantMinSteps)
			}

			// Verify step structure and ordering
			for i, step := range plan.Steps {
				if step.StepNumber != i+1 {
					t.Errorf("Step[%d].StepNumber = %d, want %d", i, step.StepNumber, i+1)
				}
				if step.Description == "" {
					t.Errorf("Step[%d].Description is empty", i)
				}
				if step.AgentType == "" {
					t.Errorf("Step[%d].AgentType is empty", i)
				}
				if step.EstimatedTime <= 0 {
					t.Errorf("Step[%d].EstimatedTime = %v, want > 0", i, step.EstimatedTime)
				}
			}
		})
	}
}

// TestDesignIntegrationTests tests the designIntegrationTests method
func TestDesignIntegrationTests(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task: "Build payment system",
	}

	plan := &agents.ArchitecturePlan{
		PlanID:           "test-plan",
		IntegrationTests: make([]agents.TestScenario, 0),
	}

	err := agent.designIntegrationTests(ctx, input, plan)
	if err != nil {
		t.Fatalf("designIntegrationTests() error = %v", err)
	}

	if len(plan.IntegrationTests) < 3 {
		t.Errorf("designIntegrationTests() generated %d tests, want at least 3",
			len(plan.IntegrationTests))
	}

	// Verify test scenario structure
	for i, test := range plan.IntegrationTests {
		if test.Name == "" {
			t.Errorf("TestScenario[%d].Name is empty", i)
		}
		if test.Description == "" {
			t.Errorf("TestScenario[%d].Description is empty", i)
		}
		if test.Type == "" {
			t.Errorf("TestScenario[%d].Type is empty", i)
		}
		if len(test.Steps) == 0 {
			t.Errorf("TestScenario[%d].Steps is empty", i)
		}
		if test.Expected == "" {
			t.Errorf("TestScenario[%d].Expected is empty", i)
		}
	}

	// Verify we have different test types
	types := make(map[string]bool)
	for _, test := range plan.IntegrationTests {
		types[test.Type] = true
	}

	if len(types) < 2 {
		t.Error("designIntegrationTests() should generate tests of multiple types")
	}
}

// TestCalculateEffortEstimate tests the calculateEffortEstimate method
func TestCalculateEffortEstimate(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	tests := []struct {
		name            string
		steps           []agents.ImplementationStep
		wantMinHours    float64
		wantMaxHours    float64
	}{
		{
			name: "two_hours_work",
			steps: []agents.ImplementationStep{
				{EstimatedTime: 1 * time.Hour},
				{EstimatedTime: 1 * time.Hour},
			},
			wantMinHours: 2.5,  // 2 hours * 1.3 buffer
			wantMaxHours: 2.7,
		},
		{
			name: "empty_steps",
			steps: []agents.ImplementationStep{},
			wantMinHours: 0,
			wantMaxHours: 0.1,
		},
		{
			name: "complex_project",
			steps: []agents.ImplementationStep{
				{EstimatedTime: 4 * time.Hour},
				{EstimatedTime: 6 * time.Hour},
				{EstimatedTime: 2 * time.Hour},
			},
			wantMinHours: 15.0, // 12 hours * 1.3 buffer
			wantMaxHours: 16.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			plan := &agents.ArchitecturePlan{
				PlanID: "test-plan",
				Steps:  tt.steps,
			}

			agent.calculateEffortEstimate(plan)

			if plan.EstimatedHours < tt.wantMinHours || plan.EstimatedHours > tt.wantMaxHours {
				t.Errorf("calculateEffortEstimate() = %.2f hours, want in range [%.2f, %.2f]",
					plan.EstimatedHours, tt.wantMinHours, tt.wantMaxHours)
			}
		})
	}
}

// TestGenerateSummary tests the generateSummary method
func TestGenerateSummary(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	plan := &agents.ArchitecturePlan{
		PlanID:         "test-plan-123",
		Title:          "Authentication System",
		EstimatedHours: 24.5,
		ADRs: []agents.ADR{
			{ID: "ADR-001", Title: "Use OAuth2"},
			{ID: "ADR-002", Title: "JWT tokens"},
		},
		Risks: []agents.Risk{
			{Severity: "high", Description: "Token leak"},
		},
		Steps: []agents.ImplementationStep{
			{StepNumber: 1, Description: "Setup OAuth2"},
			{StepNumber: 2, Description: "Implement JWT"},
			{StepNumber: 3, Description: "Add tests"},
		},
		IntegrationTests: []agents.TestScenario{
			{Name: "Test OAuth flow"},
			{Name: "Test token validation"},
		},
	}

	summary := agent.generateSummary(plan)

	if summary == "" {
		t.Fatal("generateSummary() returned empty string")
	}

	wantContain := []string{
		"Authentication System",
		"ADRs Generated: 2",
		"Risks Identified: 1",
		"Implementation Steps: 3",
		"Integration Tests: 2",
		"24.5 hours",
	}

	for _, want := range wantContain {
		if !strings.Contains(summary, want) {
			t.Errorf("generateSummary() missing %q in output:\n%s", want, summary)
		}
	}
}

// TestBuildClaudePrompt tests the buildClaudePrompt method
func TestBuildClaudePrompt(t *testing.T) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	input := agents.AgentInput{
		Task:    "Create microservice for user management",
		Targets: []string{"./services/user", "./api/user"},
	}

	tests := []struct {
		name        string
		diagContext map[string]interface{}
		wantContain []string
	}{
		{
			name:        "basic_prompt",
			diagContext: map[string]interface{}{},
			wantContain: []string{
				"ARQUITETO",
				"Create microservice for user management",
				"./services/user",
				"Architecture Decision Records",
				"Risk Assessment",
				"Implementation Steps",
				"Padrão Pagani",
				"VÉRTICE",
			},
		},
		{
			name: "with_security_findings",
			diagContext: map[string]interface{}{
				"security_findings": []agents.SecurityFinding{
					{Severity: "critical", Category: "auth", Description: "Broken auth"},
					{Severity: "high", Category: "crypto", Description: "Weak encryption"},
				},
			},
			wantContain: []string{
				"Security Findings: 2 issues",
				"[critical] auth: Broken auth",
			},
		},
		{
			name: "with_performance_issues",
			diagContext: map[string]interface{}{
				"performance_issues": []agents.PerformanceIssue{
					{Severity: "high", Description: "Slow DB queries"},
				},
			},
			wantContain: []string{
				"Performance Issues: 1 issues",
			},
		},
		{
			name: "with_coverage_data",
			diagContext: map[string]interface{}{
				"test_coverage": 67.8,
				"dependencies":  15,
			},
			wantContain: []string{
				"Current Test Coverage: 67.8%",
				"Total Dependencies: 15",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			prompt := agent.buildClaudePrompt(input, tt.diagContext)

			if prompt == "" {
				t.Fatal("buildClaudePrompt() returned empty string")
			}

			for _, want := range tt.wantContain {
				if !strings.Contains(prompt, want) {
					t.Errorf("buildClaudePrompt() missing %q", want)
				}
			}

			// Verify JSON structure is mentioned
			if !strings.Contains(prompt, "```json") {
				t.Error("buildClaudePrompt() missing JSON code block")
			}
		})
	}
}

// TestExecute_BasicFlow tests the Execute method with basic flow
func TestExecute_BasicFlow(t *testing.T) {
	// Set environment to simulate vcli-go (not Claude Code)
	os.Setenv("VCLI_RUNTIME", "vcli-go")
	defer os.Unsetenv("VCLI_RUNTIME")

	agent := NewArquitetoAgent(agents.AgentConfig{
		Type:                   agents.AgentTypeArquiteto,
		MaximusOraculoEndpoint: "http://localhost:8080",
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task:    "Design payment gateway",
		Targets: []string{"./services/payment"},
		Context: make(map[string]interface{}),
	}

	output, err := agent.Execute(ctx, input)
	if err != nil {
		t.Fatalf("Execute() error = %v", err)
	}

	if output == nil {
		t.Fatal("Execute() returned nil output")
	}

	// Verify output structure
	if output.AgentType != agents.AgentTypeArquiteto {
		t.Errorf("output.AgentType = %v, want %v", output.AgentType, agents.AgentTypeArquiteto)
	}

	if output.StartedAt.IsZero() {
		t.Error("output.StartedAt is zero")
	}

	if output.CompletedAt.IsZero() {
		t.Error("output.CompletedAt is zero")
	}

	if output.Duration <= 0 {
		t.Error("output.Duration is not positive")
	}

	if output.Metrics == nil {
		t.Error("output.Metrics is nil")
	}

	// Verify result is an ArchitecturePlan
	plan, ok := output.Result.(*agents.ArchitecturePlan)
	if !ok {
		t.Fatal("output.Result is not an ArchitecturePlan")
	}

	if plan.PlanID == "" {
		t.Error("plan.PlanID is empty")
	}

	if plan.Title == "" {
		t.Error("plan.Title is empty")
	}

	// Should have generated ADRs, risks, steps, tests
	if len(plan.ADRs) == 0 {
		t.Error("plan.ADRs is empty")
	}

	if len(plan.Risks) == 0 {
		t.Error("plan.Risks is empty")
	}

	if len(plan.Steps) == 0 {
		t.Error("plan.Steps is empty")
	}

	if len(plan.IntegrationTests) == 0 {
		t.Error("plan.IntegrationTests is empty")
	}

	if plan.EstimatedHours <= 0 {
		t.Error("plan.EstimatedHours is not positive")
	}

	// Verify metrics
	if output.Metrics["adr_count"] != float64(len(plan.ADRs)) {
		t.Errorf("metrics[adr_count] = %v, want %v", output.Metrics["adr_count"], len(plan.ADRs))
	}

	if output.Metrics["risk_count"] != float64(len(plan.Risks)) {
		t.Errorf("metrics[risk_count] = %v, want %v", output.Metrics["risk_count"], len(plan.Risks))
	}

	// Should recommend next agent
	if output.NextAgent != agents.AgentTypeDevSenior {
		t.Errorf("output.NextAgent = %v, want %v", output.NextAgent, agents.AgentTypeDevSenior)
	}
}

// TestExecute_WithDiagnosticContext tests Execute with diagnostic context
func TestExecute_WithDiagnosticContext(t *testing.T) {
	os.Setenv("VCLI_RUNTIME", "vcli-go")
	defer os.Unsetenv("VCLI_RUNTIME")

	agent := NewArquitetoAgent(agents.AgentConfig{
		Type:                   agents.AgentTypeArquiteto,
		MaximusOraculoEndpoint: "http://localhost:8080",
	})

	ctx := context.Background()
	diagnosticResult := &agents.DiagnosticResult{
		SecurityFindings: []agents.SecurityFinding{
			{Severity: "high", Description: "SQL injection risk"},
		},
		TestCoverage: struct {
			LineCoverage   float64
			BranchCoverage float64
			UncoveredFiles []string
		}{
			LineCoverage: 55.0,
		},
		Dependencies: struct {
			Total      int
			Outdated   []string
			Vulnerable []string
			Licenses   map[string]int
		}{
			Total: 25,
		},
	}

	input := agents.AgentInput{
		Task:    "Secure API endpoints",
		Targets: []string{"./api"},
		Context: map[string]interface{}{
			"diagnosticador_output": &agents.AgentOutput{
				Result: diagnosticResult,
			},
		},
	}

	output, err := agent.Execute(ctx, input)
	if err != nil {
		t.Fatalf("Execute() error = %v", err)
	}

	plan, ok := output.Result.(*agents.ArchitecturePlan)
	if !ok {
		t.Fatal("output.Result is not an ArchitecturePlan")
	}

	// Should have identified security risks
	hasSecurityRisk := false
	for _, risk := range plan.Risks {
		if risk.Category == "security" && risk.Severity == "high" {
			hasSecurityRisk = true
			break
		}
	}

	if !hasSecurityRisk {
		t.Error("Execute() did not identify high security risk from diagnostic context")
	}

	// Should have identified test coverage risk
	hasCoverageRisk := false
	for _, risk := range plan.Risks {
		if strings.Contains(strings.ToLower(risk.Description), "coverage") {
			hasCoverageRisk = true
			break
		}
	}

	if !hasCoverageRisk {
		t.Error("Execute() did not identify test coverage risk from diagnostic context")
	}
}

// TestExecute_WithHITL tests Execute with HITL enabled
func TestExecute_WithHITL(t *testing.T) {
	os.Setenv("VCLI_RUNTIME", "vcli-go")
	defer os.Unsetenv("VCLI_RUNTIME")

	agent := NewArquitetoAgent(agents.AgentConfig{
		Type:                   agents.AgentTypeArquiteto,
		MaximusOraculoEndpoint: "http://localhost:8080",
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task:        "Design critical system",
		Targets:     []string{"./critical"},
		Context:     make(map[string]interface{}),
		HITLEnabled: true,
	}

	output, err := agent.Execute(ctx, input)
	if err != nil {
		t.Fatalf("Execute() error = %v", err)
	}

	// Should require HITL approval
	if output.Status != agents.StatusWaitingHITL {
		t.Errorf("output.Status = %v, want %v", output.Status, agents.StatusWaitingHITL)
	}

	if output.HITLDecisionID == "" {
		t.Error("output.HITLDecisionID is empty")
	}

	if !strings.Contains(output.HITLDecisionID, "arch-plan-") {
		t.Errorf("output.HITLDecisionID = %q, want to contain 'arch-plan-'", output.HITLDecisionID)
	}
}

// TestExecute_ClaudeCodePath tests the Claude Code execution path
func TestExecute_ClaudeCodePath(t *testing.T) {
	// Simulate Claude Code environment
	os.Setenv("CLAUDE_CODE", "true")
	defer os.Unsetenv("CLAUDE_CODE")

	agent := NewArquitetoAgent(agents.AgentConfig{
		Type:                   agents.AgentTypeArquiteto,
		MaximusOraculoEndpoint: "http://localhost:8080",
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task:    "Create authentication service",
		Targets: []string{"./auth"},
		Context: make(map[string]interface{}),
	}

	output, err := agent.Execute(ctx, input)
	if err != nil {
		t.Fatalf("Execute() error = %v", err)
	}

	// In Claude Code mode, should return prompt
	if output.ClaudePrompt == "" {
		t.Error("Execute() in Claude Code mode should return ClaudePrompt")
	}

	// Should be waiting for HITL (Claude to process)
	if output.Status != agents.StatusWaitingHITL {
		t.Errorf("output.Status = %v, want %v", output.Status, agents.StatusWaitingHITL)
	}

	// Prompt should contain key elements
	wantInPrompt := []string{
		"ARQUITETO",
		"Create authentication service",
		"Architecture Decision Records",
		"Risk Assessment",
	}

	for _, want := range wantInPrompt {
		if !strings.Contains(output.ClaudePrompt, want) {
			t.Errorf("ClaudePrompt missing %q", want)
		}
	}
}

// Benchmark tests

func BenchmarkNewArquitetoAgent(b *testing.B) {
	config := agents.AgentConfig{
		Type:                   agents.AgentTypeArquiteto,
		MaximusOraculoEndpoint: "http://localhost:8080",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = NewArquitetoAgent(config)
	}
}

func BenchmarkGenerateADRs(b *testing.B) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task: "Implement feature X",
	}
	diagContext := map[string]interface{}{}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		plan := &agents.ArchitecturePlan{
			PlanID: "test-plan",
			ADRs:   make([]agents.ADR, 0),
		}
		_ = agent.generateADRs(ctx, input, diagContext, plan)
	}
}

func BenchmarkAssessRisks(b *testing.B) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	ctx := context.Background()
	input := agents.AgentInput{
		Task: "Deploy service",
	}
	diagContext := map[string]interface{}{
		"security_findings": []agents.SecurityFinding{
			{Severity: "high", Description: "Issue"},
		},
		"test_coverage": 60.0,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		plan := &agents.ArchitecturePlan{
			PlanID: "test-plan",
			Risks:  make([]agents.Risk, 0),
		}
		_ = agent.assessRisks(ctx, input, diagContext, plan)
	}
}

func BenchmarkBuildClaudePrompt(b *testing.B) {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	input := agents.AgentInput{
		Task:    "Create microservice",
		Targets: []string{"./service"},
	}
	diagContext := map[string]interface{}{
		"security_findings": []agents.SecurityFinding{
			{Severity: "high", Description: "Issue"},
		},
		"test_coverage": 75.0,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = agent.buildClaudePrompt(input, diagContext)
	}
}

// Example tests

func ExampleArquitetoAgent_GetCapabilities() {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	capabilities := agent.GetCapabilities()
	fmt.Printf("Agent has %d capabilities\n", len(capabilities))
	// Output is non-deterministic due to implementation details
}

func ExampleArquitetoAgent_Validate() {
	agent := NewArquitetoAgent(agents.AgentConfig{
		Type: agents.AgentTypeArquiteto,
	})

	// Valid input
	validInput := agents.AgentInput{
		Task:    "Design authentication system",
		Targets: []string{"./auth"},
	}

	if err := agent.Validate(validInput); err != nil {
		fmt.Println("Validation failed:", err)
	} else {
		fmt.Println("Valid input")
	}

	// Invalid input
	invalidInput := agents.AgentInput{
		Task: "", // Empty task
	}

	if err := agent.Validate(invalidInput); err != nil {
		fmt.Println("Validation failed: empty task")
	}

	// Output:
	// Valid input
	// Validation failed: empty task
}
