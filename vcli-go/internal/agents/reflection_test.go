package agents

import (
	"context"
	"log"
	"os"
	"testing"
	"time"
)

// Test: NewReflectionEngine - Basic Creation
func TestNewReflectionEngine_Creation(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	if engine == nil {
		t.Fatal("Reflection engine is nil")
	}

	if engine.logger == nil {
		t.Error("Logger is nil")
	}
}

// Test: ReflectOnCodeQuality - Well-Written Code
func TestReflectOnCodeQuality_WellWrittenCode(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `
package main

import "fmt"

// CalculateSum adds two integers and returns the result.
// It handles error cases by returning an error if inputs are invalid.
func CalculateSum(a, b int) (int, error) {
	if a < 0 || b < 0 {
		return 0, fmt.Errorf("negative numbers not allowed")
	}
	return a + b, nil
}

// Test for CalculateSum
func TestCalculateSum(t *testing.T) {
	result, err := CalculateSum(5, 10)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != 15 {
		t.Errorf("expected 15, got %d", result)
	}
}
`

	ctx := context.Background()
	score, issues, _ := engine.ReflectOnCodeQuality(ctx, code, "go", "Add sum function")

	if score <= 0 {
		t.Error("Expected positive quality score")
	}

	if score > 100 {
		t.Error("Score should not exceed 100")
	}

	// Well-written code should have fewer issues
	if len(issues) > 3 {
		t.Errorf("Expected few issues for well-written code, got %d", len(issues))
	}
}

// Test: ReflectOnCodeQuality - Short/Incomplete Code
func TestReflectOnCodeQuality_ShortIncompleteCode(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `func add() {}`

	ctx := context.Background()
	score, issues, _ := engine.ReflectOnCodeQuality(ctx, code, "go", "Add function")

	// Short code should get penalized
	if score >= 80 {
		t.Errorf("Expected lower score for short code, got %.1f", score)
	}

	// Should have issue about being short
	hasShortIssue := false
	for _, issue := range issues {
		if contains(issue, "short") || contains(issue, "incomplete") {
			hasShortIssue = true
			break
		}
	}

	if !hasShortIssue {
		t.Error("Expected issue about code being too short")
	}
}

// Test: ReflectOnCodeQuality - Go Code Without Error Handling
func TestReflectOnCodeQuality_GoNoErrorHandling(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `
package main

func CalculateSum(a, b int) int {
	return a + b
}

func ProcessData(data string) string {
	return data
}
`

	ctx := context.Background()
	_, issues, suggestions := engine.ReflectOnCodeQuality(ctx, code, "go", "Add functions")

	// Should detect missing error handling
	hasErrorHandlingIssue := false
	for _, issue := range issues {
		if contains(issue, "error") && contains(issue, "handling") {
			hasErrorHandlingIssue = true
			break
		}
	}

	if !hasErrorHandlingIssue {
		t.Error("Expected issue about missing error handling in Go code")
	}

	// Should suggest adding error handling
	hasErrorSuggestion := false
	for _, suggestion := range suggestions {
		if contains(suggestion, "error") {
			hasErrorSuggestion = true
			break
		}
	}

	if !hasErrorSuggestion {
		t.Error("Expected suggestion to add error handling")
	}
}

// Test: ReflectOnCodeQuality - Python Code Without Exception Handling
func TestReflectOnCodeQuality_PythonNoExceptionHandling(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `
def calculate_sum(a, b):
    return a + b

def process_data(data):
    return data.upper()
`

	ctx := context.Background()
	_, issues, suggestions := engine.ReflectOnCodeQuality(ctx, code, "python", "Add functions")

	// Should detect limited exception handling
	hasExceptionIssue := false
	for _, issue := range issues {
		if contains(issue, "exception") || contains(issue, "handling") {
			hasExceptionIssue = true
			break
		}
	}

	if !hasExceptionIssue {
		t.Error("Expected issue about limited exception handling in Python code")
	}

	// Should suggest try/except
	hasTryExceptSuggestion := false
	for _, suggestion := range suggestions {
		if contains(suggestion, "try") || contains(suggestion, "except") {
			hasTryExceptSuggestion = true
			break
		}
	}

	if !hasTryExceptSuggestion {
		t.Error("Expected suggestion to add try/except blocks")
	}
}

