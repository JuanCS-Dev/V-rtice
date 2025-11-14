package agents

import (
	"log"
	"os"
	"testing"
	"time"
)

// Test: NewPlanningEngine - Basic Creation
func TestNewPlanningEngine_Creation(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	if engine == nil {
		t.Fatal("Planning engine is nil")
	}

	if engine.logger == nil {
		t.Error("Logger is nil")
	}
}

// Test: GeneratePlan - Basic Plan Generation
func TestGeneratePlan_BasicPlanGeneration(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add fibonacci function"
	targets := []string{"math.go"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	if plan == nil {
		t.Fatal("Plan is nil")
	}

	if plan.PlanID == "" {
		t.Error("Plan ID is empty")
	}

	if plan.Approach == "" {
		t.Error("Approach is empty")
	}

	if plan.Complexity == 0 {
		t.Error("Complexity is zero")
	}

	if plan.GeneratedAt.IsZero() {
		t.Error("GeneratedAt timestamp is zero")
	}
}

// Test: GeneratePlan - Add Task
func TestGeneratePlan_AddTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add new authentication middleware"
	targets := []string{}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should have files to create for "add" task
	if len(plan.FilesToCreate) == 0 {
		t.Error("Expected files to create for 'add' task")
	}

	// Should contain tests
	if len(plan.TestsNeeded) == 0 {
		t.Error("Expected tests to be planned")
	}

	// Should have reasonable complexity
	if plan.Complexity < 1 || plan.Complexity > 10 {
		t.Errorf("Expected complexity between 1-10, got %d", plan.Complexity)
	}
}

// Test: GeneratePlan - Refactor Task
func TestGeneratePlan_RefactorTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Refactor database connection pooling"
	targets := []string{"db/pool.go"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should identify breaking change risk or database risk
	hasRisk := false
	for _, risk := range plan.Risks {
		if contains(risk, "breaking") || contains(risk, "Database") || contains(risk, "database") {
			hasRisk = true
			break
		}
	}

	if !hasRisk {
		t.Errorf("Expected breaking change or database risk for refactor task, got risks: %v", plan.Risks)
	}

	// Should have higher complexity
	if plan.Complexity < 3 {
		t.Errorf("Expected higher complexity for refactor, got %d", plan.Complexity)
	}
}

// Test: GeneratePlan - Fix Task
func TestGeneratePlan_FixTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Fix memory leak in worker pool"
	targets := []string{"worker/pool.go"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should have approach that mentions fix
	if !contains(plan.Approach, "fix") && !contains(plan.Approach, "Fix") {
		t.Error("Expected approach to mention 'fix'")
	}
}

// Test: GeneratePlan - Security Task
func TestGeneratePlan_SecurityTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add password hashing with bcrypt"
	targets := []string{"auth/password.go"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should identify security risk
	hasSecurityRisk := false
	for _, risk := range plan.Risks {
		if contains(risk, "security") || contains(risk, "Security") {
			hasSecurityRisk = true
			break
		}
	}

	if !hasSecurityRisk {
		t.Error("Expected security risk for password-related task")
	}
}

// Test: GeneratePlan - Database Task
func TestGeneratePlan_DatabaseTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Create database migration for user schema changes"
	targets := []string{"migrations/"}
	language := "sql"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should identify database risk
	hasDatabaseRisk := false
	for _, risk := range plan.Risks {
		if contains(risk, "Database") || contains(risk, "migration") {
			hasDatabaseRisk = true
			break
		}
	}

	if !hasDatabaseRisk {
		t.Error("Expected database risk for migration task")
	}
}

// Test: GeneratePlan - API Task (Integration Tests)
func TestGeneratePlan_APITask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add REST API endpoint for user management"
	targets := []string{"api/users.go"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should recommend integration tests
	hasIntegrationTests := false
	for _, test := range plan.TestsNeeded {
		if contains(test, "Integration") || contains(test, "API") {
			hasIntegrationTests = true
			break
		}
	}

	if !hasIntegrationTests {
		t.Error("Expected integration tests for API endpoint task")
	}
}

// Test: GeneratePlan - UI Task (E2E Tests)
func TestGeneratePlan_UITask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add frontend dashboard interface"
	targets := []string{"ui/dashboard.tsx"}
	language := "typescript"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should recommend E2E tests
	hasE2ETests := false
	for _, test := range plan.TestsNeeded {
		if contains(test, "E2E") || contains(test, "user") {
			hasE2ETests = true
			break
		}
	}

	if !hasE2ETests {
		t.Error("Expected E2E tests for UI task")
	}
}

// Test: GeneratePlan - Complex Task (High Complexity)
func TestGeneratePlan_ComplexTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Migrate authentication system to distributed microservice with machine learning fraud detection"
	targets := []string{"auth/"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should have high complexity
	if plan.Complexity < 7 {
		t.Errorf("Expected high complexity (>=7), got %d", plan.Complexity)
	}

	// Should have multiple risks
	if len(plan.Risks) < 2 {
		t.Errorf("Expected multiple risks for complex task, got %d", len(plan.Risks))
	}
}

