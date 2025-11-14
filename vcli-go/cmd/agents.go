package cmd

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/arquiteto"
	"github.com/verticedev/vcli-go/internal/agents/dev_senior"
	"github.com/verticedev/vcli-go/internal/agents/diagnosticador"
	"github.com/verticedev/vcli-go/internal/agents/tester"
	"github.com/verticedev/vcli-go/internal/agents/workflow"
	"github.com/verticedev/vcli-go/internal/visual"
	"gopkg.in/yaml.v3"
)

var (
	agentsWorkspacePath string
	agentsTask          string
	agentsTargets       []string
	agentsWorkflow      string
	agentsOutputFormat  string
	agentsHITLEnabled   bool
	agentsContextFile   string

	// FASE 4.6: Anthropic Patterns - CLI flags
	agentsEnableRetry      bool
	agentsMaxRetries       int
	agentsBackoffStrategy  string
	agentsEnableReflection bool
	agentsSkipPlanning     bool
)

// agentsCmd represents the agents command (Agent Smith)
var agentsCmd = &cobra.Command{
	Use:   "agents",
	Short: "Agent Smith - Autonomous Development Framework",
	Long: `Agent Smith: Autonomous multi-agent development system for VÉRTICE.

The Agent Smith framework provides four specialized autonomous agents:
  • DIAGNOSTICADOR - Code analysis & security scanning
  • ARQUITETO      - Architecture planning & decision making
  • DEV SENIOR     - Autonomous code implementation
  • TESTER         - Validation & quality assurance

Examples:
  # Run full development cycle
  vcli agents run full-cycle --task "Add Redis caching to Governance API"

  # Run individual agent
  vcli agents diagnosticador analyze --targets ./internal/maximus/

  # List available agents
  vcli agents list

  # Get agent status
  vcli agents status`,
}

// agentsListCmd lists available agents
var agentsListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available agents and their capabilities",
	RunE:  runAgentsList,
}

func runAgentsList(cmd *cobra.Command, args []string) error {
	styles := visual.DefaultStyles()

	fmt.Println(styles.Bold.Render("🤖 Agent Smith - Available Agents"))
	fmt.Println()

	agents := []struct {
		Type         string
		Name         string
		Capabilities []string
		Status       string
	}{
		{
			Type: "diagnosticador",
			Name: "DIAGNOSTICADOR",
			Capabilities: []string{
				"Static code analysis",
				"Security vulnerability scanning",
				"Code quality metrics",
				"Dependency analysis",
				"Test coverage analysis",
			},
			Status: "✅ Active",
		},
		{
			Type: "arquiteto",
			Name: "ARQUITETO",
			Capabilities: []string{
				"Architecture planning",
				"ADR generation",
				"Risk assessment",
				"Integration test design",
				"Implementation planning",
			},
			Status: "✅ Active",
		},
		{
			Type: "dev_senior",
			Name: "DEV SENIOR",
			Capabilities: []string{
				"Autonomous code generation",
				"File operations",
				"Git operations",
				"Code refactoring",
			},
			Status: "✅ Active",
		},
		{
			Type: "tester",
			Name: "TESTER",
			Capabilities: []string{
				"Test execution",
				"Coverage analysis",
				"Regression detection",
				"Quality gate validation",
			},
			Status: "✅ Active",
		},
	}

	for _, agent := range agents {
		fmt.Printf("%s %s\n", styles.Accent.Render("●"), styles.Bold.Render(agent.Name))
		fmt.Printf("  Type:   %s\n", agent.Type)
		fmt.Printf("  Status: %s\n", agent.Status)
		fmt.Printf("  Capabilities:\n")
		for _, cap := range agent.Capabilities {
			fmt.Printf("    • %s\n", cap)
		}
		fmt.Println()
	}

	return nil
}

// agentsArquitetoCmd represents the arquiteto agent commands
var agentsArquitetoCmd = &cobra.Command{
	Use:   "arquiteto",
	Short: "ARQUITETO - Architecture planning & decision making",
	Long: `ARQUITETO Agent: Architecture planning and decision making.

Capabilities:
  • Architecture Decision Records (ADR) generation
  • Risk assessment
  • Implementation planning
  • Integration test design
  • Effort estimation

Examples:
  # Generate architecture plan
  vcli agents arquiteto plan --task "Add Redis caching to API"

  # Plan with diagnostic context
  vcli agents arquiteto plan --task "Implement rate limiting" --context diagnostics.json`,
}

var agentsArquitetoPlanCmd = &cobra.Command{
	Use:   "plan",
	Short: "Generate architecture plan for a task",
	RunE:  runArquitetoPlan,
}

func runArquitetoPlan(cmd *cobra.Command, args []string) error {
	styles := visual.DefaultStyles()

	fmt.Println(styles.Bold.Render("📐 ARQUITETO - Architecture Planning"))
	fmt.Println()

	if agentsTask == "" {
		return fmt.Errorf("--task is required")
	}

	// Load configuration
	config, err := loadAgentConfig()
	if err != nil {
		return fmt.Errorf("failed to load agent config: %w", err)
	}

	// Create agent
	agent := arquiteto.NewArquitetoAgent(config)

	// Prepare input
	input := agents.AgentInput{
		Task:        agentsTask,
		Targets:     agentsTargets,
		Context:     make(map[string]interface{}),
		Config:      make(map[string]interface{}),
		HITLEnabled: agentsHITLEnabled,
	}

	// Validate
	if err := agent.Validate(input); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// Execute
	ctx := context.Background()
	fmt.Printf("%s Planning architecture for: %s\n", styles.Info.Render("ℹ️"), agentsTask)
	fmt.Println()

	output, err := agent.Execute(ctx, input)
	if err != nil {
		return fmt.Errorf("planning failed: %w", err)
	}

	// Display results
	if result, ok := output.Result.(*agents.ArchitecturePlan); ok {
		displayArchitecturePlan(result, styles)
	}

	// Display summary
	fmt.Println()
	if output.Status == agents.StatusWaitingHITL {
		fmt.Println(styles.Warning.Render("⏸️  Architecture Plan Requires HITL Approval"))
		fmt.Printf("Decision ID: %s\n", output.HITLDecisionID)
		fmt.Println()
		fmt.Println("To approve:")
		fmt.Printf("  vcli maximus approve %s --session-id <session>\n", output.HITLDecisionID)
	} else {
		fmt.Println(styles.Success.Render("✅ Planning Complete"))
	}
	fmt.Printf("Duration: %v\n", output.Duration)
	fmt.Printf("Status: %s\n", output.Status)

	return nil
}

