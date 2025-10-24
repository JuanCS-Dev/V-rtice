package arquiteto

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/runtime"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// ArquitetoAgent performs architecture planning and decision making
type ArquitetoAgent struct {
	config agents.AgentConfig
	status agents.AgentStatus
	logger *log.Logger

	// MAXIMUS Oraculo client for predictive analysis
	oraculoClient *maximus.OraculoClient
}

// NewArquitetoAgent creates a new ARQUITETO agent
func NewArquitetoAgent(config agents.AgentConfig) *ArquitetoAgent {
	return &ArquitetoAgent{
		config:        config,
		status:        agents.StatusIdle,
		logger:        log.New(os.Stdout, "[ARQUITETO] ", log.LstdFlags),
		oraculoClient: maximus.NewOraculoClient(config.MaximusOraculoEndpoint, config.AuthToken),
	}
}

// Type returns the agent type
func (a *ArquitetoAgent) Type() agents.AgentType {
	return agents.AgentTypeArquiteto
}

// Name returns the agent name
func (a *ArquitetoAgent) Name() string {
	return "ARQUITETO - Architecture Planning & Decision Making"
}

// GetCapabilities returns the agent's capabilities
func (a *ArquitetoAgent) GetCapabilities() []string {
	return []string{
		"architecture_planning",
		"adr_generation",
		"risk_assessment",
		"integration_test_design",
		"implementation_planning",
		"pattern_detection",
	}
}

// GetStatus returns the current agent status
func (a *ArquitetoAgent) GetStatus() agents.AgentStatus {
	return a.status
}

// Validate checks if the agent can execute with the given input
func (a *ArquitetoAgent) Validate(input agents.AgentInput) error {
	if input.Task == "" {
		return fmt.Errorf("task description is required for architecture planning")
	}

	// Check if we have diagnosticador output in context
	if _, ok := input.Context["diagnosticador_output"]; !ok {
		a.logger.Println("Warning: No diagnosticador output in context - proceeding without analysis data")
	}

	return nil
}