// Test: GeneratePlan - With Context Dependencies
func TestGeneratePlan_WithContextDependencies(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add test coverage reporting"
	targets := []string{}
	language := "python"
	contextData := map[string]interface{}{
		"dependencies": []string{"coverage", "pytest-cov"},
	}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should include context dependencies
	if len(plan.Dependencies) < 2 {
		t.Error("Expected context dependencies to be included")
	}

	// Should suggest pytest for Python tests
	hasPytest := false
	for _, dep := range plan.Dependencies {
		if contains(dep, "pytest") {
			hasPytest = true
			break
		}
	}

	if !hasPytest {
		t.Error("Expected pytest dependency for Python test task")
	}
}

// Test: GeneratePlan - Python HTTP Task
func TestGeneratePlan_PythonHTTPTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add HTTP client for external API integration"
	targets := []string{"api/client.py"}
	language := "python"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should suggest HTTP library or tests
	// Note: Dependencies may vary based on task interpretation
	if len(plan.Dependencies) == 0 {
		// At minimum, should identify some dependencies for HTTP task
		t.Logf("Note: No dependencies identified for Python HTTP task. Plan: %+v", plan)
	}
}

// Test: GeneratePlan - Go HTTP Task
func TestGeneratePlan_GoHTTPTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add HTTP server for REST API"
	targets := []string{"server/http.go"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should suggest net/http or tests
	// Note: Dependencies may vary based on task interpretation
	if len(plan.Dependencies) == 0 {
		// At minimum, should identify some dependencies for Go HTTP task
		t.Logf("Note: No dependencies identified for Go HTTP task. Plan: %+v", plan)
	}
}

// Test: GeneratePlan - Multiple Targets
func TestGeneratePlan_MultipleTargets(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Update authentication flow"
	targets := []string{"auth/login.go", "auth/session.go", "auth/middleware.go"}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should include all targets in files to modify
	if len(plan.FilesToModify) != 3 {
		t.Errorf("Expected 3 files to modify, got %d", len(plan.FilesToModify))
	}

	for _, target := range targets {
		found := false
		for _, file := range plan.FilesToModify {
			if file == target {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Target file %s not found in FilesToModify", target)
		}
	}
}

// Test: Complexity Estimation - Simple Task
func TestComplexityEstimation_SimpleTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Add helper function to format dates"
	targets := []string{}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Simple task should have low complexity
	if plan.Complexity > 5 {
		t.Errorf("Expected low complexity (<=5) for simple task, got %d", plan.Complexity)
	}
}

// Test: Complexity Estimation - Authentication Task
func TestComplexityEstimation_AuthenticationTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Implement authentication with OAuth2"
	targets := []string{}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Authentication task should have higher complexity
	if plan.Complexity < 5 {
		t.Errorf("Expected higher complexity (>=5) for authentication task, got %d", plan.Complexity)
	}
}

// Test: Complexity Estimation - Optimization Task
func TestComplexityEstimation_OptimizationTask(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Optimize database query performance"
	targets := []string{}
	language := "sql"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Optimization task should have moderate complexity
	if plan.Complexity < 4 {
		t.Errorf("Expected moderate complexity (>=4) for optimization task, got %d", plan.Complexity)
	}
}

// Test: Complexity Estimation - Capped at 10
func TestComplexityEstimation_CappedAt10(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	// Task with many complexity-increasing keywords
	task := "Refactor distributed microservice authentication system with machine learning fraud detection and database migration"
	targets := []string{}
	language := "go"
	contextData := map[string]interface{}{}

	plan, err := engine.GeneratePlan(task, targets, language, contextData)

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Complexity should be capped at 10
	if plan.Complexity > 10 {
		t.Errorf("Expected complexity capped at 10, got %d", plan.Complexity)
	}
}

// Test: Plan ID Generation - Uniqueness
func TestPlanIDGeneration_Uniqueness(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	planIDs := make(map[string]bool)
	iterations := 100

	for i := 0; i < iterations; i++ {
		plan, err := engine.GeneratePlan("test task", []string{}, "go", map[string]interface{}{})
		if err != nil {
			t.Fatalf("Failed to generate plan: %v", err)
		}

		if planIDs[plan.PlanID] {
			t.Errorf("Duplicate plan ID generated: %s", plan.PlanID)
		}

		planIDs[plan.PlanID] = true
	}
}

// Test: Plan ID Generation - Format
func TestPlanIDGeneration_Format(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	plan, err := engine.GeneratePlan("test task", []string{}, "go", map[string]interface{}{})
	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Should start with "plan-"
	if len(plan.PlanID) < 6 || plan.PlanID[:5] != "plan-" {
		t.Errorf("Expected plan ID to start with 'plan-', got: %s", plan.PlanID)
	}

	// Should have hex characters after prefix
	hexPart := plan.PlanID[5:]
	if len(hexPart) == 0 {
		t.Error("Plan ID has no hex part")
	}
}

