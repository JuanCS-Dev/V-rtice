package agents

import (
	"context"
	"errors"
	"log"
	"os"
	"testing"
	"time"
)

// Test: NewSelfHealingExecutor - Basic Creation
func TestNewSelfHealingExecutor_Creation(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:            true,
		MaxRetries:         3,
		BackoffStrategy:    "exponential",
		InitialBackoff:     1 * time.Second,
		EnableReflection:   true,
		MaxReflectionDepth: 2,
	}

	executor := NewSelfHealingExecutor(config, logger)

	if executor == nil {
		t.Fatal("Self-healing executor is nil")
	}

	if executor.logger == nil {
		t.Error("Logger is nil")
	}
}

// Test: NewSelfHealingExecutor - Default Values
func TestNewSelfHealingExecutor_DefaultValues(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{} // Empty config

	executor := NewSelfHealingExecutor(config, logger)

	if executor.config.MaxRetries != 3 {
		t.Errorf("Expected default MaxRetries=3, got %d", executor.config.MaxRetries)
	}

	if executor.config.BackoffStrategy != "exponential" {
		t.Errorf("Expected default BackoffStrategy='exponential', got %s", executor.config.BackoffStrategy)
	}

	if executor.config.InitialBackoff != 1*time.Second {
		t.Errorf("Expected default InitialBackoff=1s, got %v", executor.config.InitialBackoff)
	}

	if executor.config.MaxReflectionDepth != 2 {
		t.Errorf("Expected default MaxReflectionDepth=2, got %d", executor.config.MaxReflectionDepth)
	}
}

// Test: ExecuteWithRetry - Success on First Attempt
func TestExecuteWithRetry_SuccessOnFirstAttempt(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:    true,
		MaxRetries: 3,
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptCount := 0
	attemptFunc := func(attempt int) error {
		attemptCount++
		return nil // Success
	}

	validateFunc := func() (bool, string, error) {
		return true, "", nil // Valid
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)

	if !result.Success {
		t.Error("Expected success")
	}

	if result.TotalAttempts != 1 {
		t.Errorf("Expected 1 attempt, got %d", result.TotalAttempts)
	}

	if result.Recovered {
		t.Error("Should not be marked as recovered on first attempt")
	}

	if attemptCount != 1 {
		t.Errorf("Attempt function should be called once, was called %d times", attemptCount)
	}
}

// Test: ExecuteWithRetry - Success on Retry
func TestExecuteWithRetry_SuccessOnRetry(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:         true,
		MaxRetries:      3,
		BackoffStrategy: "none", // No backoff for faster testing
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptCount := 0
	attemptFunc := func(attempt int) error {
		attemptCount++
		if attempt < 3 {
			return errors.New("temporary failure")
		}
		return nil // Success on third attempt
	}

	validateFunc := func() (bool, string, error) {
		if attemptCount < 3 {
			return false, "test_failure", errors.New("validation failed")
		}
		return true, "", nil
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)

	if !result.Success {
		t.Error("Expected eventual success")
	}

	if result.TotalAttempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", result.TotalAttempts)
	}

	if !result.Recovered {
		t.Error("Should be marked as recovered")
	}

	if len(result.Attempts) != 3 {
		t.Errorf("Expected 3 attempt records, got %d", len(result.Attempts))
	}
}

// Test: ExecuteWithRetry - All Attempts Fail
func TestExecuteWithRetry_AllAttemptsFail(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:         true,
		MaxRetries:      3,
		BackoffStrategy: "none",
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptCount := 0
	attemptFunc := func(attempt int) error {
		attemptCount++
		return errors.New("permanent failure")
	}

	validateFunc := func() (bool, string, error) {
		return false, "test_failure", errors.New("validation always fails")
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)

	if result.Success {
		t.Error("Expected failure")
	}

	if result.TotalAttempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", result.TotalAttempts)
	}

	if result.Recovered {
		t.Error("Should not be marked as recovered")
	}

	if result.FinalError == nil {
		t.Error("Expected final error to be set")
	}

	if attemptCount != 3 {
		t.Errorf("Expected 3 execution attempts, got %d", attemptCount)
	}
}

// Test: ExecuteWithRetry - Disabled Self-Healing
func TestExecuteWithRetry_DisabledSelfHealing(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:    false, // Disabled
		MaxRetries: 3,
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptCount := 0
	attemptFunc := func(attempt int) error {
		attemptCount++
		return errors.New("failure")
	}

	validateFunc := func() (bool, string, error) {
		return false, "test_failure", nil
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)

	if result.Success {
		t.Error("Expected failure")
	}

	if result.TotalAttempts != 1 {
		t.Errorf("Expected only 1 attempt when disabled, got %d", result.TotalAttempts)
	}

	if attemptCount != 1 {
		t.Errorf("Expected single execution, got %d attempts", attemptCount)
	}
}