// Execute runs the arquiteto agent
func (a *ArquitetoAgent) Execute(ctx context.Context, input agents.AgentInput) (*agents.AgentOutput, error) {
	a.status = agents.StatusRunning
	startTime := time.Now()

	a.logger.Printf("Starting architecture planning for task: %s", input.Task)

	output := &agents.AgentOutput{
		AgentType:  agents.AgentTypeArquiteto,
		Status:     agents.StatusRunning,
		Artifacts:  make([]string, 0),
		Metrics:    make(map[string]float64),
		Errors:     make([]string, 0),
		StartedAt:  startTime,
		Metadata:   make(map[string]interface{}),
	}

	plan := &agents.ArchitecturePlan{
		PlanID:      uuid.New().String(),
		Title:       input.Task,
		Description: fmt.Sprintf("Architecture plan for: %s", input.Task),
		CreatedAt:   startTime,
		ADRs:        make([]agents.ADR, 0),
		Steps:       make([]agents.ImplementationStep, 0),
		Risks:       make([]agents.Risk, 0),
		IntegrationTests: make([]agents.TestScenario, 0),
	}

	// Step 1: Analyze diagnostic results (if available)
	a.logger.Println("Step 1/6: Analyzing diagnostic context")
	diagnosticContext := a.extractDiagnosticContext(input.Context)

	// CLAUDE CODE INTEGRATION: If running in Claude Code, generate prompt for Sonnet 4.5
	if runtime.IsClaudeCode() {
		a.logger.Println("🤖 Claude Code detected - generating prompt for Sonnet 4.5 processing")
		claudePrompt := a.buildClaudePrompt(input, diagnosticContext)

		// Return output with Claude prompt for processing
		output.ClaudePrompt = claudePrompt
		output.Status = agents.StatusWaitingHITL // Wait for Claude to process
		output.CompletedAt = time.Now()
		output.Duration = output.CompletedAt.Sub(output.StartedAt)
		a.status = agents.StatusCompleted

		a.logger.Println("✅ Prompt generated - waiting for Claude Code processing")
		return output, nil
	}

	// VCLI-GO PATH: Use template-based or Oráculo API planning
	a.logger.Println("📡 vcli-go detected - using template-based planning (TODO: Oráculo API)")

	// Step 2: Generate Architecture Decision Records
	a.logger.Println("Step 2/6: Generating Architecture Decision Records")
	if err := a.generateADRs(ctx, input, diagnosticContext, plan); err != nil {
		output.Errors = append(output.Errors, fmt.Sprintf("ADR generation failed: %v", err))
	}

	// Step 3: Perform risk assessment
	a.logger.Println("Step 3/6: Performing risk assessment")
	if err := a.assessRisks(ctx, input, diagnosticContext, plan); err != nil {
		output.Errors = append(output.Errors, fmt.Sprintf("risk assessment failed: %v", err))
	}

	// Step 4: Generate implementation plan
	a.logger.Println("Step 4/6: Generating implementation plan")
	if err := a.generateImplementationPlan(ctx, input, diagnosticContext, plan); err != nil {
		output.Errors = append(output.Errors, fmt.Sprintf("implementation planning failed: %v", err))
	}

	// Step 5: Design integration tests
	a.logger.Println("Step 5/6: Designing integration test scenarios")
	if err := a.designIntegrationTests(ctx, input, plan); err != nil {
		output.Errors = append(output.Errors, fmt.Sprintf("test design failed: %v", err))
	}

	// Step 6: Calculate effort estimate
	a.logger.Println("Step 6/6: Calculating effort estimate")
	a.calculateEffortEstimate(plan)

	// Generate summary
	plan.Summary = a.generateSummary(plan)

	// Populate output
	output.Result = plan
	output.Metrics["adr_count"] = float64(len(plan.ADRs))
	output.Metrics["risk_count"] = float64(len(plan.Risks))
	output.Metrics["implementation_steps"] = float64(len(plan.Steps))
	output.Metrics["estimated_hours"] = plan.EstimatedHours

	// Determine next agent
	output.NextAgent = agents.AgentTypeDevSenior

	// HITL Required - Architecture changes need approval
	if input.HITLEnabled {
		output.Status = agents.StatusWaitingHITL
		output.HITLDecisionID = fmt.Sprintf("arch-plan-%s", plan.PlanID[:8])
		a.logger.Printf("HITL approval required for architecture plan: %s", output.HITLDecisionID)
	} else {
		output.Status = agents.StatusCompleted
	}

	output.CompletedAt = time.Now()
	output.Duration = output.CompletedAt.Sub(output.StartedAt)
	a.status = agents.StatusCompleted

	a.logger.Printf("Architecture planning complete: %d ADRs, %d risks, %d steps",
		len(plan.ADRs), len(plan.Risks), len(plan.Steps))

	return output, nil
}

// extractDiagnosticContext extracts relevant data from DIAGNOSTICADOR output
func (a *ArquitetoAgent) extractDiagnosticContext(context map[string]interface{}) map[string]interface{} {
	diagnosticContext := make(map[string]interface{})

	if diagOutput, ok := context["diagnosticador_output"]; ok {
		if output, ok := diagOutput.(*agents.AgentOutput); ok {
			if result, ok := output.Result.(*agents.DiagnosticResult); ok {
				diagnosticContext["security_findings"] = result.SecurityFindings
				diagnosticContext["performance_issues"] = result.PerformanceIssues
				diagnosticContext["test_coverage"] = result.TestCoverage.LineCoverage
				diagnosticContext["dependencies"] = result.Dependencies.Total
			}
		}
	}

	return diagnosticContext
}