func displayArchitecturePlan(plan *agents.ArchitecturePlan, styles *visual.Styles) {
	// Header
	fmt.Println(styles.Bold.Render(fmt.Sprintf("Architecture Plan: %s", plan.Title)))
	fmt.Printf("Plan ID: %s\n", plan.PlanID)
	fmt.Printf("Created: %s\n", plan.CreatedAt.Format("2006-01-02 15:04:05"))
	fmt.Println()

	// ADRs
	if len(plan.ADRs) > 0 {
		fmt.Println(styles.Bold.Render("📋 Architecture Decision Records"))
		for i, adr := range plan.ADRs {
			fmt.Printf("\n  [%d] %s\n", i+1, styles.Accent.Render(adr.Title))
			fmt.Printf("      ID: %s | Status: %s\n", adr.ID, adr.Status)
			fmt.Printf("      Decision: %s\n", strings.Split(adr.Decision, "\n")[0])
			if len(adr.Consequences) > 0 {
				fmt.Printf("      Consequences: %d items\n", len(adr.Consequences))
			}
		}
		fmt.Println()
	}

	// Risks
	if len(plan.Risks) > 0 {
		fmt.Println(styles.Bold.Render("⚠️  Risk Assessment"))
		for i, risk := range plan.Risks {
			severity := risk.Severity
			icon := "ℹ️"
			if severity == "critical" || severity == "high" {
				icon = "🚨"
			}
			fmt.Printf("  %s [%d] %s - %s\n", icon, i+1, strings.ToUpper(severity), risk.Description)
			fmt.Printf("      Impact: %s\n", risk.Impact)
			fmt.Printf("      Mitigation: %s\n", risk.Mitigation)
			fmt.Printf("      Probability: %.0f%%\n", risk.Probability*100)
		}
		fmt.Println()
	}

	// Implementation Steps
	if len(plan.Steps) > 0 {
		fmt.Println(styles.Bold.Render("📝 Implementation Plan"))
		for _, step := range plan.Steps {
			fmt.Printf("  Step %d: %s\n", step.StepNumber, step.Description)
			fmt.Printf("          Agent: %s | Estimated: %v\n", step.AgentType, step.EstimatedTime)
			if step.HITLRequired {
				fmt.Printf("          HITL: %s\n", styles.Warning.Render("Required"))
			}
		}
		fmt.Println()
	}

	// Integration Tests
	if len(plan.IntegrationTests) > 0 {
		fmt.Println(styles.Bold.Render("🧪 Integration Tests"))
		for i, test := range plan.IntegrationTests {
			fmt.Printf("  [%d] %s (%s)\n", i+1, test.Name, test.Type)
			fmt.Printf("      Description: %s\n", test.Description)
		}
		fmt.Println()
	}

	// Effort Estimate
	fmt.Println(styles.Bold.Render("⏱️  Effort Estimate"))
	fmt.Printf("  Total: %.1f hours\n", plan.EstimatedHours)
	fmt.Println()

	// Summary
	fmt.Println(styles.Bold.Render("📊 Summary"))
	fmt.Println(plan.Summary)
}

// ============================================================================
// DEV SENIOR COMMANDS
// ============================================================================

// agentsDevSeniorCmd represents the dev-senior agent commands
var agentsDevSeniorCmd = &cobra.Command{
	Use:   "dev-senior",
	Short: "DEV SENIOR - Autonomous code implementation",
	Long: `DEV SENIOR Agent: Autonomous code generation and implementation.

Capabilities:
  • Autonomous code generation
  • File operations (create, modify, delete)
  • Git operations (branch, commit)
  • Code formatting (gofmt, goimports)
  • Compilation validation
  • Basic test execution
  • MAXIMUS Oraculo integration

Examples:
  # Implement a task
  vcli agents dev-senior implement --task "Add Redis caching layer"

  # Implement with architecture plan
  vcli agents dev-senior implement --task "Add rate limiting" --plan arch-plan-xyz

  # Implement without HITL (for testing)
  vcli agents dev-senior implement --task "Refactor function" --hitl=false`,
}

var agentsDevSeniorImplementCmd = &cobra.Command{
	Use:   "implement",
	Short: "Implement code changes for a task",
	RunE:  runDevSeniorImplement,
}