// Test: ReflectOnCodeQuality - Code Without Documentation
func TestReflectOnCodeQuality_NoDocumentation(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `
package main

func CalculateSum(a, b int) (int, error) {
	if a < 0 || b < 0 {
		return 0, fmt.Errorf("negative numbers not allowed")
	}
	return a + b, nil
}
`

	ctx := context.Background()
	_, issues, suggestions := engine.ReflectOnCodeQuality(ctx, code, "go", "Add sum function")

	// Should detect missing documentation
	hasDocIssue := false
	for _, issue := range issues {
		if contains(issue, "documentation") || contains(issue, "comment") {
			hasDocIssue = true
			break
		}
	}

	if !hasDocIssue {
		t.Error("Expected issue about missing documentation")
	}

	// Should suggest adding docs
	hasDocSuggestion := false
	for _, suggestion := range suggestions {
		if contains(suggestion, "docstring") || contains(suggestion, "comment") {
			hasDocSuggestion = true
			break
		}
	}

	if !hasDocSuggestion {
		t.Error("Expected suggestion to add documentation")
	}
}

// Test: ReflectOnCodeQuality - Code With TODOs
func TestReflectOnCodeQuality_WithTODOs(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `
package main

// CalculateSum adds two numbers
func CalculateSum(a, b int) (int, error) {
	// TODO: Add validation
	// FIXME: Handle overflow
	return a + b, nil
}
`

	ctx := context.Background()
	score, issues, suggestions := engine.ReflectOnCodeQuality(ctx, code, "go", "Add sum function")

	// Should heavily penalize TODOs
	if score >= 75 {
		t.Errorf("Expected significant penalty for TODO markers, got score %.1f", score)
	}

	// Should detect TODO markers
	hasTODOIssue := false
	for _, issue := range issues {
		if contains(issue, "TODO") || contains(issue, "FIXME") || contains(issue, "incomplete") {
			hasTODOIssue = true
			break
		}
	}

	if !hasTODOIssue {
		t.Error("Expected issue about TODO/FIXME markers")
	}

	// Should suggest completing TODOs
	hasCompleteSuggestion := false
	for _, suggestion := range suggestions {
		if contains(suggestion, "TODO") || contains(suggestion, "Complete") {
			hasCompleteSuggestion = true
			break
		}
	}

	if !hasCompleteSuggestion {
		t.Error("Expected suggestion to complete TODO items")
	}
}

// Test: ReflectOnCodeQuality - Security-Sensitive Code Without Encryption
func TestReflectOnCodeQuality_SecuritySensitiveNoEncryption(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `
package main

func StorePassword(password string) error {
	// Store password directly
	db.Save("password", password)
	return nil
}
`

	ctx := context.Background()
	_, issues, suggestions := engine.ReflectOnCodeQuality(ctx, code, "go", "Store user password")

	// Should detect security issue
	hasSecurityIssue := false
	for _, issue := range issues {
		if contains(issue, "Security") || contains(issue, "security") || contains(issue, "encrypt") {
			hasSecurityIssue = true
			break
		}
	}

	if !hasSecurityIssue {
		t.Error("Expected security issue for password handling without encryption")
	}

	// Should suggest encryption
	hasEncryptionSuggestion := false
	for _, suggestion := range suggestions {
		if contains(suggestion, "encrypt") || contains(suggestion, "hash") {
			hasEncryptionSuggestion = true
			break
		}
	}

	if !hasEncryptionSuggestion {
		t.Error("Expected suggestion to add encryption")
	}
}

// Test: ReflectOnCodeQuality - Very Long Code
func TestReflectOnCodeQuality_VeryLongCode(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	// Generate long code (>200 lines)
	code := "package main\n\nfunc LongFunction() {\n"
	for i := 0; i < 250; i++ {
		code += "    // Line " + string(rune(i)) + "\n"
	}
	code += "}\n"

	ctx := context.Background()
	_, issues, suggestions := engine.ReflectOnCodeQuality(ctx, code, "go", "Add long function")

	// Should detect code length issue
	hasLengthIssue := false
	for _, issue := range issues {
		if contains(issue, "long") || contains(issue, "refactor") {
			hasLengthIssue = true
			break
		}
	}

	if !hasLengthIssue {
		t.Error("Expected issue about code length")
	}

	// Should suggest breaking into smaller functions
	hasBreakdownSuggestion := false
	for _, suggestion := range suggestions {
		if contains(suggestion, "smaller") || contains(suggestion, "breaking") {
			hasBreakdownSuggestion = true
			break
		}
	}

	if !hasBreakdownSuggestion {
		t.Error("Expected suggestion to break into smaller functions")
	}
}