// generateADRs generates Architecture Decision Records
func (a *ArquitetoAgent) generateADRs(ctx context.Context, input agents.AgentInput, diagContext map[string]interface{}, plan *agents.ArchitecturePlan) error {
	// ADR 1: Main architectural decision for the task
	mainADR := agents.ADR{
		ID:          fmt.Sprintf("ADR-%s-001", plan.PlanID[:8]),
		Title:       fmt.Sprintf("Architecture for %s", input.Task),
		Context:     a.buildADRContext(input, diagContext),
		Decision:    a.buildADRDecision(input, diagContext),
		Consequences: a.buildADRConsequences(input, diagContext),
		Status:      "proposed",
		CreatedAt:   time.Now(),
	}
	plan.ADRs = append(plan.ADRs, mainADR)

	// ADR 2: Integration strategy
	if len(diagContext) > 0 {
		integrationADR := agents.ADR{
			ID:          fmt.Sprintf("ADR-%s-002", plan.PlanID[:8]),
			Title:       "Integration Strategy with Existing Systems",
			Context:     "Integration with VÉRTICE ecosystem (MAXIMUS, Immunis, Orchestration)",
			Decision:    "Use existing service client patterns; follow OrchestrationEngine model",
			Consequences: []string{
				"Maintains architectural consistency",
				"Leverages proven patterns",
				"Reduces integration complexity",
			},
			Status:    "proposed",
			CreatedAt: time.Now(),
		}
		plan.ADRs = append(plan.ADRs, integrationADR)
	}

	// ADR 3: Testing strategy
	testingADR := agents.ADR{
		ID:          fmt.Sprintf("ADR-%s-003", plan.PlanID[:8]),
		Title:       "Testing Strategy",
		Context:     "Ensure reliability and maintainability of new implementation",
		Decision:    "Implement unit tests, integration tests, and functional tests; maintain >80% coverage",
		Consequences: []string{
			"High confidence in code quality",
			"Easier maintenance and refactoring",
			"Catches regressions early",
		},
		Status:    "proposed",
		CreatedAt: time.Now(),
	}
	plan.ADRs = append(plan.ADRs, testingADR)

	return nil
}

// buildADRContext builds the context section of an ADR
func (a *ArquitetoAgent) buildADRContext(input agents.AgentInput, diagContext map[string]interface{}) string {
	context := fmt.Sprintf("Task: %s\n\n", input.Task)

	if securityFindings, ok := diagContext["security_findings"]; ok {
		if findings, ok := securityFindings.([]agents.SecurityFinding); ok && len(findings) > 0 {
			context += fmt.Sprintf("Security Considerations: %d findings identified\n", len(findings))
		}
	}

	if perfIssues, ok := diagContext["performance_issues"]; ok {
		if issues, ok := perfIssues.([]agents.PerformanceIssue); ok && len(issues) > 0 {
			context += fmt.Sprintf("Performance Considerations: %d issues identified\n", len(issues))
		}
	}

	if coverage, ok := diagContext["test_coverage"]; ok {
		context += fmt.Sprintf("Current Test Coverage: %.1f%%\n", coverage)
	}

	return context
}

// buildADRDecision builds the decision section of an ADR
func (a *ArquitetoAgent) buildADRDecision(input agents.AgentInput, diagContext map[string]interface{}) string {
	decision := fmt.Sprintf("Implement %s following VÉRTICE architectural patterns:\n", input.Task)
	decision += "- Use existing service client patterns\n"
	decision += "- Integrate with MAXIMUS services where appropriate\n"
	decision += "- Follow Padrão Pagani quality standards\n"
	decision += "- Implement comprehensive error handling\n"

	if securityFindings, ok := diagContext["security_findings"]; ok {
		if findings, ok := securityFindings.([]agents.SecurityFinding); ok && len(findings) > 0 {
			decision += "- Address all security findings before implementation\n"
		}
	}

	return decision
}

// buildADRConsequences builds the consequences section of an ADR
func (a *ArquitetoAgent) buildADRConsequences(input agents.AgentInput, diagContext map[string]interface{}) []string {
	consequences := []string{
		"Maintains consistency with VÉRTICE ecosystem",
		"Enables seamless integration with existing services",
		"Provides foundation for future enhancements",
	}

	if coverage, ok := diagContext["test_coverage"]; ok {
		if cov, ok := coverage.(float64); ok && cov < 80.0 {
			consequences = append(consequences, "Requires test coverage improvement to meet quality gates")
		}
	}

	return consequences
}