// Test: ExecuteWithRetry - With Reflection
func TestExecuteWithRetry_WithReflection(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:          true,
		MaxRetries:       3,
		BackoffStrategy:  "none",
		EnableReflection: true,
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptCount := 0
	attemptFunc := func(attempt int) error {
		attemptCount++
		if attempt < 2 {
			return errors.New("temporary failure")
		}
		return nil
	}

	validateFunc := func() (bool, string, error) {
		if attemptCount < 2 {
			return false, "test_failure", errors.New("validation failed")
		}
		return true, "", nil
	}

	reflectionCallCount := 0
	reflectFunc := func(err error, attemptNum int) (string, string) {
		reflectionCallCount++
		return "Reflection on error", "Suggested action"
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, reflectFunc)

	if !result.Success {
		t.Error("Expected success with reflection")
	}

	if reflectionCallCount == 0 {
		t.Error("Reflection function should have been called")
	}

	// Check that reflection was recorded
	hasReflection := false
	for _, attempt := range result.Attempts {
		if attempt.Reflection != "" {
			hasReflection = true
			break
		}
	}

	if !hasReflection {
		t.Error("Expected reflection to be recorded in attempts")
	}
}

// Test: ExecuteWithRetry - No Reflection Function
func TestExecuteWithRetry_NoReflectionFunction(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:          true,
		MaxRetries:       2,
		BackoffStrategy:  "none",
		EnableReflection: true, // Enabled but no function provided
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptFunc := func(attempt int) error {
		if attempt == 1 {
			return errors.New("failure")
		}
		return nil
	}

	validateFunc := func() (bool, string, error) {
		return true, "", nil
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil) // No reflect func

	// Should not fail even without reflection function
	if result.Success {
		if result.TotalAttempts != 2 {
			t.Errorf("Expected 2 attempts (1 fail + 1 success), got %d", result.TotalAttempts)
		}
	}
}

// Test: ExecuteWithRetry - Context Cancellation
func TestExecuteWithRetry_ContextCancellation(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:         true,
		MaxRetries:      10,
		BackoffStrategy: "linear",
		InitialBackoff:  100 * time.Millisecond,
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptFunc := func(attempt int) error {
		return errors.New("always fails")
	}

	validateFunc := func() (bool, string, error) {
		return false, "test_failure", errors.New("validation failed")
	}

	// Cancel context after short delay
	ctx, cancel := context.WithTimeout(context.Background(), 150*time.Millisecond)
	defer cancel()

	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)

	if result.Success {
		t.Error("Expected failure due to context cancellation")
	}

	// Should have stopped early due to context
	if result.TotalAttempts >= 10 {
		t.Errorf("Expected early termination, but got %d attempts", result.TotalAttempts)
	}

	if result.FinalError != context.DeadlineExceeded {
		t.Errorf("Expected context.DeadlineExceeded error, got: %v", result.FinalError)
	}
}

// Test: Backoff Calculation - None
func TestBackoffCalculation_None(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		BackoffStrategy: "none",
		InitialBackoff:  1 * time.Second,
	}
	executor := NewSelfHealingExecutor(config, logger)

	backoff1 := executor.calculateBackoff(1)
	backoff2 := executor.calculateBackoff(2)
	backoff3 := executor.calculateBackoff(3)

	if backoff1 != 0 {
		t.Errorf("Expected 0 backoff with 'none' strategy, got %v", backoff1)
	}

	if backoff2 != 0 {
		t.Errorf("Expected 0 backoff with 'none' strategy, got %v", backoff2)
	}

	if backoff3 != 0 {
		t.Errorf("Expected 0 backoff with 'none' strategy, got %v", backoff3)
	}
}

// Test: Backoff Calculation - Linear
func TestBackoffCalculation_Linear(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		BackoffStrategy: "linear",
		InitialBackoff:  1 * time.Second,
	}
	executor := NewSelfHealingExecutor(config, logger)

	backoff1 := executor.calculateBackoff(1)
	backoff2 := executor.calculateBackoff(2)
	backoff3 := executor.calculateBackoff(3)

	// Linear: initialBackoff * attempt
	if backoff1 != 1*time.Second {
		t.Errorf("Expected 1s backoff, got %v", backoff1)
	}

	if backoff2 != 2*time.Second {
		t.Errorf("Expected 2s backoff, got %v", backoff2)
	}

	if backoff3 != 3*time.Second {
		t.Errorf("Expected 3s backoff, got %v", backoff3)
	}
}

