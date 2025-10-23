package agents

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"log"
	"time"
)

// PlanningEngine generates implementation plans before code generation
// Based on Anthropic best practice: "Ask Claude to make a plan first"
type PlanningEngine struct {
	logger *log.Logger
}

// NewPlanningEngine creates a new planning engine
func NewPlanningEngine(logger *log.Logger) *PlanningEngine {
	return &PlanningEngine{
		logger: logger,
	}
}

// GeneratePlan creates an implementation plan for a task
// This is template-based for now - will integrate with Oraculo API later
func (p *PlanningEngine) GeneratePlan(
	task string,
	targets []string,
	language string,
	contextData map[string]interface{},
) (*ImplementationPlan, error) {

	p.logger.Printf("[Planning] Generating implementation plan for: %s", task)

	plan := &ImplementationPlan{
		PlanID:        generatePlanID(),
		Approach:      p.generateApproach(task, language),
		FilesToModify: make([]string, 0),
		FilesToCreate: make([]string, 0),
		FilesToDelete: make([]string, 0),
		TestsNeeded:   make([]string, 0),
		Risks:         make([]string, 0),
		Dependencies:  make([]string, 0),
		Complexity:    p.estimateComplexity(task),
		GeneratedAt:   time.Now(),
		UserApproved:  false,
	}

	// Analyze task to determine files affected
	p.analyzeTaskForFiles(task, targets, plan)

	// Identify tests needed
	p.identifyTestsNeeded(task, language, plan)

	// Identify risks
	p.identifyRisks(task, plan)

	// Identify dependencies
	p.identifyDependencies(task, language, contextData, plan)

	p.logger.Printf("[Planning] Plan generated: %s", plan.PlanID)
	p.logger.Printf("[Planning]   Complexity: %d/10", plan.Complexity)
	p.logger.Printf("[Planning]   Files to create: %d", len(plan.FilesToCreate))
	p.logger.Printf("[Planning]   Files to modify: %d", len(plan.FilesToModify))
	p.logger.Printf("[Planning]   Tests needed: %d", len(plan.TestsNeeded))
	p.logger.Printf("[Planning]   Risks identified: %d", len(plan.Risks))

	return plan, nil
}

// generateApproach generates a high-level approach description
func (p *PlanningEngine) generateApproach(task string, language string) string {
	// Template-based approach generation
	// TODO: Integrate with Oraculo for AI-generated approaches

	approach := fmt.Sprintf("Implement '%s' in %s:\n\n", task, language)

	// Detect task type
	if contains(task, "add") || contains(task, "create") {
		approach += "1. Create new file with implementation\n"
		approach += "2. Add necessary imports/dependencies\n"
		approach += "3. Implement core functionality\n"
		approach += "4. Add error handling\n"
		approach += "5. Write tests\n"
		approach += "6. Format and lint code\n"
	} else if contains(task, "refactor") {
		approach += "1. Analyze existing code\n"
		approach += "2. Identify refactoring opportunities\n"
		approach += "3. Apply refactoring while preserving behavior\n"
		approach += "4. Ensure tests still pass\n"
		approach += "5. Update documentation\n"
	} else if contains(task, "fix") {
		approach += "1. Reproduce the issue\n"
		approach += "2. Identify root cause\n"
		approach += "3. Implement fix\n"
		approach += "4. Add regression test\n"
		approach += "5. Verify fix resolves issue\n"
	} else {
		approach += "1. Analyze task requirements\n"
		approach += "2. Implement solution\n"
		approach += "3. Test implementation\n"
		approach += "4. Verify quality\n"
	}

	return approach
}

// analyzeTaskForFiles determines which files will be affected
func (p *PlanningEngine) analyzeTaskForFiles(task string, targets []string, plan *ImplementationPlan) {
	// Simplified analysis - real implementation would use AST/code analysis

	// If task says "add" or "create", we'll create new files
	if contains(task, "add") || contains(task, "create") || contains(task, "new") {
		// Generate filename from task
		filename := generateFilenameFromTask(task)
		plan.FilesToCreate = append(plan.FilesToCreate, filename)
	}

	// If task mentions specific files/modules, add to modify list
	if len(targets) > 0 {
		plan.FilesToModify = append(plan.FilesToModify, targets...)
	}
}

// identifyTestsNeeded determines what tests should be written
func (p *PlanningEngine) identifyTestsNeeded(task string, language string, plan *ImplementationPlan) {
	// Always recommend unit tests
	plan.TestsNeeded = append(plan.TestsNeeded, "Unit tests for core functionality")

	// Integration tests for certain task types
	if contains(task, "api") || contains(task, "endpoint") || contains(task, "service") {
		plan.TestsNeeded = append(plan.TestsNeeded, "Integration tests for API endpoints")
	}

	// E2E tests for UI-related tasks
	if contains(task, "ui") || contains(task, "interface") || contains(task, "frontend") {
		plan.TestsNeeded = append(plan.TestsNeeded, "E2E tests for user workflows")
	}
}