// assessRisks performs risk assessment
func (a *ArquitetoAgent) assessRisks(ctx context.Context, input agents.AgentInput, diagContext map[string]interface{}, plan *agents.ArchitecturePlan) error {
	// Risk 1: Security findings
	if securityFindings, ok := diagContext["security_findings"]; ok {
		if findings, ok := securityFindings.([]agents.SecurityFinding); ok && len(findings) > 0 {
			criticalCount := 0
			for _, f := range findings {
				if f.Severity == "critical" || f.Severity == "high" {
					criticalCount++
				}
			}

			if criticalCount > 0 {
				risk := agents.Risk{
					Severity:    "high",
					Category:    "security",
					Description: fmt.Sprintf("%d critical/high security findings must be addressed", criticalCount),
					Impact:      "Potential security vulnerabilities in production",
					Mitigation:  "Address all critical findings before implementation; implement security review process",
					Probability: 0.8,
				}
				plan.Risks = append(plan.Risks, risk)
			}
		}
	}

	// Risk 2: Test coverage
	if coverage, ok := diagContext["test_coverage"]; ok {
		if cov, ok := coverage.(float64); ok && cov < 80.0 {
			risk := agents.Risk{
				Severity:    "medium",
				Category:    "technical",
				Description: fmt.Sprintf("Low test coverage (%.1f%%) increases risk of regressions", cov),
				Impact:      "Potential bugs in production; difficult refactoring",
				Mitigation:  "Increase test coverage to >80% before major changes",
				Probability: 0.6,
			}
			plan.Risks = append(plan.Risks, risk)
		}
	}

	// Risk 3: Integration complexity
	integrationRisk := agents.Risk{
		Severity:    "medium",
		Category:    "technical",
		Description: "Integration with multiple VÉRTICE services increases complexity",
		Impact:      "Potential integration failures; increased development time",
		Mitigation:  "Follow existing patterns; implement integration tests; use OrchestrationEngine model",
		Probability: 0.4,
	}
	plan.Risks = append(plan.Risks, integrationRisk)

	return nil
}

// generateImplementationPlan generates detailed implementation steps
func (a *ArquitetoAgent) generateImplementationPlan(ctx context.Context, input agents.AgentInput, diagContext map[string]interface{}, plan *agents.ArchitecturePlan) error {
	stepNumber := 1

	// Step: Address security findings (if any)
	if securityFindings, ok := diagContext["security_findings"]; ok {
		if findings, ok := securityFindings.([]agents.SecurityFinding); ok && len(findings) > 0 {
			step := agents.ImplementationStep{
				StepNumber:  stepNumber,
				Description: "Address security findings from DIAGNOSTICADOR",
				AgentType:   agents.AgentTypeDevSenior,
				Inputs: map[string]interface{}{
					"security_findings": findings,
				},
				Outputs:       []string{"security_fixes.patch"},
				EstimatedTime: time.Duration(len(findings)) * 30 * time.Minute,
				HITLRequired:  true,
			}
			plan.Steps = append(plan.Steps, step)
			stepNumber++
		}
	}

	// Step: Core implementation
	step := agents.ImplementationStep{
		StepNumber:  stepNumber,
		Description: fmt.Sprintf("Implement %s", input.Task),
		AgentType:   agents.AgentTypeDevSenior,
		Inputs: map[string]interface{}{
			"task":         input.Task,
			"architecture": plan.ADRs,
		},
		Outputs:       []string{"implementation_complete"},
		EstimatedTime: 2 * time.Hour,
		HITLRequired:  true,
	}
	plan.Steps = append(plan.Steps, step)
	stepNumber++

	// Step: Testing
	step = agents.ImplementationStep{
		StepNumber:  stepNumber,
		Description: "Execute comprehensive tests and validate quality gates",
		AgentType:   agents.AgentTypeTester,
		Inputs: map[string]interface{}{
			"implementation": "implementation_complete",
		},
		Outputs:       []string{"test_report", "coverage_report"},
		EstimatedTime: 1 * time.Hour,
		HITLRequired:  true,
	}
	plan.Steps = append(plan.Steps, step)

	return nil
}