func runDevSeniorImplement(cmd *cobra.Command, args []string) error {
	styles := visual.DefaultStyles()

	fmt.Println(styles.Bold.Render("💻 DEV SENIOR - Code Implementation"))
	fmt.Println()

	if agentsTask == "" {
		return fmt.Errorf("--task is required")
	}

	// Load configuration
	config, err := loadAgentConfig()
	if err != nil {
		return fmt.Errorf("failed to load agent config: %w", err)
	}

	// Create agent
	agent := dev_senior.NewDevSeniorAgent(config)

	// Prepare input
	input := agents.AgentInput{
		Task:        agentsTask,
		Targets:     agentsTargets,
		Context:     make(map[string]interface{}),
		Config:      make(map[string]interface{}),
		HITLEnabled: agentsHITLEnabled,
	}

	// FASE 4.6: Pass Anthropic patterns config to agent
	if agentsSkipPlanning {
		input.Config["skip_planning"] = true
	}

	// Load context from file if provided
	if agentsContextFile != "" {
		// TODO: Load context from JSON file
		fmt.Printf("%s Loading context from: %s\n", styles.Info.Render("ℹ️"), agentsContextFile)
	}

	fmt.Printf("%s Implementing: %s\n", styles.Info.Render("ℹ️"), agentsTask)
	fmt.Println()

	// Execute agent
	output, err := agent.Execute(context.Background(), input)
	if err != nil {
		return fmt.Errorf("implementation failed: %w", err)
	}

	// Display result
	result, ok := output.Result.(*agents.ImplementationResult)
	if !ok {
		return fmt.Errorf("invalid result type")
	}

	displayImplementationResult(result, styles)

	// Show HITL status
	fmt.Println()
	if output.Status == agents.StatusWaitingHITL {
		fmt.Println(styles.Warning.Render("⏸️  Implementation Requires HITL Approval"))
		fmt.Printf("Decision ID: impl-%s\n", result.TaskDescription[:12])
		fmt.Println()
		fmt.Println("To approve:")
		fmt.Printf("  vcli maximus approve impl-%s --session-id <session>\n", result.TaskDescription[:12])
	} else {
		fmt.Println(styles.Success.Render("✅ Implementation Complete"))
	}

	// Show metrics
	fmt.Printf("Duration: %v\n", output.Duration)
	fmt.Printf("Status: %s\n", output.Status)

	return nil
}

func displayImplementationResult(result *agents.ImplementationResult, styles *visual.Styles) {
	// Header
	fmt.Println(styles.Bold.Render(fmt.Sprintf("Implementation: %s", result.TaskDescription)))
	fmt.Println()

	// File Changes
	if len(result.FilesCreated) > 0 || len(result.FilesModified) > 0 || len(result.FilesDeleted) > 0 {
		fmt.Println(styles.Bold.Render("📁 File Changes"))
		if len(result.FilesCreated) > 0 {
			fmt.Printf("  %s Created: %d files\n", styles.Success.Render("✅"), len(result.FilesCreated))
			for _, f := range result.FilesCreated {
				fmt.Printf("    • %s\n", f.FilePath)
			}
		}
		if len(result.FilesModified) > 0 {
			fmt.Printf("  %s Modified: %d files\n", styles.Info.Render("ℹ️"), len(result.FilesModified))
			for _, f := range result.FilesModified {
				fmt.Printf("    • %s\n", f.FilePath)
			}
		}
		if len(result.FilesDeleted) > 0 {
			fmt.Printf("  %s Deleted: %d files\n", styles.Warning.Render("⚠️"), len(result.FilesDeleted))
			for _, f := range result.FilesDeleted {
				fmt.Printf("    • %s\n", f.FilePath)
			}
		}
		fmt.Println()
	}

	// Git Info
	if result.GitBranch != "" {
		fmt.Println(styles.Bold.Render("🌿 Git Information"))
		fmt.Printf("  Branch: %s\n", styles.Accent.Render(result.GitBranch))
		if result.GitCommit != "" {
			fmt.Printf("  Commit: %s\n", result.GitCommit[:8])
		}
		fmt.Println()
	}

	// Compilation
	fmt.Println(styles.Bold.Render("🔨 Compilation"))
	if result.CompilationSuccess {
		fmt.Printf("  %s Build successful\n", styles.Success.Render("✅"))
	} else {
		fmt.Printf("  %s Build failed\n", styles.Error.Render("❌"))
		if len(result.CompilationErrors) > 0 {
			fmt.Printf("  Errors: %d\n", len(result.CompilationErrors))
			for i, err := range result.CompilationErrors {
				if i < 5 { // Show first 5 errors
					fmt.Printf("    • %s\n", err)
				}
			}
			if len(result.CompilationErrors) > 5 {
				fmt.Printf("    ... and %d more\n", len(result.CompilationErrors)-5)
			}
		}
	}
	fmt.Println()

	// Tests
	if result.TestsExecuted > 0 {
		fmt.Println(styles.Bold.Render("🧪 Tests"))
		fmt.Printf("  Total: %d\n", result.TestsExecuted)
		if result.TestsPassed > 0 {
			fmt.Printf("  %s Passed: %d\n", styles.Success.Render("✅"), result.TestsPassed)
		}
		if result.TestsFailed > 0 {
			fmt.Printf("  %s Failed: %d\n", styles.Error.Render("❌"), result.TestsFailed)
		}
		fmt.Println()
	}

	// Code Quality
	fmt.Println(styles.Bold.Render("📊 Code Quality"))
	fmt.Printf("  Score: %.1f/100\n", result.CodeQualityScore)
	fmt.Println()

	// Recommendations
	if len(result.Recommendations) > 0 {
		fmt.Println(styles.Bold.Render("💡 Recommendations"))
		for _, rec := range result.Recommendations {
			fmt.Printf("  %s\n", rec)
		}
		fmt.Println()
	}

	// Summary
	fmt.Println(styles.Bold.Render("📝 Summary"))
	fmt.Printf("Implementation Complete:\n")
	fmt.Printf("- Files Changed: %d created, %d modified, %d deleted\n",
		len(result.FilesCreated), len(result.FilesModified), len(result.FilesDeleted))
	fmt.Printf("- Compilation: %v\n", result.CompilationSuccess)
	fmt.Printf("- Tests: %d/%d passed\n", result.TestsPassed, result.TestsExecuted)
	fmt.Printf("- Quality Score: %.1f/100\n", result.CodeQualityScore)
}

// ============================================================================
// TESTER COMMANDS
// ============================================================================