// identifyRisks identifies potential risks in implementation
func (p *PlanningEngine) identifyRisks(task string, plan *ImplementationPlan) {
	// Complexity risk
	if plan.Complexity >= 7 {
		plan.Risks = append(plan.Risks, "High complexity - may require multiple iterations")
	}

	// Breaking change risk
	if contains(task, "refactor") || contains(task, "change") {
		plan.Risks = append(plan.Risks, "Potential breaking changes to existing code")
	}

	// Security risk
	if contains(task, "auth") || contains(task, "security") || contains(task, "password") {
		plan.Risks = append(plan.Risks, "Security-critical code - requires careful review")
	}

	// Performance risk
	if contains(task, "performance") || contains(task, "optimize") {
		plan.Risks = append(plan.Risks, "Performance changes may have unintended side effects")
	}

	// Database risk
	if contains(task, "database") || contains(task, "migration") || contains(task, "schema") {
		plan.Risks = append(plan.Risks, "Database changes - ensure migrations are reversible")
	}
}

// identifyDependencies identifies required dependencies
func (p *PlanningEngine) identifyDependencies(task string, language string, contextData map[string]interface{}, plan *ImplementationPlan) {
	// Check context for existing dependencies
	if deps, ok := contextData["dependencies"].([]string); ok {
		plan.Dependencies = append(plan.Dependencies, deps...)
	}

	// Language-specific common dependencies
	if language == "python" {
		if contains(task, "test") {
			plan.Dependencies = append(plan.Dependencies, "pytest")
		}
		if contains(task, "http") || contains(task, "api") {
			plan.Dependencies = append(plan.Dependencies, "requests or httpx")
		}
	} else if language == "go" {
		if contains(task, "test") {
			plan.Dependencies = append(plan.Dependencies, "testing package (stdlib)")
		}
		if contains(task, "http") || contains(task, "api") {
			plan.Dependencies = append(plan.Dependencies, "net/http (stdlib)")
		}
	}
}

// estimateComplexity estimates task complexity on scale 1-10
func (p *PlanningEngine) estimateComplexity(task string) int {
	complexity := 3 // Base complexity

	// Increase for certain keywords
	keywords := map[string]int{
		"refactor": 2,
		"migrate": 3,
		"database": 2,
		"security": 2,
		"authentication": 3,
		"optimization": 2,
		"distributed": 3,
		"microservice": 2,
		"ai": 2,
		"machine learning": 3,
	}

	for keyword, points := range keywords {
		if contains(task, keyword) {
			complexity += points
		}
	}

	// Cap at 10
	if complexity > 10 {
		complexity = 10
	}

	return complexity
}

// generateFilenameFromTask generates a filename from task description
func generateFilenameFromTask(task string) string {
	// Very simplified - real implementation would be smarter
	// Convert "Add fibonacci function" -> "fibonacci.py" or "fibonacci.go"

	// Extract main noun/concept
	// For now, just use task and sanitize
	filename := task

	// Remove common prefixes
	filename = removePrefix(filename, "add ")
	filename = removePrefix(filename, "create ")
	filename = removePrefix(filename, "implement ")
	filename = removePrefix(filename, "write ")

	// Replace spaces with underscores
	filename = replaceSpaces(filename, "_")

	// Keep it short - take first 3-4 words
	words := splitWords(filename)
	if len(words) > 4 {
		words = words[:4]
	}
	filename = joinWords(words, "_")

	// Extension will be added by codegen strategy
	return filename
}

// generatePlanID generates a unique plan ID
func generatePlanID() string {
	bytes := make([]byte, 8)
	rand.Read(bytes)
	return "plan-" + hex.EncodeToString(bytes)
}

// Helper functions
func removePrefix(s, prefix string) string {
	if len(s) >= len(prefix) && s[:len(prefix)] == prefix {
		return s[len(prefix):]
	}
	return s
}

func replaceSpaces(s, replacement string) string {
	result := ""
	for i := 0; i < len(s); i++ {
		if s[i] == ' ' {
			result += replacement
		} else {
			result += string(s[i])
		}
	}
	return result
}

func splitWords(s string) []string {
	words := make([]string, 0)
	current := ""
	for i := 0; i < len(s); i++ {
		if s[i] == '_' || s[i] == ' ' {
			if current != "" {
				words = append(words, current)
				current = ""
			}
		} else {
			current += string(s[i])
		}
	}
	if current != "" {
		words = append(words, current)
	}
	return words
}

func joinWords(words []string, separator string) string {
	if len(words) == 0 {
		return ""
	}
	result := words[0]
	for i := 1; i < len(words); i++ {
		result += separator + words[i]
	}
	return result
}