// designIntegrationTests designs integration test scenarios
func (a *ArquitetoAgent) designIntegrationTests(ctx context.Context, input agents.AgentInput, plan *agents.ArchitecturePlan) error {
	// Test 1: Basic functionality
	test := agents.TestScenario{
		Name:        "Basic Functionality Test",
		Description: fmt.Sprintf("Verify basic functionality of %s", input.Task),
		Type:        "integration",
		PreConditions: []string{
			"System dependencies available",
			"Test environment configured",
		},
		Steps: []string{
			"Initialize system",
			"Execute core functionality",
			"Verify expected behavior",
			"Check error handling",
		},
		Expected: "All functionality works as specified; errors handled gracefully",
	}
	plan.IntegrationTests = append(plan.IntegrationTests, test)

	// Test 2: MAXIMUS integration
	test = agents.TestScenario{
		Name:        "MAXIMUS Integration Test",
		Description: "Verify integration with MAXIMUS services",
		Type:        "integration",
		PreConditions: []string{
			"MAXIMUS services running",
			"Authentication configured",
		},
		Steps: []string{
			"Connect to MAXIMUS",
			"Execute service calls",
			"Verify responses",
			"Test error scenarios",
		},
		Expected: "Integration with MAXIMUS services works correctly",
	}
	plan.IntegrationTests = append(plan.IntegrationTests, test)

	// Test 3: End-to-end workflow
	test = agents.TestScenario{
		Name:        "End-to-End Workflow Test",
		Description: "Verify complete workflow execution",
		Type:        "e2e",
		PreConditions: []string{
			"All services running",
			"Test data prepared",
		},
		Steps: []string{
			"Execute full workflow",
			"Verify each step completes",
			"Check final state",
			"Validate artifacts",
		},
		Expected: "Complete workflow executes successfully",
	}
	plan.IntegrationTests = append(plan.IntegrationTests, test)

	return nil
}

// calculateEffortEstimate calculates estimated effort in hours
func (a *ArquitetoAgent) calculateEffortEstimate(plan *agents.ArchitecturePlan) {
	var totalHours float64

	for _, step := range plan.Steps {
		totalHours += step.EstimatedTime.Hours()
	}

	// Add buffer for testing and review (30%)
	totalHours *= 1.3

	plan.EstimatedHours = totalHours
}

// generateSummary generates a summary of the architecture plan
func (a *ArquitetoAgent) generateSummary(plan *agents.ArchitecturePlan) string {
	summary := fmt.Sprintf("Architecture Plan: %s\n", plan.Title)
	summary += fmt.Sprintf("\nADRs Generated: %d\n", len(plan.ADRs))
	summary += fmt.Sprintf("Risks Identified: %d\n", len(plan.Risks))
	summary += fmt.Sprintf("Implementation Steps: %d\n", len(plan.Steps))
	summary += fmt.Sprintf("Integration Tests: %d\n", len(plan.IntegrationTests))
	summary += fmt.Sprintf("Estimated Effort: %.1f hours\n", plan.EstimatedHours)

	return summary
}