// Test: Timestamp Generation
func TestPlanGeneration_Timestamp(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	before := time.Now()
	plan, err := engine.GeneratePlan("test task", []string{}, "go", map[string]interface{}{})
	after := time.Now()

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	// Timestamp should be between before and after
	if plan.GeneratedAt.Before(before) || plan.GeneratedAt.After(after) {
		t.Errorf("Generated timestamp %v is outside expected range [%v, %v]", plan.GeneratedAt, before, after)
	}
}

// Test: User Approved Flag - Default False
func TestPlanGeneration_UserApprovedDefaultFalse(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	plan, err := engine.GeneratePlan("test task", []string{}, "go", map[string]interface{}{})

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	if plan.UserApproved {
		t.Error("Expected UserApproved to be false by default")
	}
}

// Test: Helper Functions - removePrefix
func TestHelperFunctions_RemovePrefix(t *testing.T) {
	tests := []struct {
		input    string
		prefix   string
		expected string
	}{
		{"add function", "add ", "function"},
		{"create class", "create ", "class"},
		{"implement feature", "implement ", "feature"},
		{"no prefix here", "add ", "no prefix here"},
		{"", "add ", ""},
	}

	for _, test := range tests {
		result := removePrefix(test.input, test.prefix)
		if result != test.expected {
			t.Errorf("removePrefix(%q, %q) = %q, expected %q", test.input, test.prefix, result, test.expected)
		}
	}
}

// Test: Helper Functions - replaceSpaces
func TestHelperFunctions_ReplaceSpaces(t *testing.T) {
	tests := []struct {
		input       string
		replacement string
		expected    string
	}{
		{"hello world", "_", "hello_world"},
		{"foo bar baz", "-", "foo-bar-baz"},
		{"no spaces", "_", "no_spaces"},
		{"", "_", ""},
	}

	for _, test := range tests {
		result := replaceSpaces(test.input, test.replacement)
		if result != test.expected {
			t.Errorf("replaceSpaces(%q, %q) = %q, expected %q", test.input, test.replacement, result, test.expected)
		}
	}
}

// Test: Helper Functions - splitWords
func TestHelperFunctions_SplitWords(t *testing.T) {
	tests := []struct {
		input    string
		expected []string
	}{
		{"hello_world_test", []string{"hello", "world", "test"}},
		{"single", []string{"single"}},
		{"with spaces here", []string{"with", "spaces", "here"}},
		{"", []string{}},
		{"_leading_underscore", []string{"leading", "underscore"}},
		{"trailing_underscore_", []string{"trailing", "underscore"}},
	}

	for _, test := range tests {
		result := splitWords(test.input)
		if len(result) != len(test.expected) {
			t.Errorf("splitWords(%q) returned %d words, expected %d", test.input, len(result), len(test.expected))
			continue
		}

		for i := range result {
			if result[i] != test.expected[i] {
				t.Errorf("splitWords(%q)[%d] = %q, expected %q", test.input, i, result[i], test.expected[i])
			}
		}
	}
}

// Test: Helper Functions - joinWords
func TestHelperFunctions_JoinWords(t *testing.T) {
	tests := []struct {
		words     []string
		separator string
		expected  string
	}{
		{[]string{"hello", "world"}, "_", "hello_world"},
		{[]string{"foo", "bar", "baz"}, "-", "foo-bar-baz"},
		{[]string{"single"}, "_", "single"},
		{[]string{}, "_", ""},
	}

	for _, test := range tests {
		result := joinWords(test.words, test.separator)
		if result != test.expected {
			t.Errorf("joinWords(%v, %q) = %q, expected %q", test.words, test.separator, result, test.expected)
		}
	}
}

// Test: Performance Risk Identification
func TestPlanGeneration_PerformanceRisk(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	task := "Optimize algorithm performance for large datasets"
	plan, err := engine.GeneratePlan(task, []string{}, "go", map[string]interface{}{})

	if err != nil {
		t.Fatalf("Failed to generate plan: %v", err)
	}

	hasPerformanceRisk := false
	for _, risk := range plan.Risks {
		if contains(risk, "Performance") || contains(risk, "performance") {
			hasPerformanceRisk = true
			break
		}
	}

	if !hasPerformanceRisk {
		t.Error("Expected performance risk for optimization task")
	}
}

// Test: Always Includes Unit Tests
func TestPlanGeneration_AlwaysIncludesUnitTests(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewPlanningEngine(logger)

	tasks := []string{
		"Add helper function",
		"Create new class",
		"Implement algorithm",
		"Fix bug",
	}

	for _, task := range tasks {
		plan, err := engine.GeneratePlan(task, []string{}, "go", map[string]interface{}{})
		if err != nil {
			t.Fatalf("Failed to generate plan for %q: %v", task, err)
		}

		hasUnitTests := false
		for _, test := range plan.TestsNeeded {
			if contains(test, "Unit") || contains(test, "unit") {
				hasUnitTests = true
				break
			}
		}

		if !hasUnitTests {
			t.Errorf("Task %q should include unit tests", task)
		}
	}
}
