package agents

import (
	"context"
	"fmt"
	"log"
	"strings"
)

// ReflectionEngine implements LLM-as-Judge pattern for self-evaluation
// Based on Anthropic Reflection Pattern research
type ReflectionEngine struct {
	logger *log.Logger
	// Future: Add Oraculo client for AI-powered reflection
}

// NewReflectionEngine creates a new reflection engine
func NewReflectionEngine(logger *log.Logger) *ReflectionEngine {
	return &ReflectionEngine{
		logger: logger,
	}
}

// ReflectOnCodeQuality evaluates generated code quality
func (r *ReflectionEngine) ReflectOnCodeQuality(
	ctx context.Context,
	code string,
	language string,
	task string,
) (score float64, issues []string, suggestions []string) {

	r.logger.Printf("[Reflection] Evaluating code quality for %s", language)

	score = 100.0 // Start perfect
	issues = make([]string, 0)
	suggestions = make([]string, 0)

	// Template-based checks (will be replaced by LLM when Oraculo ready)

	// 1. Length check
	if len(code) < 50 {
		score -= 20
		issues = append(issues, "Code is very short - may be incomplete")
		suggestions = append(suggestions, "Ensure full implementation")
	}

	// 2. Error handling check
	if language == "go" && !strings.Contains(code, "error") {
		score -= 15
		issues = append(issues, "No error handling detected")
		suggestions = append(suggestions, "Add explicit error handling")
	}

	if language == "python" && !strings.Contains(code, "except") && !strings.Contains(code, "raise") {
		score -= 10
		issues = append(issues, "Limited exception handling")
		suggestions = append(suggestions, "Consider adding try/except blocks")
	}

	// 3. Documentation check
	hasComments := strings.Contains(code, "//") || strings.Contains(code, "/*") ||
		strings.Contains(code, "#") || strings.Contains(code, `"""`)

	if !hasComments {
		score -= 10
		issues = append(issues, "No documentation/comments found")
		suggestions = append(suggestions, "Add docstrings or comments")
	}

	// 4. TODO check (indicates incomplete)
	if strings.Contains(code, "TODO") || strings.Contains(code, "FIXME") {
		score -= 25
		issues = append(issues, "Contains TODO/FIXME markers - incomplete implementation")
		suggestions = append(suggestions, "Complete all TODO items")
	}

	// 5. Test presence check
	isTestCode := strings.Contains(task, "test") || strings.Contains(code, "test") ||
		strings.Contains(code, "Test") || strings.Contains(code, "assert")

	if !isTestCode && !strings.Contains(task, "example") {
		score -= 5
		suggestions = append(suggestions, "Consider adding tests")
	}

	// 6. Security patterns
	if containsAny(code, []string{"password", "secret", "token", "key"}) {
		if !containsAny(code, []string{"encrypt", "hash", "secure"}) {
			score -= 20
			issues = append(issues, "Security-sensitive code without encryption/hashing")
			suggestions = append(suggestions, "Add encryption for sensitive data")
		}
	}

	// 7. Complexity heuristic (very rough)
	lines := strings.Split(code, "\n")
	if len(lines) > 200 {
		score -= 10
		issues = append(issues, "Code is quite long - may need refactoring")
		suggestions = append(suggestions, "Consider breaking into smaller functions")
	}

	r.logger.Printf("[Reflection] Quality score: %.1f/100", score)
	r.logger.Printf("[Reflection] Issues found: %d", len(issues))

	return score, issues, suggestions
}

// ReflectOnCompilationError reflects on compilation/validation errors
func (r *ReflectionEngine) ReflectOnCompilationError(
	ctx context.Context,
	errorOutput string,
	code string,
	attemptNumber int,
) (reflection string, suggestedAction string) {

	r.logger.Printf("[Reflection] Analyzing compilation error (attempt %d)", attemptNumber)

	// Parse error type
	errorType, suggestions := ParseCompilationError(errorOutput)

	// Build reflection
	reflection = fmt.Sprintf("Attempt %d failed with %s. ", attemptNumber, errorType)

	// Add specific insights based on error type
	switch errorType {
	case "undefined_symbol":
		reflection += "The code references symbols that don't exist. "
		suggestedAction = "Add missing imports or fix symbol names"

	case "syntax_error":
		reflection += "The code has syntax issues. "
		suggestedAction = "Fix syntax errors in generated code"

	case "type_mismatch":
		reflection += "Type incompatibility detected. "
		suggestedAction = "Ensure type compatibility or add conversions"

	default:
		reflection += "Compilation failed. "
		suggestedAction = "Review error output and adjust code"
	}

	// Add suggestions from parser
	if len(suggestions) > 0 {
		reflection += "Specific issues: " + strings.Join(suggestions, ", ")
	}

	r.logger.Printf("[Reflection] %s", reflection)
	r.logger.Printf("[Reflection] Suggested action: %s", suggestedAction)

	return reflection, suggestedAction
}

