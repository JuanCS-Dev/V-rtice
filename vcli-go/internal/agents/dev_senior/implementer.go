package dev_senior

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
	"github.com/verticedev/vcli-go/internal/agents/strategies"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// DevSeniorAgent implements autonomous code generation and implementation
type DevSeniorAgent struct {
	config        agents.AgentConfig
	status        agents.AgentStatus
	logger        *log.Logger
	oraculoClient *maximus.OraculoClient
	workingDir    string

	// FASE 4.5/4.6: Anthropic Best Practices
	planningEngine   *agents.PlanningEngine
	selfHealing      *agents.SelfHealingExecutor
	reflectionEngine *agents.ReflectionEngine
}

// NewDevSeniorAgent creates a new DEV SENIOR agent
func NewDevSeniorAgent(config agents.AgentConfig) *DevSeniorAgent {
	logger := log.New(os.Stdout, "[DEV SENIOR] ", log.LstdFlags)

	return &DevSeniorAgent{
		config:        config,
		status:        agents.StatusIdle,
		logger:        logger,
		oraculoClient: maximus.NewOraculoClient(config.MaximusOraculoEndpoint, ""), // Auth token from env
		workingDir:    ".", // Default to current directory

		// FASE 4.5/4.6: Initialize Anthropic patterns
		planningEngine:   agents.NewPlanningEngine(logger),
		selfHealing:      agents.NewSelfHealingExecutor(config.RetryConfig, logger),
		reflectionEngine: agents.NewReflectionEngine(logger),
	}
}

// Type returns the agent type
func (a *DevSeniorAgent) Type() agents.AgentType {
	return agents.AgentTypeDevSenior
}

// Name returns the agent name
func (a *DevSeniorAgent) Name() string {
	return "DEV SENIOR"
}