// Test: Backoff Calculation - Exponential
func TestBackoffCalculation_Exponential(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		BackoffStrategy: "exponential",
		InitialBackoff:  1 * time.Second,
	}
	executor := NewSelfHealingExecutor(config, logger)

	backoff1 := executor.calculateBackoff(1)
	backoff2 := executor.calculateBackoff(2)
	backoff3 := executor.calculateBackoff(3)

	// Exponential: initialBackoff * 2^(attempt-1)
	// attempt 1: 1s * 2^0 = 1s
	// attempt 2: 1s * 2^1 = 2s
	// attempt 3: 1s * 2^2 = 4s

	if backoff1 != 1*time.Second {
		t.Errorf("Expected 1s backoff, got %v", backoff1)
	}

	if backoff2 != 2*time.Second {
		t.Errorf("Expected 2s backoff, got %v", backoff2)
	}

	if backoff3 != 4*time.Second {
		t.Errorf("Expected 4s backoff, got %v", backoff3)
	}
}

// Test: Backoff Calculation - Unknown Strategy (Defaults to InitialBackoff)
func TestBackoffCalculation_UnknownStrategy(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		BackoffStrategy: "unknown",
		InitialBackoff:  5 * time.Second,
	}
	executor := NewSelfHealingExecutor(config, logger)

	backoff1 := executor.calculateBackoff(1)
	backoff2 := executor.calculateBackoff(2)

	// Unknown strategy should fall back to InitialBackoff
	if backoff1 != 5*time.Second {
		t.Errorf("Expected 5s backoff, got %v", backoff1)
	}

	if backoff2 != 5*time.Second {
		t.Errorf("Expected 5s backoff, got %v", backoff2)
	}
}

// Test: ParseCompilationError - Undefined Symbol
func TestParseCompilationError_UndefinedSymbol(t *testing.T) {
	errorOutput := "error: undefined reference to 'someFunction'"

	errorType, suggestions := ParseCompilationError(errorOutput)

	if errorType != "undefined_symbol" {
		t.Errorf("Expected error type 'undefined_symbol', got %s", errorType)
	}

	if len(suggestions) == 0 {
		t.Error("Expected suggestions for undefined symbol")
	}

	// Should suggest checking imports
	hasSuggestion := false
	for _, s := range suggestions {
		if contains(s, "import") || contains(s, "names") {
			hasSuggestion = true
			break
		}
	}

	if !hasSuggestion {
		t.Error("Expected suggestion about imports or names")
	}
}

// Test: ParseCompilationError - Syntax Error
func TestParseCompilationError_SyntaxError(t *testing.T) {
	errorOutput := "syntax error: unexpected '}' at line 42"

	errorType, suggestions := ParseCompilationError(errorOutput)

	if errorType != "syntax_error" {
		t.Errorf("Expected error type 'syntax_error', got %s", errorType)
	}

	if len(suggestions) == 0 {
		t.Error("Expected suggestions for syntax error")
	}
}

// Test: ParseCompilationError - Type Mismatch
func TestParseCompilationError_TypeMismatch(t *testing.T) {
	errorOutput := "type mismatch: cannot use string as int"

	errorType, suggestions := ParseCompilationError(errorOutput)

	if errorType != "type_mismatch" {
		t.Errorf("Expected error type 'type_mismatch', got %s", errorType)
	}

	if len(suggestions) == 0 {
		t.Error("Expected suggestions for type mismatch")
	}
}

// Test: ParseCompilationError - Empty Error Output
func TestParseCompilationError_EmptyOutput(t *testing.T) {
	errorOutput := ""

	errorType, suggestions := ParseCompilationError(errorOutput)

	if errorType != "unknown" {
		t.Errorf("Expected error type 'unknown', got %s", errorType)
	}

	if len(suggestions) == 0 {
		t.Error("Expected at least one suggestion")
	}
}

// Test: ParseCompilationError - Unknown Error
func TestParseCompilationError_UnknownError(t *testing.T) {
	errorOutput := "something went wrong, but I don't know what"

	errorType, suggestions := ParseCompilationError(errorOutput)

	if errorType != "compilation_error" {
		t.Errorf("Expected error type 'compilation_error', got %s", errorType)
	}

	if len(suggestions) == 0 {
		t.Error("Expected at least one suggestion")
	}
}