// ReflectOnTestFailure reflects on test failures
func (r *ReflectionEngine) ReflectOnTestFailure(
	ctx context.Context,
	failedTests []string,
	testOutput string,
	attemptNumber int,
) (reflection string, suggestedAction string) {

	r.logger.Printf("[Reflection] Analyzing test failures (attempt %d)", attemptNumber)

	numFailed := len(failedTests)

	reflection = fmt.Sprintf("Attempt %d: %d test(s) failed. ", attemptNumber, numFailed)

	if numFailed == 1 {
		reflection += "Focus on fixing the single failing test. "
		suggestedAction = "Debug and fix the failing test case"
	} else if numFailed <= 3 {
		reflection += "A few tests are failing - likely related issues. "
		suggestedAction = "Fix the failing tests systematically"
	} else {
		reflection += "Many tests failing - may indicate fundamental issue. "
		suggestedAction = "Review core implementation logic"
	}

	// Extract common patterns from test output
	if strings.Contains(testOutput, "AssertionError") || strings.Contains(testOutput, "expected") {
		reflection += "Assertion failures suggest logic errors. "
	}

	if strings.Contains(testOutput, "timeout") || strings.Contains(testOutput, "hang") {
		reflection += "Timeout detected - may have infinite loop or deadlock. "
		suggestedAction = "Check for infinite loops or blocking operations"
	}

	if strings.Contains(testOutput, "panic") || strings.Contains(testOutput, "SIGSEGV") {
		reflection += "Crash detected - serious runtime error. "
		suggestedAction = "Fix crash-causing bug before proceeding"
	}

	r.logger.Printf("[Reflection] %s", reflection)

	return reflection, suggestedAction
}

// ReflectOnPlan evaluates an implementation plan
func (r *ReflectionEngine) ReflectOnPlan(
	ctx context.Context,
	plan *ImplementationPlan,
) (score float64, concerns []string, recommendations []string) {

	r.logger.Printf("[Reflection] Evaluating implementation plan: %s", plan.PlanID)

	score = 100.0
	concerns = make([]string, 0)
	recommendations = make([]string, 0)

	// Check complexity
	if plan.Complexity >= 8 {
		score -= 15
		concerns = append(concerns, "Very high complexity - high risk of failure")
		recommendations = append(recommendations, "Consider breaking into smaller tasks")
	} else if plan.Complexity >= 6 {
		score -= 5
		recommendations = append(recommendations, "Monitor complexity during implementation")
	}

	// Check risks
	if len(plan.Risks) > 3 {
		score -= 10
		concerns = append(concerns, fmt.Sprintf("%d risks identified - careful implementation needed", len(plan.Risks)))
	}

	// Check if tests are planned
	if len(plan.TestsNeeded) == 0 {
		score -= 20
		concerns = append(concerns, "No tests planned - quality verification will be limited")
		recommendations = append(recommendations, "Add test planning")
	}

	// Check file scope
	totalFiles := len(plan.FilesToCreate) + len(plan.FilesToModify) + len(plan.FilesToDelete)
	if totalFiles == 0 {
		score -= 30
		concerns = append(concerns, "No files identified - plan may be incomplete")
	} else if totalFiles > 10 {
		score -= 10
		concerns = append(concerns, "Large number of files affected - extensive changes")
	}

	// Check for deletions (higher risk)
	if len(plan.FilesToDelete) > 0 {
		score -= 5
		recommendations = append(recommendations, "Ensure deleted files are truly obsolete")
	}

	r.logger.Printf("[Reflection] Plan quality score: %.1f/100", score)
	r.logger.Printf("[Reflection] Concerns: %d, Recommendations: %d", len(concerns), len(recommendations))

	return score, concerns, recommendations
}

// Helper function
func containsAny(s string, substrs []string) bool {
	for _, substr := range substrs {
		if contains(s, substr) {
			return true
		}
	}
	return false
}