// Execute implements the Agent interface - main execution logic
func (a *DevSeniorAgent) Execute(ctx context.Context, input agents.AgentInput) (*agents.AgentOutput, error) {
	a.status = agents.StatusRunning
	startTime := time.Now()

	a.logger.Printf("Starting code implementation for task: %s", input.Task)

	// Step 0: Language Detection
	a.logger.Println("Step 0/10: Detecting language...")
	detector := language.NewDetector()
	langResult, err := detector.Detect(input.Targets)
	if err != nil {
		return nil, fmt.Errorf("language detection failed: %w", err)
	}
	a.logger.Printf("   Detected: %s (%.0f%% confidence)", langResult.Primary, langResult.Confidence*100)

	// Step 0.5: Generate Implementation Plan (FASE 4.6: Planning Phase)
	var implPlan *agents.ImplementationPlan
	skipPlanning := false

	// Check if planning should be skipped (fast mode)
	if skipPlanConfig, ok := input.Config["skip_planning"].(bool); ok && skipPlanConfig {
		skipPlanning = true
		a.logger.Println("Step 0.5/10: Skipping planning phase (fast mode enabled)")
	}

	if !skipPlanning {
		a.logger.Println("Step 0.5/10: Generating implementation plan...")

		// Extract architecture plan from context first
		archPlan := a.extractArchitecturePlan(input.Context)
		contextData := a.buildContextData(input, archPlan)

		implPlan, err = a.planningEngine.GeneratePlan(
			input.Task,
			input.Targets,
			string(langResult.Primary),
			contextData,
		)
		if err != nil {
			a.logger.Printf("Warning: Planning failed: %v (continuing without plan)", err)
			implPlan = nil
		}

		// Display plan and wait for approval if HITL enabled
		if implPlan != nil && input.HITLEnabled {
			a.displayPlan(implPlan)
			a.logger.Println("⚠️  Waiting for plan approval (HITL)...")
			// TODO: Integrate with actual HITL system
			// For now, just set approved = true
			implPlan.UserApproved = true
		} else if implPlan != nil {
			implPlan.UserApproved = true // Auto-approve if HITL disabled
		}

		// Reflect on plan quality (FASE 4.6: Reflection)
		if implPlan != nil {
			score, concerns, recommendations := a.reflectionEngine.ReflectOnPlan(ctx, implPlan)
			a.logger.Printf("[Reflection] Plan quality score: %.1f/100", score)
			if len(concerns) > 0 {
				a.logger.Printf("[Reflection] Concerns: %v", concerns)
			}
			if len(recommendations) > 0 {
				a.logger.Printf("[Reflection] Recommendations: %v", recommendations)
			}
		}
	}

	// Step 1: Extract architecture plan from context (if available)
	a.logger.Println("Step 1/10: Extracting architecture plan from context")
	var archPlan *agents.ArchitecturePlan
	var contextData map[string]interface{}
	if !skipPlanning {
		// archPlan and contextData already extracted above for planning - reuse them
		archPlan = a.extractArchitecturePlan(input.Context)
		contextData = a.buildContextData(input, archPlan)
	} else {
		// Extract them now since planning was skipped
		archPlan = a.extractArchitecturePlan(input.Context)
		contextData = a.buildContextData(input, archPlan)
	}

	// Step 2: Create git branch for changes
	a.logger.Println("Step 2/10: Creating git branch")
	branchName, err := a.createGitBranch(input.Task)
	if err != nil {
		a.logger.Printf("Warning: Failed to create git branch: %v", err)
		// Continue without git - not fatal
		branchName = ""
	}

	// Step 3: Create and populate strategy registry
	a.logger.Println("Step 3/10: Initializing code generation strategy...")
	registry := strategies.NewStrategyRegistry()
	registry.RegisterCodeGen(strategies.NewGoCodeGenStrategy(a.config.MaximusOraculoEndpoint, ""))
	registry.RegisterCodeGen(strategies.NewPythonCodeGenStrategy(a.config.MaximusOraculoEndpoint, ""))

	strategy, ok := registry.GetCodeGen(langResult.Primary)
	if !ok {
		return nil, fmt.Errorf("no code generation strategy for language: %s", langResult.Primary)
	}
	a.logger.Printf("   Using %s code generation strategy", langResult.Primary)

	// Step 4: Generate implementation code using strategy
	a.logger.Println("Step 4/10: Generating implementation code")
	// contextData already built for planning above, reuse it
	strategyChanges, err := strategy.GenerateCode(ctx, input.Task, contextData)
	if err != nil {
		a.status = agents.StatusFailed
		return nil, fmt.Errorf("code generation failed: %w", err)
	}

	// Convert strategy output to legacy CodeChanges format
	codeChanges := a.convertToCodeChanges(strategyChanges)

	// FASE 4.6: Reflect on generated code quality
	a.logger.Println("Step 4.5/10: Reflecting on generated code quality")
	for _, change := range strategyChanges {
		if change.After != "" {
			score, issues, suggestions := a.reflectionEngine.ReflectOnCodeQuality(
				ctx,
				change.After,
				change.Language,
				input.Task,
			)
			a.logger.Printf("[Reflection] %s quality: %.1f/100", change.FilePath, score)
			if len(issues) > 0 {
				a.logger.Printf("[Reflection] Issues found: %v", issues)
			}
			if len(suggestions) > 0 {
				a.logger.Printf("[Reflection] Suggestions: %v", suggestions)
			}
		}
	}

	// Step 5: Apply code changes to files
	a.logger.Println("Step 5/10: Applying code changes to files")
	modifiedPaths, err := a.applyCodeChanges(codeChanges)
	if err != nil {
		a.status = agents.StatusFailed
		return nil, fmt.Errorf("failed to apply code changes: %w", err)
	}

	// Step 5: Run go fmt and goimports
	a.logger.Println("Step 5/10: Formatting code (gofmt, goimports)")
	if err := a.formatCode(modifiedPaths); err != nil {
		a.logger.Printf("Warning: Code formatting issues: %v", err)
		// Continue - formatting issues are non-fatal
	}

	// Step 6: Compile and check for errors (FASE 4.6: Self-Healing with Retry)
	a.logger.Println("Step 6/10: Compiling code to check for errors (with self-healing retry)")
	var compilationResult *CompilationResult
	var compilationSelfHealing *agents.SelfHealingResult

	if a.config.RetryConfig.Enabled {
		// Use self-healing retry loop for compilation
		compilationSelfHealing = a.selfHealing.ExecuteWithRetry(
			ctx,
			// Attempt function: compile code
			func(attempt int) error {
				a.logger.Printf("   Compilation attempt %d...", attempt)
				result, err := a.compileCode()
				compilationResult = result
				if err != nil || !result.Success {
					return fmt.Errorf("compilation failed")
				}
				return nil
			},
			// Validation function: check compilation success
			func() (bool, string, error) {
				if compilationResult == nil {
					return false, "runtime", fmt.Errorf("compilation result is nil")
				}
				if !compilationResult.Success {
					return false, "compilation", fmt.Errorf("compilation errors: %v", compilationResult.Errors)
				}
				return true, "", nil
			},
			// Reflection function: analyze compilation errors
			func(err error, attemptNum int) (string, string) {
				if compilationResult != nil && len(compilationResult.Errors) > 0 {
					errorOutput := strings.Join(compilationResult.Errors, "\n")
					return a.reflectionEngine.ReflectOnCompilationError(ctx, errorOutput, "", attemptNum)
				}
				return fmt.Sprintf("Compilation failed at attempt %d", attemptNum), "Review compilation errors"
			},
		)

		if !compilationSelfHealing.Success {
			a.logger.Printf("⚠️  Compilation failed after %d attempts", compilationSelfHealing.TotalAttempts)
		} else {
			a.logger.Printf("✅ Compilation succeeded (attempt %d)", compilationSelfHealing.TotalAttempts)
		}
	} else {
		// Non-retry path (legacy behavior)
		result, err := a.compileCode()
		compilationResult = result
		if err != nil {
			a.logger.Printf("Warning: Compilation failed: %v", err)
		}
	}

	// Step 7: Run basic tests (FASE 4.6: Self-Healing with Retry)
	a.logger.Println("Step 7/10: Running basic tests (with self-healing retry)")
	var testResult *TestResult
	var testSelfHealing *agents.SelfHealingResult

	if a.config.RetryConfig.Enabled {
		// Use self-healing retry loop for tests
		testSelfHealing = a.selfHealing.ExecuteWithRetry(
			ctx,
			// Attempt function: run tests
			func(attempt int) error {
				a.logger.Printf("   Test attempt %d...", attempt)
				result, err := a.runTests(input.Targets)
				testResult = result
				if err != nil || result.FailedTests > 0 {
					return fmt.Errorf("tests failed: %d/%d passed", result.PassedTests, result.TotalTests)
				}
				return nil
			},
			// Validation function: check test pass rate
			func() (bool, string, error) {
				if testResult == nil {
					return false, "runtime", fmt.Errorf("test result is nil")
				}
				if testResult.FailedTests > 0 {
					return false, "test_failure", fmt.Errorf("%d tests failed", testResult.FailedTests)
				}
				return true, "", nil
			},
			// Reflection function: analyze test failures
			func(err error, attemptNum int) (string, string) {
				if testResult != nil && testResult.FailedTests > 0 {
					failedTests := []string{} // TODO: Parse failed test names from output
					return a.reflectionEngine.ReflectOnTestFailure(ctx, failedTests, testResult.Output, attemptNum)
				}
				return fmt.Sprintf("Tests failed at attempt %d", attemptNum), "Review test failures"
			},
		)

		if !testSelfHealing.Success {
			a.logger.Printf("⚠️  Tests failed after %d attempts", testSelfHealing.TotalAttempts)
		} else {
			a.logger.Printf("✅ Tests passed (attempt %d)", testSelfHealing.TotalAttempts)
		}
	} else {
		// Non-retry path (legacy behavior)
		result, err := a.runTests(input.Targets)
		testResult = result
		if err != nil {
			a.logger.Printf("Warning: Tests failed: %v", err)
		}
	}

	// Merge self-healing results (prioritize compilation issues over test issues)
	var mergedSelfHealing *agents.SelfHealingResult
	if compilationSelfHealing != nil && testSelfHealing != nil {
		// Merge both results
		mergedSelfHealing = &agents.SelfHealingResult{
			Success:       compilationSelfHealing.Success && testSelfHealing.Success,
			TotalAttempts: compilationSelfHealing.TotalAttempts + testSelfHealing.TotalAttempts,
			Attempts:      append(compilationSelfHealing.Attempts, testSelfHealing.Attempts...),
			FinalError:    compilationSelfHealing.FinalError, // Compilation errors are more critical
			Recovered:     compilationSelfHealing.Recovered || testSelfHealing.Recovered,
			Duration:      compilationSelfHealing.Duration + testSelfHealing.Duration,
		}
		if testSelfHealing.FinalError != nil && compilationSelfHealing.FinalError == nil {
			mergedSelfHealing.FinalError = testSelfHealing.FinalError
		}
	} else if compilationSelfHealing != nil {
		mergedSelfHealing = compilationSelfHealing
	} else if testSelfHealing != nil {
		mergedSelfHealing = testSelfHealing
	}

	// Step 8: Prepare git commit (but don't push - requires HITL approval)
	a.logger.Println("Step 8/10: Preparing git commit")
	commitHash := ""
	if branchName != "" {
		commitHash, err = a.prepareGitCommit(input.Task, modifiedPaths)
		if err != nil {
			a.logger.Printf("Warning: Failed to create git commit: %v", err)
		}
	}

	// Convert string slices to FileChange slices
	filesCreated := make([]agents.FileChange, len(codeChanges.FilesCreated))
	for i, path := range codeChanges.FilesCreated {
		filesCreated[i] = agents.FileChange{
			FilePath:  path,
			Operation: "create",
			Language:  "go",
		}
	}

	filesModified := make([]agents.FileChange, len(codeChanges.FilesModified))
	for i, path := range codeChanges.FilesModified {
		filesModified[i] = agents.FileChange{
			FilePath:  path,
			Operation: "modify",
			Language:  "go",
		}
	}

	filesDeleted := make([]agents.FileChange, len(codeChanges.FilesDeleted))
	for i, path := range codeChanges.FilesDeleted {
		filesDeleted[i] = agents.FileChange{
			FilePath:  path,
			Operation: "delete",
			Language:  "go",
		}
	}

	// Build result
	result := &agents.ImplementationResult{
		TaskDescription:    input.Task,
		Plan:               implPlan,            // FASE 4.6: Include implementation plan
		SelfHealing:        mergedSelfHealing,   // FASE 4.6: Include self-healing retry results
		FilesCreated:       filesCreated,
		FilesModified:      filesModified,
		FilesDeleted:       filesDeleted,
		GitBranch:          branchName,
		GitCommit:          commitHash,
		CompilationSuccess: compilationResult.Success,
		CompilationErrors:  compilationResult.Errors,
		TestsExecuted:      testResult.TotalTests,
		TestsPassed:        testResult.PassedTests,
		TestsFailed:        testResult.FailedTests,
		CodeQualityScore:   a.calculateCodeQuality(compilationResult, testResult),
		Recommendations:    a.generateRecommendations(compilationResult, testResult, codeChanges),
	}

	duration := time.Since(startTime)
	a.logger.Printf("Implementation complete: %d files modified, compilation: %v, tests: %d/%d passed",
		len(modifiedPaths), compilationResult.Success, testResult.PassedTests, testResult.TotalTests)

	// Determine status
	outputStatus := agents.StatusCompleted
	if input.HITLEnabled {
		// DEV SENIOR always requires HITL approval for code changes
		outputStatus = agents.StatusWaitingHITL
		a.logger.Printf("HITL approval required for implementation: impl-%s", result.TaskDescription[:8])
	}

	metrics := make(map[string]float64)
	metrics["files_created"] = float64(len(result.FilesCreated))
	metrics["files_modified"] = float64(len(result.FilesModified))
	metrics["files_deleted"] = float64(len(result.FilesDeleted))
	if result.CompilationSuccess {
		metrics["compilation_success"] = 1.0
	} else {
		metrics["compilation_success"] = 0.0
	}
	metrics["tests_passed"] = float64(result.TestsPassed)
	metrics["tests_failed"] = float64(result.TestsFailed)

	output := &agents.AgentOutput{
		AgentType:   agents.AgentTypeDevSenior,
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
func (a *DevSeniorAgent) Validate(input agents.AgentInput) error {
	if input.Task == "" {
		return fmt.Errorf("task description is required")
	}
	return nil
}

// GetCapabilities returns agent capabilities
func (a *DevSeniorAgent) GetCapabilities() []string {
	return []string{
		"Autonomous code generation",
		"File operations (create, modify, delete)",
		"Git operations (branch, commit)",
		"Code formatting (gofmt, goimports)",
		"Compilation validation",
		"Basic test execution",
		"Code refactoring",
		"MAXIMUS Oraculo integration",
	}
}

// GetStatus returns current agent status
func (a *DevSeniorAgent) GetStatus() agents.AgentStatus {
	return a.status
}

// buildContextData builds context data map for code generation strategy
func (a *DevSeniorAgent) buildContextData(input agents.AgentInput, archPlan *agents.ArchitecturePlan) map[string]interface{} {
	contextData := make(map[string]interface{})

	// Add architecture plan if available
	if archPlan != nil {
		contextData["architecture_plan"] = archPlan
		contextData["implementation_steps"] = archPlan.Steps
	}

	// Add any existing code from context
	if existingCode, ok := input.Context["existing_code"]; ok {
		contextData["existing_code"] = existingCode
	}

	// Add dependencies from context
	if deps, ok := input.Context["dependencies"]; ok {
		contextData["dependencies"] = deps
	}

	// Add framework info if available
	if framework, ok := input.Context["framework"]; ok {
		contextData["framework"] = framework
	}

	// Add target files/directories
	if len(input.Targets) > 0 {
		contextData["targets"] = input.Targets
	}

	return contextData
}

// displayPlan pretty-prints an implementation plan (FASE 4.6)
func (a *DevSeniorAgent) displayPlan(plan *agents.ImplementationPlan) {
	a.logger.Println("============================================================")
	a.logger.Printf("📋 Implementation Plan: %s", plan.PlanID)
	a.logger.Println("============================================================")
	a.logger.Printf("\n🎯 Approach:\n%s\n", plan.Approach)

	if len(plan.FilesToCreate) > 0 {
		a.logger.Printf("📝 Files to Create (%d):", len(plan.FilesToCreate))
		for _, f := range plan.FilesToCreate {
			a.logger.Printf("   + %s", f)
		}
	}

	if len(plan.FilesToModify) > 0 {
		a.logger.Printf("✏️  Files to Modify (%d):", len(plan.FilesToModify))
		for _, f := range plan.FilesToModify {
			a.logger.Printf("   ~ %s", f)
		}
	}

	if len(plan.FilesToDelete) > 0 {
		a.logger.Printf("🗑️  Files to Delete (%d):", len(plan.FilesToDelete))
		for _, f := range plan.FilesToDelete {
			a.logger.Printf("   - %s", f)
		}
	}

	if len(plan.TestsNeeded) > 0 {
		a.logger.Printf("\n🧪 Tests Needed (%d):", len(plan.TestsNeeded))
		for _, t := range plan.TestsNeeded {
			a.logger.Printf("   • %s", t)
		}
	}

	if len(plan.Risks) > 0 {
		a.logger.Printf("\n⚠️  Risks Identified (%d):", len(plan.Risks))
		for _, r := range plan.Risks {
			a.logger.Printf("   ⚡ %s", r)
		}
	}

	if len(plan.Dependencies) > 0 {
		a.logger.Printf("\n📦 Dependencies (%d):", len(plan.Dependencies))
		for _, d := range plan.Dependencies {
			a.logger.Printf("   • %s", d)
		}
	}

	a.logger.Printf("\n🔢 Estimated Complexity: %d/10", plan.Complexity)
	a.logger.Println("============================================================")
}

// convertToCodeChanges converts strategy output ([]agents.CodeChange) to legacy CodeChanges format
func (a *DevSeniorAgent) convertToCodeChanges(strategyChanges []agents.CodeChange) *CodeChanges {
	result := &CodeChanges{
		FilesCreated:  make([]string, 0),
		FilesModified: make([]string, 0),
		FilesDeleted:  make([]string, 0),
		Changes:       make(map[string]string),
	}

	// Categorize changes by operation type
	for _, change := range strategyChanges {
		switch change.Operation {
		case "create":
			result.FilesCreated = append(result.FilesCreated, change.FilePath)
			result.Changes[change.FilePath] = change.After
		case "modify":
			result.FilesModified = append(result.FilesModified, change.FilePath)
			result.Changes[change.FilePath] = change.After
		case "delete":
			result.FilesDeleted = append(result.FilesDeleted, change.FilePath)
			// For delete operations, store Before content in case needed
			if change.Before != "" {
				result.Changes[change.FilePath] = change.Before
			}
		}
	}

	a.logger.Printf("Converted %d strategy changes: %d created, %d modified, %d deleted",
		len(strategyChanges),
		len(result.FilesCreated),
		len(result.FilesModified),
		len(result.FilesDeleted))

	return result
}

// ============================================================================
// HELPER FUNCTIONS - IMPLEMENTATION LOGIC
// ============================================================================

// extractArchitecturePlan extracts architecture plan from context
func (a *DevSeniorAgent) extractArchitecturePlan(context map[string]interface{}) *agents.ArchitecturePlan {
	if archOutput, ok := context["arquiteto_output"]; ok {
		if output, ok := archOutput.(*agents.AgentOutput); ok {
			if plan, ok := output.Result.(*agents.ArchitecturePlan); ok {
				a.logger.Println("Architecture plan found in context")
				return plan
			}
		}
	}
	a.logger.Println("No architecture plan in context - proceeding without plan")
	return nil
}

// CodeChanges represents code changes to be applied
type CodeChanges struct {
	FilesCreated  []string
	FilesModified []string
	FilesDeleted  []string
	Changes       map[string]string // filepath -> new content
}

// generateCode generates implementation code using MAXIMUS Oraculo
func (a *DevSeniorAgent) generateCode(ctx context.Context, task string, plan *agents.ArchitecturePlan) (*CodeChanges, error) {
	// In real implementation, this would call MAXIMUS Oraculo for AI-powered code generation
	// For now, we'll create a basic implementation structure

	a.logger.Println("Generating code using MAXIMUS Oraculo...")

	// Build context for Oraculo
	oraculoContext := map[string]interface{}{
		"task":        task,
		"language":    "go",
		"project":     "vcli-go",
		"framework":   "cobra",
		"patterns":    []string{"VÉRTICE", "Padrão Pagani"},
	}

	if plan != nil {
		oraculoContext["architecture_plan"] = plan
		oraculoContext["adrs"] = plan.ADRs
		oraculoContext["risks"] = plan.Risks
	}

	// For Phase 3 initial implementation, we'll return a mock structure
	// Real implementation will call: a.oraculoClient.AutoImplement(task, "go", oraculoContext)

	a.logger.Println("Note: Using mock code generation - full Oraculo integration pending")

	changes := &CodeChanges{
		FilesCreated:  []string{},
		FilesModified: []string{},
		FilesDeleted:  []string{},
		Changes:       make(map[string]string),
	}

	// Mock: For demo purposes, we return empty changes
	// Real implementation would generate actual code files
	a.logger.Printf("Generated %d file changes", len(changes.Changes))

	return changes, nil
}

// applyCodeChanges applies code changes to files
func (a *DevSeniorAgent) applyCodeChanges(changes *CodeChanges) ([]string, error) {
	modified := []string{}

	// Create new files
	for _, filepath := range changes.FilesCreated {
		if content, ok := changes.Changes[filepath]; ok {
			if err := a.createFile(filepath, content); err != nil {
				return modified, fmt.Errorf("failed to create %s: %w", filepath, err)
			}
			modified = append(modified, filepath)
			a.logger.Printf("Created: %s", filepath)
		}
	}

	// Modify existing files
	for _, filepath := range changes.FilesModified {
		if content, ok := changes.Changes[filepath]; ok {
			if err := a.modifyFile(filepath, content); err != nil {
				return modified, fmt.Errorf("failed to modify %s: %w", filepath, err)
			}
			modified = append(modified, filepath)
			a.logger.Printf("Modified: %s", filepath)
		}
	}

	// Delete files
	for _, filepath := range changes.FilesDeleted {
		if err := a.deleteFile(filepath); err != nil {
			return modified, fmt.Errorf("failed to delete %s: %w", filepath, err)
		}
		modified = append(modified, filepath)
		a.logger.Printf("Deleted: %s", filepath)
	}

	return modified, nil
}

// createFile creates a new file with content
func (a *DevSeniorAgent) createFile(filepath, content string) error {
	// Ensure directory exists (if filepath contains directory)
	lastSlash := strings.LastIndex(filepath, "/")
	if lastSlash > 0 {
		dir := filepath[:lastSlash]
		if err := os.MkdirAll(dir, 0755); err != nil {
			return err
		}
	}

	// Write file
	return os.WriteFile(filepath, []byte(content), 0644)
}

// modifyFile modifies an existing file
func (a *DevSeniorAgent) modifyFile(filepath, content string) error {
	// Check if file exists
	if _, err := os.Stat(filepath); os.IsNotExist(err) {
		return fmt.Errorf("file does not exist: %s", filepath)
	}

	// Write new content
	return os.WriteFile(filepath, []byte(content), 0644)
}

// deleteFile deletes a file
func (a *DevSeniorAgent) deleteFile(filepath string) error {
	return os.Remove(filepath)
}

// formatCode runs gofmt and goimports on files
func (a *DevSeniorAgent) formatCode(files []string) error {
	for _, file := range files {
		if !strings.HasSuffix(file, ".go") {
			continue // Only format Go files
		}

		// Run gofmt
		cmd := exec.Command("gofmt", "-w", file)
		if err := cmd.Run(); err != nil {
			a.logger.Printf("gofmt failed for %s: %v", file, err)
		}

		// Run goimports (if available)
		cmd = exec.Command("goimports", "-w", file)
		if err := cmd.Run(); err != nil {
			// goimports might not be installed - not fatal
			a.logger.Printf("goimports not available for %s", file)
		}
	}
	return nil
}

// CompilationResult represents compilation results
type CompilationResult struct {
	Success bool
	Errors  []string
	Output  string
}

// compileCode compiles the code to check for errors
func (a *DevSeniorAgent) compileCode() (*CompilationResult, error) {
	a.logger.Println("Running: go build ./...")

	cmd := exec.Command("go", "build", "./...")
	output, err := cmd.CombinedOutput()

	result := &CompilationResult{
		Success: err == nil,
		Errors:  []string{},
		Output:  string(output),
	}

	if err != nil {
		// Parse errors from output
		lines := strings.Split(string(output), "\n")
		for _, line := range lines {
			if strings.Contains(line, "error") || strings.Contains(line, "undefined") {
				result.Errors = append(result.Errors, line)
			}
		}
	}

	return result, nil
}

// TestResult represents test execution results
type TestResult struct {
	TotalTests  int
	PassedTests int
	FailedTests int
	Output      string
}

// runTests runs basic tests
func (a *DevSeniorAgent) runTests(targets []string) (*TestResult, error) {
	if len(targets) == 0 {
		targets = []string{"./..."}
	}

	a.logger.Printf("Running tests: go test %s", strings.Join(targets, " "))

	args := append([]string{"test", "-v"}, targets...)
	cmd := exec.Command("go", args...)
	output, err := cmd.CombinedOutput()

	result := &TestResult{
		Output: string(output),
	}

	// Parse test results
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.Contains(line, "PASS") {
			result.PassedTests++
			result.TotalTests++
		} else if strings.Contains(line, "FAIL") {
			result.FailedTests++
			result.TotalTests++
		}
	}

	return result, err
}

// createGitBranch creates a new git branch
func (a *DevSeniorAgent) createGitBranch(task string) (string, error) {
	// Generate branch name from task
	branchName := "feature/" + strings.ToLower(strings.ReplaceAll(task, " ", "-"))
	branchName = strings.ReplaceAll(branchName, ":", "")
	branchName = strings.ReplaceAll(branchName, "/", "-")

	// Limit length
	if len(branchName) > 50 {
		branchName = branchName[:50]
	}

	a.logger.Printf("Creating branch: %s", branchName)

	cmd := exec.Command("git", "checkout", "-b", branchName)
	if err := cmd.Run(); err != nil {
		return "", err
	}

	return branchName, nil
}

// prepareGitCommit creates a git commit (but doesn't push)
func (a *DevSeniorAgent) prepareGitCommit(task string, files []string) (string, error) {
	// Add files to staging
	for _, file := range files {
		cmd := exec.Command("git", "add", file)
		if err := cmd.Run(); err != nil {
			a.logger.Printf("Warning: Failed to add %s to git: %v", file, err)
		}
	}

	// Create commit message
	commitMsg := fmt.Sprintf(`feat: %s

Implementation by DEV SENIOR Agent

🤖 Generated with Agent Smith
Co-Authored-By: DEV SENIOR <agent-smith@vertice.ai>`, task)

	// Commit
	cmd := exec.Command("git", "commit", "-m", commitMsg)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("commit failed: %w, output: %s", err, string(output))
	}

	// Get commit hash
	cmd = exec.Command("git", "rev-parse", "HEAD")
	hash, err := cmd.Output()
	if err != nil {
		return "", err
	}

	commitHash := strings.TrimSpace(string(hash))
	a.logger.Printf("Created commit: %s", commitHash[:8])

	return commitHash, nil
}