// agentsTesterCmd represents the tester agent commands
var agentsTesterCmd = &cobra.Command{
	Use:   "tester",
	Short: "TESTER - Autonomous testing & quality validation",
	Long: `TESTER Agent: Autonomous testing and quality assurance.

Capabilities:
  • Unit test execution
  • Integration test execution
  • Coverage analysis
  • Performance benchmarking
  • Quality gate validation
  • Regression detection
  • MAXIMUS Predict integration

Examples:
  # Run tests and validate quality
  vcli agents tester validate --targets ./...

  # Run tests with coverage
  vcli agents tester validate --targets ./internal/ --coverage

  # Validate with quality gates
  vcli agents tester validate --targets ./... --hitl`,
}

var agentsTesterValidateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Run tests and validate quality gates",
	RunE:  runTesterValidate,
}

func runTesterValidate(cmd *cobra.Command, args []string) error {
	styles := visual.DefaultStyles()

	fmt.Println(styles.Bold.Render("🧪 TESTER - Test Validation"))
	fmt.Println()

	if agentsTask == "" {
		agentsTask = "Validate code quality and tests"
	}

	// Load configuration
	config, err := loadAgentConfig()
	if err != nil {
		return fmt.Errorf("failed to load agent config: %w", err)
	}

	// Create agent
	agent := tester.NewTesterAgent(config)

	// Prepare input
	input := agents.AgentInput{
		Task:        agentsTask,
		Targets:     agentsTargets,
		Context:     make(map[string]interface{}),
		Config:      make(map[string]interface{}),
		HITLEnabled: agentsHITLEnabled,
	}

	fmt.Printf("%s Validating: %s\n", styles.Info.Render("ℹ️"), agentsTask)
	fmt.Println()

	// Execute agent
	output, err := agent.Execute(context.Background(), input)
	if err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// Display result
	result, ok := output.Result.(*agents.TestResult)
	if !ok {
		return fmt.Errorf("invalid result type")
	}

	displayTestResult(result, styles)

	// Show HITL status
	fmt.Println()
	if output.Status == agents.StatusWaitingHITL {
		fmt.Println(styles.Warning.Render("⏸️  Quality Gates Failed - HITL Approval Required"))
		fmt.Printf("Decision ID: test-validation-%s\n", result.TaskDescription[:12])
		fmt.Println()
		fmt.Println("To approve:")
		fmt.Printf("  vcli maximus approve test-validation-%s --session-id <session>\n", result.TaskDescription[:12])
	} else {
		fmt.Println(styles.Success.Render("✅ Validation Complete"))
	}

	// Show metrics
	fmt.Printf("Duration: %v\n", output.Duration)
	fmt.Printf("Status: %s\n", output.Status)

	return nil
}

func displayTestResult(result *agents.TestResult, styles *visual.Styles) {
	// Header
	fmt.Println(styles.Bold.Render(fmt.Sprintf("Test Results: %s", result.TaskDescription)))
	fmt.Println()

	// Unit Tests
	if result.UnitTests.TotalTests > 0 {
		fmt.Println(styles.Bold.Render("🧪 Unit Tests"))
		fmt.Printf("  Total: %d\n", result.UnitTests.TotalTests)
		if result.UnitTests.PassedTests > 0 {
			fmt.Printf("  %s Passed: %d\n", styles.Success.Render("✅"), result.UnitTests.PassedTests)
		}
		if result.UnitTests.FailedTests > 0 {
			fmt.Printf("  %s Failed: %d\n", styles.Error.Render("❌"), result.UnitTests.FailedTests)
			// Show first few failures
			for i, failure := range result.UnitTests.Failures {
				if i < 3 {
					fmt.Printf("    • %s: %s\n", failure.TestName, failure.Message)
				}
			}
			if len(result.UnitTests.Failures) > 3 {
				fmt.Printf("    ... and %d more\n", len(result.UnitTests.Failures)-3)
			}
		}
		if result.UnitTests.SkippedTests > 0 {
			fmt.Printf("  ⏭️  Skipped: %d\n", result.UnitTests.SkippedTests)
		}
		fmt.Printf("  Duration: %v\n", result.UnitTests.Duration)
		fmt.Println()
	}

	// Integration Tests
	if result.IntegrationTests.TotalTests > 0 {
		fmt.Println(styles.Bold.Render("🔗 Integration Tests"))
		fmt.Printf("  Total: %d\n", result.IntegrationTests.TotalTests)
		fmt.Printf("  %s Passed: %d\n", styles.Success.Render("✅"), result.IntegrationTests.PassedTests)
		if result.IntegrationTests.FailedTests > 0 {
			fmt.Printf("  %s Failed: %d\n", styles.Error.Render("❌"), result.IntegrationTests.FailedTests)
		}
		fmt.Printf("  Duration: %v\n", result.IntegrationTests.Duration)
		fmt.Println()
	}

	// Coverage
	fmt.Println(styles.Bold.Render("📊 Coverage"))
	fmt.Printf("  Line Coverage: %.1f%%\n", result.Coverage.LineCoverage)
	fmt.Printf("  Branch Coverage: %.1f%%\n", result.Coverage.BranchCoverage)
	if len(result.Coverage.UncoveredFiles) > 0 {
		fmt.Printf("  Uncovered Files: %d\n", len(result.Coverage.UncoveredFiles))
	}
	fmt.Println()

	// Benchmarks
	if len(result.Benchmarks) > 0 {
		fmt.Println(styles.Bold.Render("⚡ Benchmarks"))
		for i, bench := range result.Benchmarks {
			if i < 5 {
				fmt.Printf("  %s: %s iterations, %s ns/op\n", bench.Name, bench.Iterations, bench.NsPerOp)
			}
		}
		if len(result.Benchmarks) > 5 {
			fmt.Printf("  ... and %d more benchmarks\n", len(result.Benchmarks)-5)
		}
		fmt.Println()
	}

	// Quality Gates
	fmt.Println(styles.Bold.Render("🚦 Quality Gates"))
	for _, gate := range result.QualityGates.Gates {
		icon := "✅"
		color := styles.Success
		if !gate.Passed {
			icon = "❌"
			color = styles.Error
		}
		fmt.Printf("  %s %s: %.1f/%.1f\n", color.Render(icon), gate.Name, gate.Actual, gate.Required)
		fmt.Printf("      %s\n", gate.Description)
	}
	if result.QualityGates.AllPassed {
		fmt.Printf("\n  %s All quality gates passed\n", styles.Success.Render("✅"))
	} else {
		fmt.Printf("\n  %s Some quality gates failed\n", styles.Error.Render("❌"))
	}
	fmt.Println()

	// Regressions
	if len(result.Regressions) > 0 {
		fmt.Println(styles.Bold.Render("⚠️  Regressions Detected"))
		for _, reg := range result.Regressions {
			impactColor := styles.Warning
			if reg.Impact == "high" || reg.Impact == "critical" {
				impactColor = styles.Error
			}
			fmt.Printf("  %s [%s] %s\n", impactColor.Render("▲"), strings.ToUpper(reg.Impact), reg.Description)
			if reg.Details != "" {
				fmt.Printf("      %s\n", reg.Details)
			}
		}
		fmt.Println()
	}

	// Recommendations
	if len(result.Recommendations) > 0 {
		fmt.Println(styles.Bold.Render("💡 Recommendations"))
		for _, rec := range result.Recommendations {
			fmt.Printf("  %s\n", rec)
		}
		fmt.Println()
	}

	// Summary
	fmt.Println(styles.Bold.Render("📝 Summary"))
	fmt.Printf("Test Validation Complete:\n")
	fmt.Printf("- Unit Tests: %d/%d passed\n", result.UnitTests.PassedTests, result.UnitTests.TotalTests)
	if result.IntegrationTests.TotalTests > 0 {
		fmt.Printf("- Integration Tests: %d/%d passed\n", result.IntegrationTests.PassedTests, result.IntegrationTests.TotalTests)
	}
	fmt.Printf("- Coverage: %.1f%%\n", result.Coverage.LineCoverage)
	fmt.Printf("- Quality Gates: %d/%d passed\n", countPassedGates(result.QualityGates), len(result.QualityGates.Gates))
	fmt.Printf("- Regressions: %d detected\n", len(result.Regressions))
}