// buildClaudePrompt builds a structured prompt for Claude Sonnet 4.5 processing
func (a *ArquitetoAgent) buildClaudePrompt(input agents.AgentInput, diagnosticContext map[string]interface{}) string {
	prompt := fmt.Sprintf(`You are ARQUITETO, a world-class software architect agent specialized in creating detailed architecture plans, ADRs (Architecture Decision Records), and implementation roadmaps.

**Task:** %s

**Target Paths:** %v

**Diagnostic Context:**
`, input.Task, input.Targets)

	// Add diagnostic findings if available
	if securityFindings, ok := diagnosticContext["security_findings"]; ok {
		if findings, ok := securityFindings.([]agents.SecurityFinding); ok && len(findings) > 0 {
			prompt += fmt.Sprintf("- Security Findings: %d issues identified\n", len(findings))
			for i, f := range findings {
				if i < 5 { // Show first 5
					prompt += fmt.Sprintf("  • [%s] %s: %s\n", f.Severity, f.Category, f.Description)
				}
			}
			if len(findings) > 5 {
				prompt += fmt.Sprintf("  ... and %d more\n", len(findings)-5)
			}
		}
	}

	if perfIssues, ok := diagnosticContext["performance_issues"]; ok {
		if issues, ok := perfIssues.([]agents.PerformanceIssue); ok && len(issues) > 0 {
			prompt += fmt.Sprintf("- Performance Issues: %d issues identified\n", len(issues))
		}
	}

	if coverage, ok := diagnosticContext["test_coverage"]; ok {
		prompt += fmt.Sprintf("- Current Test Coverage: %.1f%%\n", coverage)
	}

	if deps, ok := diagnosticContext["dependencies"]; ok {
		prompt += fmt.Sprintf("- Total Dependencies: %v\n", deps)
	}

	prompt += `

**Your Mission:**

Generate a comprehensive architecture plan following **Padrão Pagani** (zero compromises) and **VÉRTICE architectural patterns**. The plan MUST include:

1. **Architecture Decision Records (ADRs)** - At least 3 ADRs covering:
   - Main architectural approach for the task
   - Integration strategy with existing VÉRTICE ecosystem (MAXIMUS, Immunis, etc.)
   - Testing strategy and quality gates

2. **Risk Assessment** - Identify and analyze:
   - Security risks (based on diagnostic findings)
   - Technical risks (complexity, integration, dependencies)
   - Operational risks (deployment, maintenance)
   - For each risk: severity, impact, mitigation strategy, probability

3. **Implementation Steps** - Detailed step-by-step roadmap:
   - Each step with clear description
   - Estimated time per step
   - Required agent (DEV SENIOR, TESTER, etc.)
   - HITL checkpoints where human approval is required
   - Input/output artifacts for each step

4. **Integration Test Scenarios** - At least 3 test scenarios:
   - Basic functionality test
   - MAXIMUS/Immunis integration test
   - End-to-end workflow test
   - Each with preconditions, steps, and expected outcomes

5. **Effort Estimate** - Calculate total estimated hours (include 30% buffer)

6. **Complexity Score** - Rate 1-10 with justification

**Output Format:**

Return your analysis in the following JSON structure:

` + "```json" + `
{
  "plan_id": "PLAN-XXXXXXXX",
  "title": "Architecture for [task]",
  "description": "Brief description",
  "adrs": [
    {
      "id": "ADR-001",
      "title": "...",
      "context": "Why this decision is needed",
      "decision": "What we decided",
      "consequences": ["Pro 1", "Pro 2", "Con 1"],
      "status": "proposed"
    }
  ],
  "risks": [
    {
      "severity": "high|medium|low",
      "category": "security|technical|operational",
      "description": "...",
      "impact": "...",
      "mitigation": "...",
      "probability": 0.0-1.0
    }
  ],
  "implementation_steps": [
    {
      "step_number": 1,
      "description": "...",
      "agent_type": "dev_senior|tester|diagnosticador",
      "estimated_hours": 2.5,
      "hitl_required": true,
      "inputs": ["..."],
      "outputs": ["..."]
    }
  ],
  "integration_tests": [
    {
      "name": "...",
      "description": "...",
      "type": "integration|e2e|unit",
      "preconditions": ["..."],
      "steps": ["..."],
      "expected": "..."
    }
  ],
  "estimated_hours": 8.5,
  "complexity": 7,
  "complexity_justification": "..."
}
` + "```" + `

**Important Guidelines:**
- Follow VÉRTICE patterns: service clients, OrchestrationEngine model, Padrão Pagani quality
- Be specific and actionable - no placeholders or TODOs
- Consider existing codebase structure and dependencies
- Prioritize security and reliability
- Include HITL checkpoints for critical decisions
- Estimate realistically (humans tend to underestimate by 2-3x)

Generate the architecture plan now.`

	return prompt
}