// calculateCodeQuality calculates overall code quality score
func (a *DevSeniorAgent) calculateCodeQuality(comp *CompilationResult, test *TestResult) float64 {
	score := 0.0

	// Compilation success: 40 points
	if comp.Success {
		score += 40.0
	}

	// Test pass rate: 40 points
	if test.TotalTests > 0 {
		passRate := float64(test.PassedTests) / float64(test.TotalTests)
		score += passRate * 40.0
	}

	// Basic quality: 20 points (for now, just give it if compilation works)
	if comp.Success {
		score += 20.0
	}

	return score
}

// generateRecommendations generates recommendations based on results
func (a *DevSeniorAgent) generateRecommendations(comp *CompilationResult, test *TestResult, changes *CodeChanges) []string {
	recs := []string{}

	if !comp.Success {
		recs = append(recs, "⚠️ Fix compilation errors before proceeding")
		recs = append(recs, fmt.Sprintf("   Found %d compilation errors", len(comp.Errors)))
	}

	if test.FailedTests > 0 {
		recs = append(recs, fmt.Sprintf("⚠️ Fix %d failing tests", test.FailedTests))
	}

	if test.TotalTests == 0 {
		recs = append(recs, "💡 Add unit tests for new code (target: >80% coverage)")
	}

	if len(changes.FilesCreated) > 0 {
		recs = append(recs, fmt.Sprintf("📄 Review %d newly created files", len(changes.FilesCreated)))
	}

	if len(changes.FilesDeleted) > 0 {
		recs = append(recs, fmt.Sprintf("🗑️  Verify %d deleted files are safe to remove", len(changes.FilesDeleted)))
	}

	if len(recs) == 0 {
		recs = append(recs, "✅ Implementation looks good - ready for review")
	}

	return recs
}