func countPassedGates(qg agents.QualityGateResult) int {
	count := 0
	for _, gate := range qg.Gates {
		if gate.Passed {
			count++
		}
	}
	return count
}

// ============================================================================
// DIAGNOSTICADOR COMMANDS
// ============================================================================

// agentsDiagnosticadorCmd represents the diagnosticador agent commands
var agentsDiagnosticadorCmd = &cobra.Command{
	Use:   "diagnosticador",
	Short: "DIAGNOSTICADOR - Code analysis & security scanning",
	Long: `DIAGNOSTICADOR Agent: Comprehensive code analysis and security scanning.

Capabilities:
  • Static analysis (go vet)
  • Linting (golangci-lint)
  • Security scanning (gosec)
  • Test coverage analysis
  • Dependency vulnerability checking
  • Code quality metrics

Examples:
  # Analyze entire codebase
  vcli agents diagnosticador analyze --targets ./...

  # Analyze specific package
  vcli agents diagnosticador analyze --targets ./internal/maximus/

  # Run with security scan
  vcli agents diagnosticador analyze --targets ./... --enable-security`,
}

var agentsDiagnosticadorAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze code for issues and vulnerabilities",
	RunE:  runDiagnosticadorAnalyze,
}

func runDiagnosticadorAnalyze(cmd *cobra.Command, args []string) error {
	styles := visual.DefaultStyles()

	fmt.Println(styles.Bold.Render("🔍 DIAGNOSTICADOR - Code Analysis"))
	fmt.Println()

	// Load configuration
	config, err := loadAgentConfig()
	if err != nil {
		return fmt.Errorf("failed to load agent config: %w", err)
	}

	// Create agent
	agent := diagnosticador.NewDiagnosticadorAgent(config)

	// Prepare input
	input := agents.AgentInput{
		Task:    agentsTask,
		Targets: agentsTargets,
		Context: make(map[string]interface{}),
		Config:  make(map[string]interface{}),
	}

	// Validate
	if err := agent.Validate(input); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// Execute
	ctx := context.Background()
	fmt.Printf("%s Analyzing targets: %v\n", styles.Info.Render("ℹ️"), agentsTargets)
	fmt.Println()

	output, err := agent.Execute(ctx, input)
	if err != nil {
		return fmt.Errorf("analysis failed: %w", err)
	}

	// Display results
	if result, ok := output.Result.(*agents.DiagnosticResult); ok {
		displayDiagnosticResult(result, styles)
	}

	// Display summary
	fmt.Println()
	fmt.Println(styles.Success.Render("✅ Analysis Complete"))
	fmt.Printf("Duration: %v\n", output.Duration)
	fmt.Printf("Status: %s\n", output.Status)

	return nil
}