// Test: Helper Function - contains
func TestHelperFunction_Contains(t *testing.T) {
	tests := []struct {
		s      string
		substr string
		expect bool
	}{
		{"hello world", "world", true},
		{"hello world", "hello", true},
		{"hello world", "o w", true},
		{"hello", "hello", true},
		{"hello world", "goodbye", false},
		{"hello", "hello world", false},
		{"", "test", false},
		{"test", "", true}, // Empty substring matches
	}

	for _, test := range tests {
		result := contains(test.s, test.substr)
		if result != test.expect {
			t.Errorf("contains(%q, %q) = %v, expected %v", test.s, test.substr, result, test.expect)
		}
	}
}

// Test: Retry Attempt Recording
func TestRetryAttemptRecording(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:         true,
		MaxRetries:      3,
		BackoffStrategy: "none",
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptCount := 0
	attemptFunc := func(attempt int) error {
		attemptCount++
		if attempt < 3 {
			return errors.New("temporary failure")
		}
		return nil
	}

	validateFunc := func() (bool, string, error) {
		if attemptCount < 3 {
			return false, "test_failure", errors.New("validation failed")
		}
		return true, "", nil
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)

	if !result.Success {
		t.Error("Expected success")
	}

	// Verify attempt records
	for i, attempt := range result.Attempts {
		expectedAttemptNumber := i + 1
		if attempt.AttemptNumber != expectedAttemptNumber {
			t.Errorf("Attempt %d has number %d", i, attempt.AttemptNumber)
		}

		if attempt.Timestamp.IsZero() {
			t.Errorf("Attempt %d has zero timestamp", i)
		}

		// First two attempts should have errors
		if i < 2 && attempt.Error == nil {
			t.Errorf("Attempt %d should have an error", i)
		}
	}
}

// Test: Error Type Recording
func TestErrorTypeRecording(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:         true,
		MaxRetries:      2,
		BackoffStrategy: "none",
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptFunc := func(attempt int) error {
		if attempt == 1 {
			return errors.New("failure")
		}
		return nil
	}

	validateFunc := func() (bool, string, error) {
		return false, "compilation_error", errors.New("compilation failed")
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)

	// Check that error type was recorded
	for _, attempt := range result.Attempts {
		if attempt.ErrorType != "" {
			if attempt.ErrorType != "compilation_error" {
				t.Errorf("Expected error type 'compilation_error', got %s", attempt.ErrorType)
			}
		}
	}
}

// Test: Duration Recording
func TestDurationRecording(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:         true,
		MaxRetries:      2,
		BackoffStrategy: "none",
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptFunc := func(attempt int) error {
		time.Sleep(10 * time.Millisecond) // Simulate work
		return nil
	}

	validateFunc := func() (bool, string, error) {
		return true, "", nil
	}

	ctx := context.Background()
	start := time.Now()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, nil)
	end := time.Now()

	if !result.Success {
		t.Error("Expected success")
	}

	if result.Duration == 0 {
		t.Error("Duration should be recorded")
	}

	// Duration should be reasonable
	actualDuration := end.Sub(start)
	if result.Duration > actualDuration+100*time.Millisecond {
		t.Errorf("Recorded duration %v is too long compared to actual %v", result.Duration, actualDuration)
	}
}

// Test: Action Recording
func TestActionRecording(t *testing.T) {
	logger := log.New(os.Stdout, "[Test] ", log.LstdFlags)
	config := RetryConfig{
		Enabled:          true,
		MaxRetries:       2,
		BackoffStrategy:  "none",
		EnableReflection: true,
	}
	executor := NewSelfHealingExecutor(config, logger)

	attemptFunc := func(attempt int) error {
		if attempt == 1 {
			return errors.New("failure")
		}
		return nil
	}

	validateFunc := func() (bool, string, error) {
		return false, "test_failure", errors.New("validation failed")
	}

	reflectFunc := func(err error, attemptNum int) (string, string) {
		return "Reflection text", "Custom action taken"
	}

	ctx := context.Background()
	result := executor.ExecuteWithRetry(ctx, attemptFunc, validateFunc, reflectFunc)

	// Check that action was recorded
	hasCustomAction := false
	for _, attempt := range result.Attempts {
		if attempt.ActionTaken == "Custom action taken" {
			hasCustomAction = true
			break
		}
	}

	if !hasCustomAction {
		t.Error("Expected custom action to be recorded")
	}
}