// Test: ReflectOnCodeQuality - Test Code (Should Not Penalize)
func TestReflectOnCodeQuality_TestCode(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	code := `
func TestCalculateSum(t *testing.T) {
	result := CalculateSum(5, 10)
	if result != 15 {
		t.Errorf("expected 15, got %d", result)
	}

	assert.Equal(t, 15, result, "sum should be 15")
}
`

	ctx := context.Background()
	score, _, _ := engine.ReflectOnCodeQuality(ctx, code, "go", "Add test for sum function")

	// Test code should not be penalized for not having tests
	if score < 70 {
		t.Errorf("Test code should not be heavily penalized, got score %.1f", score)
	}
}

// Test: ReflectOnCompilationError - Undefined Symbol
func TestReflectOnCompilationError_UndefinedSymbol(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	errorOutput := "error: undefined: fmt.Printfln"
	code := "fmt.Printfln(\"hello\")"

	ctx := context.Background()
	reflection, action := engine.ReflectOnCompilationError(ctx, errorOutput, code, 1)

	if reflection == "" {
		t.Error("Reflection should not be empty")
	}

	if !contains(reflection, "undefined") {
		t.Error("Reflection should mention undefined symbol")
	}

	if !contains(action, "import") || !contains(action, "symbol") {
		t.Errorf("Action should suggest fixing imports or symbols, got: %s", action)
	}
}

// Test: ReflectOnCompilationError - Syntax Error
func TestReflectOnCompilationError_SyntaxError(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	errorOutput := "syntax error: unexpected }"
	code := "func test() { return }"

	ctx := context.Background()
	reflection, action := engine.ReflectOnCompilationError(ctx, errorOutput, code, 1)

	if !contains(reflection, "syntax") {
		t.Error("Reflection should mention syntax error")
	}

	if !contains(action, "syntax") {
		t.Errorf("Action should suggest fixing syntax, got: %s", action)
	}
}

// Test: ReflectOnCompilationError - Type Mismatch
func TestReflectOnCompilationError_TypeMismatch(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	errorOutput := "type mismatch: cannot convert string to int"
	code := "var x int = \"hello\""

	ctx := context.Background()
	reflection, action := engine.ReflectOnCompilationError(ctx, errorOutput, code, 1)

	if !contains(reflection, "type") || !contains(reflection, "incompatibility") {
		t.Error("Reflection should mention type incompatibility")
	}

	if !contains(action, "type") {
		t.Errorf("Action should suggest type fixes, got: %s", action)
	}
}

// Test: ReflectOnCompilationError - Multiple Attempts
func TestReflectOnCompilationError_MultipleAttempts(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	errorOutput := "undefined: invalidFunc"
	code := "invalidFunc()"

	ctx := context.Background()

	// First attempt
	reflection1, _ := engine.ReflectOnCompilationError(ctx, errorOutput, code, 1)
	if !contains(reflection1, "Attempt 1") {
		t.Error("First reflection should mention Attempt 1")
	}

	// Second attempt
	reflection2, _ := engine.ReflectOnCompilationError(ctx, errorOutput, code, 2)
	if !contains(reflection2, "Attempt 2") {
		t.Error("Second reflection should mention Attempt 2")
	}

	// Third attempt
	reflection3, _ := engine.ReflectOnCompilationError(ctx, errorOutput, code, 3)
	if !contains(reflection3, "Attempt 3") {
		t.Error("Third reflection should mention Attempt 3")
	}
}

// Test: ReflectOnTestFailure - Single Test Failure
func TestReflectOnTestFailure_SingleTestFailure(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	failedTests := []string{"TestCalculateSum"}
	testOutput := "TestCalculateSum failed: expected 15, got 10"

	ctx := context.Background()
	reflection, action := engine.ReflectOnTestFailure(ctx, failedTests, testOutput, 1)

	if !contains(reflection, "1 test") || !contains(reflection, "failed") {
		t.Error("Reflection should mention single test failure")
	}

	if !contains(reflection, "single") {
		t.Error("Reflection should emphasize focusing on single test")
	}

	if !contains(action, "fix") || !contains(action, "test") {
		t.Errorf("Action should suggest fixing the test, got: %s", action)
	}
}

// Test: ReflectOnTestFailure - Few Tests Failure
func TestReflectOnTestFailure_FewTestsFailure(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	failedTests := []string{"TestAdd", "TestSubtract", "TestMultiply"}
	testOutput := "3 tests failed"

	ctx := context.Background()
	reflection, action := engine.ReflectOnTestFailure(ctx, failedTests, testOutput, 1)

	if !contains(reflection, "few") || !contains(reflection, "related") {
		t.Error("Reflection should mention few related failures")
	}

	if !contains(action, "systematically") {
		t.Error("Action should suggest systematic approach")
	}
}