func displayDiagnosticResult(result *agents.DiagnosticResult, styles *visual.Styles) {
	// Code Quality
	fmt.Println(styles.Bold.Render("📊 Code Quality Metrics"))
	fmt.Printf("  Lines of Code: %d\n", result.CodeQuality.LinesOfCode)
	fmt.Printf("  Maintainability Index: %.1f/100\n", result.CodeQuality.MaintainabilityIndex)
	fmt.Println()

	// Test Coverage
	fmt.Println(styles.Bold.Render("🧪 Test Coverage"))
	fmt.Printf("  Line Coverage: %.1f%%\n", result.TestCoverage.LineCoverage)
	fmt.Printf("  Branch Coverage: %.1f%%\n", result.TestCoverage.BranchCoverage)
	fmt.Println()

	// Security Findings
	if len(result.SecurityFindings) > 0 {
		fmt.Println(styles.Bold.Render("🔒 Security Findings"))
		for i, finding := range result.SecurityFindings {
			severity := finding.Severity
			icon := "ℹ️"
			if severity == "critical" || severity == "high" {
				icon = "🚨"
			}
			fmt.Printf("  %s [%d] %s - %s\n", icon, i+1, strings.ToUpper(severity), finding.Description)
			if finding.FilePath != "" {
				fmt.Printf("      File: %s:%d\n", finding.FilePath, finding.LineNumber)
			}
		}
		fmt.Println()
	} else {
		fmt.Println(styles.Success.Render("✅ No security findings"))
		fmt.Println()
	}

	// Dependencies
	fmt.Println(styles.Bold.Render("📦 Dependencies"))
	fmt.Printf("  Total: %d\n", result.Dependencies.Total)
	if len(result.Dependencies.Outdated) > 0 {
		fmt.Printf("  Outdated: %d\n", len(result.Dependencies.Outdated))
	}
	if len(result.Dependencies.Vulnerable) > 0 {
		fmt.Printf("  Vulnerable: %d\n", len(result.Dependencies.Vulnerable))
	}
	fmt.Println()

	// Recommendations
	if len(result.Recommendations) > 0 {
		fmt.Println(styles.Bold.Render("💡 Recommendations"))
		for i, rec := range result.Recommendations {
			fmt.Printf("  %d. %s\n", i+1, rec)
		}
		fmt.Println()
	}

	// Summary
	fmt.Println(styles.Bold.Render("📝 Summary"))
	fmt.Println(result.Summary)
}

// agentsRunCmd runs a workflow
var agentsRunCmd = &cobra.Command{
	Use:   "run <workflow>",
	Short: "Run a multi-agent workflow",
	Long: `Run a pre-defined multi-agent workflow.

Available workflows:
  • full-cycle     - Complete development cycle (all agents)
  • bug-fix        - Rapid bug fix workflow
  • refactor       - Code refactoring workflow
  • security-audit - Security-focused analysis and fixes

Examples:
  # Run full development cycle
  vcli agents run full-cycle --task "Add Redis caching"

  # Run bug fix workflow
  vcli agents run bug-fix --task "Fix authentication issue"`,
	Args: cobra.ExactArgs(1),
	RunE: runAgentsWorkflow,
}

func runAgentsWorkflow(cmd *cobra.Command, args []string) error {
	workflowName := args[0]
	styles := visual.DefaultStyles()

	// Load workflow from YAML
	fmt.Printf("%s Loading workflow: %s\n", styles.Info.Render("📋"), workflowName)

	workflowDef, err := workflow.LoadWorkflow(workflowName)
	if err != nil {
		return fmt.Errorf("failed to load workflow: %w", err)
	}

	// Display workflow info
	fmt.Println()
	fmt.Printf("%s Workflow: %s\n", styles.Bold.Render("🚀"), workflowDef.Name)
	fmt.Printf("   Description: %s\n", workflowDef.Description)
	fmt.Printf("   Steps: %d\n", len(workflowDef.Steps))
	fmt.Println()

	// Display workflow steps
	fmt.Println(styles.Bold.Render("Workflow Steps:"))
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "  #\tAgent\tDescription\tHITL\n")
	fmt.Fprintf(w, "  -\t-----\t-----------\t----\n")
	for i, step := range workflowDef.Steps {
		hitlStatus := "No"
		if step.HITLRequired {
			hitlStatus = styles.Warning.Render("Yes")
		}
		fmt.Fprintf(w, "  %d\t%s\t%s\t%s\n", i+1, step.AgentType, step.Description, hitlStatus)
	}
	w.Flush()
	fmt.Println()

	// Load agent configuration
	config, err := loadAgentConfig()
	if err != nil {
		return fmt.Errorf("failed to load agent config: %w", err)
	}

	// Override task from CLI flag if provided
	if agentsTask != "" {
		// Inject task into first step
		if len(workflowDef.Steps) > 0 {
			workflowDef.Steps[0].Task = agentsTask
		}
	}

	// Override targets from CLI flag if provided
	if len(agentsTargets) > 0 {
		// Inject targets into all steps
		for i := range workflowDef.Steps {
			workflowDef.Steps[i].Targets = agentsTargets
		}
	}

	// Create orchestrator
	orchestrator, err := agents.NewAgentOrchestrator(config)
	if err != nil {
		return fmt.Errorf("failed to create orchestrator: %w", err)
	}

	// Register all agents
	fmt.Println(styles.Bold.Render("Registering agents..."))

	// Create agent instances
	diagAgent := diagnosticador.NewDiagnosticadorAgent(config)
	arquitetoAgent := arquiteto.NewArquitetoAgent(config)
	devAgent := dev_senior.NewDevSeniorAgent(config)
	testerAgent := tester.NewTesterAgent(config)

	// Register agents with orchestrator
	if err := orchestrator.RegisterAgent(diagAgent); err != nil {
		return fmt.Errorf("failed to register diagnosticador: %w", err)
	}
	if err := orchestrator.RegisterAgent(arquitetoAgent); err != nil {
		return fmt.Errorf("failed to register arquiteto: %w", err)
	}
	if err := orchestrator.RegisterAgent(devAgent); err != nil {
		return fmt.Errorf("failed to register dev_senior: %w", err)
	}
	if err := orchestrator.RegisterAgent(testerAgent); err != nil {
		return fmt.Errorf("failed to register tester: %w", err)
	}

	fmt.Printf("%s All agents registered successfully\n", styles.Success.Render("✓"))
	fmt.Println()

	// Execute workflow
	fmt.Println(styles.Bold.Render("Executing workflow..."))
	fmt.Println()

	ctx := context.Background()
	startTime := time.Now()

	execution, err := orchestrator.ExecuteWorkflow(ctx, *workflowDef)

	duration := time.Since(startTime)

	// Display results
	fmt.Println()
	fmt.Println(strings.Repeat("─", 80))
	fmt.Println()

	if err != nil {
		fmt.Printf("%s Workflow failed: %v\n", styles.Error.Render("❌"), err)
		fmt.Printf("   Duration: %s\n", duration.Round(time.Second))
		fmt.Printf("   Completed Steps: %d/%d\n", execution.CurrentStep-1, execution.TotalSteps)

		if len(execution.Errors) > 0 {
			fmt.Println()
			fmt.Println(styles.Bold.Render("Errors:"))
			for i, execErr := range execution.Errors {
				fmt.Printf("  %d. %v\n", i+1, execErr)
			}
		}

		return fmt.Errorf("workflow execution failed")
	}

	// Success
	fmt.Printf("%s Workflow completed successfully!\n", styles.Success.Render("✅"))
	fmt.Printf("   Duration: %s\n", duration.Round(time.Second))
	fmt.Printf("   Steps Completed: %d/%d\n", execution.CurrentStep, execution.TotalSteps)

	if len(execution.HITLDecisions) > 0 {
		fmt.Printf("   HITL Decisions: %d\n", len(execution.HITLDecisions))
		for i, decisionID := range execution.HITLDecisions {
			fmt.Printf("     %d. %s\n", i+1, decisionID)
		}
	}

	// Display agent outputs summary
	fmt.Println()
	fmt.Println(styles.Bold.Render("Agent Outputs:"))
	for agentType, output := range execution.AgentOutputs {
		fmt.Printf("  • %s: %s (%.2fs)\n",
			agentType,
			output.Status,
			output.Duration.Seconds())

		if len(output.Artifacts) > 0 {
			fmt.Printf("    Artifacts: %d files\n", len(output.Artifacts))
		}
	}

	fmt.Println()
	fmt.Printf("%s Workflow execution complete. Check artifacts in: %s\n",
		styles.Info.Render("ℹ️"),
		filepath.Join(config.WorkspacePath, "artifacts"))

	return nil
}

// loadAgentConfig loads agent configuration from YAML
func loadAgentConfig() (agents.AgentConfig, error) {
	configPath := filepath.Join(agentsWorkspacePath, "config", "agent_config.yaml")

	// Build RetryConfig from CLI flags (FASE 4.6)
	retryConfig := agents.RetryConfig{
		Enabled:            agentsEnableRetry,
		MaxRetries:         agentsMaxRetries,
		BackoffStrategy:    agentsBackoffStrategy,
		InitialBackoff:     1000000000, // 1 second in nanoseconds
		EnableReflection:   agentsEnableReflection,
		MaxReflectionDepth: 3,
	}

	// Set defaults if not specified
	if retryConfig.MaxRetries == 0 {
		retryConfig.MaxRetries = 3
	}
	if retryConfig.BackoffStrategy == "" {
		retryConfig.BackoffStrategy = "exponential"
	}

	// Check if config exists
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		// Return default config with environment variable fallback
		defaultConfig := agents.AgentConfig{
			WorkspacePath:         agentsWorkspacePath,
			MinCoveragePercent:    80.0,
			RequireSecurityScan:   true,
			RequireTestPass:       true,
			HITLOnFileDelete:      true,
			HITLOnSchemaChange:    true,
			HITLOnSecurityChange:  true,
			RetryConfig:           retryConfig, // FASE 4.6
		}

		// Environment variable fallback for Oraculo endpoint
		if envEndpoint := os.Getenv("MAXIMUS_ORACULO_ENDPOINT"); envEndpoint != "" {
			defaultConfig.MaximusOraculoEndpoint = envEndpoint
		}

		return defaultConfig, nil
	}

	// Load YAML config
	data, err := os.ReadFile(configPath)
	if err != nil {
		return agents.AgentConfig{}, err
	}

	var yamlConfig struct {
		MaximusEndpoints map[string]string `yaml:"maximus"`
		QualityGates     map[string]interface{} `yaml:"quality_gates"`
	}

	if err := yaml.Unmarshal(data, &yamlConfig); err != nil {
		return agents.AgentConfig{}, err
	}

	// Build config
	config := agents.AgentConfig{
		WorkspacePath:         agentsWorkspacePath,
		RequireSecurityScan:   true,
		RequireTestPass:       true,
		HITLOnFileDelete:      true,
		HITLOnSchemaChange:    true,
		HITLOnSecurityChange:  true,
		RetryConfig:           retryConfig, // FASE 4.6
	}

	// Parse endpoints
	if endpoint, ok := yamlConfig.MaximusEndpoints["eureka_endpoint"]; ok {
		config.MaximusEurekaEndpoint = endpoint
	}
	if endpoint, ok := yamlConfig.MaximusEndpoints["oraculo_endpoint"]; ok {
		config.MaximusOraculoEndpoint = endpoint
	}

	// Environment variable fallback for Oraculo endpoint
	if config.MaximusOraculoEndpoint == "" {
		if envEndpoint := os.Getenv("MAXIMUS_ORACULO_ENDPOINT"); envEndpoint != "" {
			config.MaximusOraculoEndpoint = envEndpoint
		}
	}

	// Parse quality gates
	if minCov, ok := yamlConfig.QualityGates["min_coverage_percent"].(float64); ok {
		config.MinCoveragePercent = minCov
	}

	return config, nil
}