// Test: ReflectOnTestFailure - Many Tests Failure
func TestReflectOnTestFailure_ManyTestsFailure(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	failedTests := []string{"Test1", "Test2", "Test3", "Test4", "Test5"}
	testOutput := "5 tests failed"

	ctx := context.Background()
	reflection, action := engine.ReflectOnTestFailure(ctx, failedTests, testOutput, 1)

	if !contains(reflection, "Many") || !contains(reflection, "fundamental") {
		t.Error("Reflection should mention many failures and fundamental issue")
	}

	if !contains(action, "core") || !contains(action, "implementation") {
		t.Error("Action should suggest reviewing core implementation")
	}
}

// Test: ReflectOnTestFailure - Assertion Error
func TestReflectOnTestFailure_AssertionError(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	failedTests := []string{"TestCalculate"}
	testOutput := "AssertionError: expected 15, got 10"

	ctx := context.Background()
	reflection, _ := engine.ReflectOnTestFailure(ctx, failedTests, testOutput, 1)

	if !contains(reflection, "Assertion") || !contains(reflection, "logic") {
		t.Error("Reflection should mention assertion failures and logic errors")
	}
}

// Test: ReflectOnTestFailure - Timeout
func TestReflectOnTestFailure_Timeout(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	failedTests := []string{"TestLongRunning"}
	testOutput := "timeout: test exceeded 30s"

	ctx := context.Background()
	reflection, action := engine.ReflectOnTestFailure(ctx, failedTests, testOutput, 1)

	if !contains(reflection, "Timeout") && !contains(reflection, "timeout") {
		t.Errorf("Reflection should mention timeout, got: %s", reflection)
	}

	if !contains(action, "infinite loop") && !contains(action, "blocking") {
		t.Errorf("Action should suggest checking for infinite loops or blocking, got: %s", action)
	}
}

// Test: ReflectOnTestFailure - Panic/Crash
func TestReflectOnTestFailure_Panic(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	failedTests := []string{"TestCrash"}
	testOutput := "panic: runtime error: invalid memory address"

	ctx := context.Background()
	reflection, action := engine.ReflectOnTestFailure(ctx, failedTests, testOutput, 1)

	if !contains(reflection, "Crash") && !contains(reflection, "crash") {
		t.Errorf("Reflection should mention crash, got: %s", reflection)
	}

	if !contains(action, "Fix crash") && !contains(action, "crash") && !contains(action, "bug") {
		t.Errorf("Action should suggest fixing crash-causing bug, got: %s", action)
	}
}

// Test: ReflectOnPlan - Good Quality Plan
func TestReflectOnPlan_GoodQualityPlan(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	plan := &ImplementationPlan{
		PlanID:        "plan-123",
		Approach:      "Well-structured approach",
		FilesToModify: []string{"file1.go", "file2.go"},
		FilesToCreate: []string{"new_file.go"},
		FilesToDelete: []string{},
		TestsNeeded:   []string{"Unit tests", "Integration tests"},
		Risks:         []string{"Minor risk 1"},
		Complexity:    4,
		GeneratedAt:   time.Now(),
	}

	ctx := context.Background()
	score, concerns, _ := engine.ReflectOnPlan(ctx, plan)

	if score <= 0 {
		t.Error("Expected positive plan quality score")
	}

	if score > 100 {
		t.Error("Score should not exceed 100")
	}

	// Good plan should have few concerns
	if len(concerns) > 2 {
		t.Errorf("Expected few concerns for good plan, got %d", len(concerns))
	}
}

// Test: ReflectOnPlan - High Complexity
func TestReflectOnPlan_HighComplexity(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	plan := &ImplementationPlan{
		PlanID:        "plan-123",
		Complexity:    9,
		FilesToModify: []string{"file.go"},
		TestsNeeded:   []string{"tests"},
		Risks:         []string{},
		GeneratedAt:   time.Now(),
	}

	ctx := context.Background()
	score, concerns, _ := engine.ReflectOnPlan(ctx, plan)

	// High complexity should reduce score
	if score >= 90 {
		t.Errorf("Expected lower score for high complexity, got %.1f", score)
	}

	// Should have complexity concern
	hasComplexityConcern := false
	for _, concern := range concerns {
		if contains(concern, "complexity") || contains(concern, "complex") {
			hasComplexityConcern = true
			break
		}
	}

	if !hasComplexityConcern {
		t.Error("Expected concern about high complexity")
	}
}