// agentsStatusCmd shows agent status
var agentsStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show agent system status",
	RunE:  runAgentsStatus,
}

func runAgentsStatus(cmd *cobra.Command, args []string) error {
	styles := visual.DefaultStyles()

	fmt.Println(styles.Bold.Render("🤖 Agent Smith Status"))
	fmt.Println()

	// Check workspace
	if _, err := os.Stat(agentsWorkspacePath); os.IsNotExist(err) {
		fmt.Printf("%s Workspace not initialized\n", styles.Warning.Render("⚠️"))
		fmt.Printf("  Run: vcli agents init\n")
		return nil
	}

	fmt.Printf("%s Workspace: %s\n", styles.Success.Render("✅"), agentsWorkspacePath)

	// Check artifacts
	artifactsPath := filepath.Join(agentsWorkspacePath, "artifacts")
	if _, err := os.Stat(artifactsPath); err == nil {
		fmt.Printf("%s Artifacts directory: Ready\n", styles.Success.Render("✅"))
	}

	// Check workflows
	workflowsPath := filepath.Join(agentsWorkspacePath, "workflows")
	if _, err := os.Stat(workflowsPath); err == nil {
		fmt.Printf("%s Workflows directory: Ready\n", styles.Success.Render("✅"))
	}

	fmt.Println()
	fmt.Println("Agent Smith is ready for autonomous development!")

	return nil
}

func init() {
	rootCmd.AddCommand(agentsCmd)

	// Subcommands
	agentsCmd.AddCommand(agentsListCmd)
	agentsCmd.AddCommand(agentsDiagnosticadorCmd)
	agentsCmd.AddCommand(agentsArquitetoCmd)
	agentsCmd.AddCommand(agentsDevSeniorCmd)
	agentsCmd.AddCommand(agentsTesterCmd)
	agentsCmd.AddCommand(agentsRunCmd)
	agentsCmd.AddCommand(agentsStatusCmd)

	// DIAGNOSTICADOR subcommands
	agentsDiagnosticadorCmd.AddCommand(agentsDiagnosticadorAnalyzeCmd)

	// ARQUITETO subcommands
	agentsArquitetoCmd.AddCommand(agentsArquitetoPlanCmd)

	// DEV SENIOR subcommands
	agentsDevSeniorCmd.AddCommand(agentsDevSeniorImplementCmd)

	// TESTER subcommands
	agentsTesterCmd.AddCommand(agentsTesterValidateCmd)

	// Global flags
	agentsCmd.PersistentFlags().StringVar(&agentsWorkspacePath, "workspace", ".agents-workspace", "Agent workspace path")
	agentsCmd.PersistentFlags().StringVarP(&agentsOutputFormat, "output", "o", "text", "Output format (text|json)")

	// DIAGNOSTICADOR flags
	agentsDiagnosticadorAnalyzeCmd.Flags().StringVar(&agentsTask, "task", "Analyze codebase", "Task description")
	agentsDiagnosticadorAnalyzeCmd.Flags().StringSliceVar(&agentsTargets, "targets", []string{"./..."}, "Target paths to analyze")

	// ARQUITETO flags
	agentsArquitetoPlanCmd.Flags().StringVar(&agentsTask, "task", "", "Task description (required)")
	agentsArquitetoPlanCmd.Flags().BoolVar(&agentsHITLEnabled, "hitl", true, "Enable HITL (Human-in-the-Loop) approvals")
	agentsArquitetoPlanCmd.Flags().StringVar(&agentsContextFile, "context", "", "Path to diagnostic context JSON file")

	// DEV SENIOR flags
	agentsDevSeniorImplementCmd.Flags().StringVar(&agentsTask, "task", "", "Task description (required)")
	agentsDevSeniorImplementCmd.Flags().BoolVar(&agentsHITLEnabled, "hitl", true, "Enable HITL (Human-in-the-Loop) approvals")
	agentsDevSeniorImplementCmd.Flags().StringSliceVar(&agentsTargets, "targets", []string{"./..."}, "Target paths for tests")
	agentsDevSeniorImplementCmd.Flags().StringVar(&agentsContextFile, "context", "", "Path to architecture plan JSON file")

	// FASE 4.6: Anthropic Patterns flags for DEV SENIOR
	agentsDevSeniorImplementCmd.Flags().BoolVar(&agentsEnableRetry, "enable-retry", false, "Enable self-healing retry mechanism")
	agentsDevSeniorImplementCmd.Flags().IntVar(&agentsMaxRetries, "max-retries", 3, "Maximum retry attempts (default: 3)")
	agentsDevSeniorImplementCmd.Flags().StringVar(&agentsBackoffStrategy, "backoff", "exponential", "Backoff strategy: none, linear, exponential")
	agentsDevSeniorImplementCmd.Flags().BoolVar(&agentsEnableReflection, "enable-reflection", true, "Enable LLM reflection on errors")
	agentsDevSeniorImplementCmd.Flags().BoolVar(&agentsSkipPlanning, "skip-planning", false, "Skip planning phase (fast mode)")

	// TESTER flags
	agentsTesterValidateCmd.Flags().StringVar(&agentsTask, "task", "Validate code quality and tests", "Task description")
	agentsTesterValidateCmd.Flags().BoolVar(&agentsHITLEnabled, "hitl", true, "Enable HITL approval for quality gate failures")
	agentsTesterValidateCmd.Flags().StringSliceVar(&agentsTargets, "targets", []string{"./..."}, "Target paths to test")

	// Workflow flags
	agentsRunCmd.Flags().StringVar(&agentsTask, "task", "", "Task description (required)")
	agentsRunCmd.Flags().BoolVar(&agentsHITLEnabled, "hitl", true, "Enable HITL (Human-in-the-Loop) approvals")
}