// Test: ReflectOnPlan - Many Risks
func TestReflectOnPlan_ManyRisks(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	plan := &ImplementationPlan{
		PlanID:        "plan-123",
		Complexity:    5,
		FilesToModify: []string{"file.go"},
		TestsNeeded:   []string{"tests"},
		Risks:         []string{"Risk 1", "Risk 2", "Risk 3", "Risk 4"},
		GeneratedAt:   time.Now(),
	}

	ctx := context.Background()
	_, concerns, _ := engine.ReflectOnPlan(ctx, plan)

	// Should have risk concern
	hasRiskConcern := false
	for _, concern := range concerns {
		if contains(concern, "risk") || contains(concern, "Risk") {
			hasRiskConcern = true
			break
		}
	}

	if !hasRiskConcern {
		t.Error("Expected concern about multiple risks")
	}
}

// Test: ReflectOnPlan - No Tests Planned
func TestReflectOnPlan_NoTestsPlanned(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	plan := &ImplementationPlan{
		PlanID:        "plan-123",
		Complexity:    3,
		FilesToModify: []string{"file.go"},
		TestsNeeded:   []string{}, // No tests
		Risks:         []string{},
		GeneratedAt:   time.Now(),
	}

	ctx := context.Background()
	score, concerns, recommendations := engine.ReflectOnPlan(ctx, plan)

	// No tests should significantly reduce score
	if score > 80 {
		t.Errorf("Expected lower score for plan without tests, got %.1f", score)
	}

	// Should have concern about tests
	hasTestConcern := false
	for _, concern := range concerns {
		if contains(concern, "test") || contains(concern, "Test") {
			hasTestConcern = true
			break
		}
	}

	if !hasTestConcern {
		t.Error("Expected concern about missing tests")
	}

	// Should recommend adding tests
	hasTestRecommendation := false
	for _, rec := range recommendations {
		if contains(rec, "test") || contains(rec, "Test") {
			hasTestRecommendation = true
			break
		}
	}

	if !hasTestRecommendation {
		t.Error("Expected recommendation to add tests")
	}
}

// Test: ReflectOnPlan - No Files Identified
func TestReflectOnPlan_NoFilesIdentified(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	plan := &ImplementationPlan{
		PlanID:        "plan-123",
		Complexity:    3,
		FilesToModify: []string{},
		FilesToCreate: []string{},
		FilesToDelete: []string{},
		TestsNeeded:   []string{"tests"},
		Risks:         []string{},
		GeneratedAt:   time.Now(),
	}

	ctx := context.Background()
	score, concerns, _ := engine.ReflectOnPlan(ctx, plan)

	// No files should heavily reduce score
	if score > 70 {
		t.Errorf("Expected lower score for plan with no files, got %.1f", score)
	}

	// Should have concern about missing files
	hasFileConcern := false
	for _, concern := range concerns {
		if contains(concern, "file") || contains(concern, "incomplete") {
			hasFileConcern = true
			break
		}
	}

	if !hasFileConcern {
		t.Error("Expected concern about no files identified")
	}
}

// Test: ReflectOnPlan - Many Files
func TestReflectOnPlan_ManyFiles(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	manyFiles := make([]string, 15)
	for i := 0; i < 15; i++ {
		manyFiles[i] = "file" + string(rune(i)) + ".go"
	}

	plan := &ImplementationPlan{
		PlanID:        "plan-123",
		Complexity:    5,
		FilesToModify: manyFiles,
		TestsNeeded:   []string{"tests"},
		Risks:         []string{},
		GeneratedAt:   time.Now(),
	}

	ctx := context.Background()
	_, concerns, _ := engine.ReflectOnPlan(ctx, plan)

	// Should have concern about large scope
	hasScopeConcern := false
	for _, concern := range concerns {
		if contains(concern, "Large") || contains(concern, "extensive") || contains(concern, "files") {
			hasScopeConcern = true
			break
		}
	}

	if !hasScopeConcern {
		t.Error("Expected concern about large number of files")
	}
}

// Test: ReflectOnPlan - File Deletions
func TestReflectOnPlan_FileDeletions(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	engine := NewReflectionEngine(logger)

	plan := &ImplementationPlan{
		PlanID:        "plan-123",
		Complexity:    3,
		FilesToModify: []string{"file.go"},
		FilesToDelete: []string{"old_file.go", "deprecated.go"},
		TestsNeeded:   []string{"tests"},
		Risks:         []string{},
		GeneratedAt:   time.Now(),
	}

	ctx := context.Background()
	_, _, recommendations := engine.ReflectOnPlan(ctx, plan)

	// Should recommend verifying deletions
	hasDeletionRecommendation := false
	for _, rec := range recommendations {
		if contains(rec, "delet") || contains(rec, "obsolete") {
			hasDeletionRecommendation = true
			break
		}
	}

	if !hasDeletionRecommendation {
		t.Error("Expected recommendation about file deletions")
	}
}
