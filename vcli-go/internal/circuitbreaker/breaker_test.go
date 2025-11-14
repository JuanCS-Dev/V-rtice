package circuitbreaker

import (
	"context"
	"errors"
	"testing"
	"time"
)

// TestNew tests the circuit breaker constructor
func TestNew(t *testing.T) {
	config := &Config{
		MaxFailures:  5,
		ResetTimeout: 10 * time.Second,
	}

	cb := New(config)

	if cb == nil {
		t.Fatal("New() returned nil")
	}
	if cb.state != StateClosed {
		t.Errorf("state = %v, want %v", cb.state, StateClosed)
	}
	if cb.failures != 0 {
		t.Errorf("failures = %d, want 0", cb.failures)
	}
}

// TestNewWithDefaults tests constructor with nil config
func TestNewWithDefaults(t *testing.T) {
	cb := New(nil)

	if cb == nil {
		t.Fatal("New(nil) returned nil")
	}
	if cb.config.MaxFailures != 5 {
		t.Errorf("MaxFailures = %d, want 5", cb.config.MaxFailures)
	}
	if cb.config.ResetTimeout != 30*time.Second {
		t.Errorf("ResetTimeout = %v, want 30s", cb.config.ResetTimeout)
	}
}

// TestExecute_Success tests successful execution
func TestExecute_Success(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		ResetTimeout: 1 * time.Second,
	})

	callCount := 0
	fn := func() error {
		callCount++
		return nil
	}

	err := cb.Execute(context.Background(), fn)

	if err != nil {
		t.Errorf("Execute() returned error: %v", err)
	}
	if callCount != 1 {
		t.Errorf("Function called %d times, want 1", callCount)
	}
	if cb.State() != StateClosed {
		t.Errorf("state = %v, want %v", cb.State(), StateClosed)
	}
	if cb.Failures() != 0 {
		t.Errorf("failures = %d, want 0", cb.Failures())
	}
}

// TestExecute_Failure tests failure handling
func TestExecute_Failure(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		ResetTimeout: 1 * time.Second,
	})

	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	err := cb.Execute(context.Background(), fn)

	if err != testErr {
		t.Errorf("Execute() = %v, want %v", err, testErr)
	}
	if cb.State() != StateClosed {
		t.Errorf("state = %v, want %v (first failure)", cb.State(), StateClosed)
	}
	if cb.Failures() != 1 {
		t.Errorf("failures = %d, want 1", cb.Failures())
	}
}

// TestExecute_OpenCircuit tests circuit opening after max failures
func TestExecute_OpenCircuit(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		Timeout:      1 * time.Second,
		ResetTimeout: 100 * time.Millisecond,
	})

	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	// Fail 3 times to open circuit
	for i := 0; i < 3; i++ {
		cb.Execute(context.Background(), fn)
	}

	if cb.State() != StateOpen {
		t.Errorf("state = %v, want %v after %d failures", cb.State(), StateOpen, 3)
	}

	// Next call should fail immediately when circuit is open
	successFn := func() error {
		return nil
	}

	err := cb.Execute(context.Background(), successFn)

	if err == nil {
		t.Error("Execute() should fail when circuit is open")
	}
}

// TestExecute_HalfOpen tests half-open state transition
func TestExecute_HalfOpen(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  2,
		Timeout:      50 * time.Millisecond,
		ResetTimeout: 50 * time.Millisecond,
	})

	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	// Open the circuit
	cb.Execute(context.Background(), fn)
	cb.Execute(context.Background(), fn)

	if cb.State() != StateOpen {
		t.Fatalf("Circuit should be open, got %v", cb.State())
	}

	// Wait for reset timeout
	time.Sleep(60 * time.Millisecond)

	// Next call should transition to half-open
	successFn := func() error {
		return nil
	}

	err := cb.Execute(context.Background(), successFn)

	if err != nil {
		t.Errorf("Execute() in half-open state returned error: %v", err)
	}

	// Should transition back to closed after success
	if cb.State() != StateClosed {
		t.Errorf("state = %v, want %v after success in half-open", cb.State(), StateClosed)
	}
	if cb.Failures() != 0 {
		t.Errorf("failures = %d, want 0 after successful recovery", cb.Failures())
	}
}

// TestExecute_HalfOpenFailure tests failure in half-open state
func TestExecute_HalfOpenFailure(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  2,
		Timeout:      50 * time.Millisecond,
		ResetTimeout: 50 * time.Millisecond,
	})

	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	// Open the circuit
	cb.Execute(context.Background(), fn)
	cb.Execute(context.Background(), fn)

	// Wait for reset timeout
	time.Sleep(60 * time.Millisecond)

	// Fail in half-open state - should go back to open
	err := cb.Execute(context.Background(), fn)

	if err != testErr {
		t.Errorf("Execute() = %v, want %v", err, testErr)
	}

	// Should be back in open state
	if cb.State() != StateOpen {
		t.Errorf("state = %v, want %v after failure in half-open", cb.State(), StateOpen)
	}
}

// TestExecuteWithResult_Success tests successful execution with result
func TestExecuteWithResult_Success(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		ResetTimeout: 1 * time.Second,
	})

	fn := func() (string, error) {
		return "success", nil
	}

	result, err := ExecuteWithResult(context.Background(), cb, fn)

	if err != nil {
		t.Errorf("ExecuteWithResult() returned error: %v", err)
	}
	if result != "success" {
		t.Errorf("result = %q, want %q", result, "success")
	}
	if cb.Failures() != 0 {
		t.Errorf("failures = %d, want 0", cb.Failures())
	}
}

// TestExecuteWithResult_Failure tests failure handling with result
func TestExecuteWithResult_Failure(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		ResetTimeout: 1 * time.Second,
	})

	testErr := errors.New("test error")
	fn := func() (int, error) {
		return 0, testErr
	}

	result, err := ExecuteWithResult(context.Background(), cb, fn)

	if err != testErr {
		t.Errorf("ExecuteWithResult() = %v, want %v", err, testErr)
	}
	if result != 0 {
		t.Errorf("result = %d, want zero value", result)
	}
	if cb.Failures() != 1 {
		t.Errorf("failures = %d, want 1", cb.Failures())
	}
}

// TestExecuteWithResult_OpenCircuit tests circuit open behavior
func TestExecuteWithResult_OpenCircuit(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  2,
		ResetTimeout: 1 * time.Second,
	})

	testErr := errors.New("test error")
	fn := func() (bool, error) {
		return false, testErr
	}

	// Open the circuit
	ExecuteWithResult(context.Background(), cb, fn)
	ExecuteWithResult(context.Background(), cb, fn)

	if cb.State() != StateOpen {
		t.Fatalf("Circuit should be open")
	}

	// Should fail immediately
	result, err := ExecuteWithResult(context.Background(), cb, fn)

	if err == nil {
		t.Error("ExecuteWithResult() should fail when circuit is open")
	}
	if result != false {
		t.Errorf("result should be zero value, got %v", result)
	}
}

// TestReset tests resetting the circuit breaker
func TestReset(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  2,
		ResetTimeout: 1 * time.Second,
	})

	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	// Open the circuit
	cb.Execute(context.Background(), fn)
	cb.Execute(context.Background(), fn)

	if cb.State() != StateOpen {
		t.Fatalf("Circuit should be open")
	}
	if cb.Failures() != 2 {
		t.Fatalf("Should have 2 failures")
	}

	// Reset
	cb.Reset()

	if cb.State() != StateClosed {
		t.Errorf("state = %v, want %v after reset", cb.State(), StateClosed)
	}
	if cb.Failures() != 0 {
		t.Errorf("failures = %d, want 0 after reset", cb.Failures())
	}

	// Should work normally after reset
	successFn := func() error {
		return nil
	}

	err := cb.Execute(context.Background(), successFn)
	if err != nil {
		t.Errorf("Execute() after reset returned error: %v", err)
	}
}

// TestState tests the State() method
func TestState(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  2,
		ResetTimeout: 1 * time.Second,
	})

	if cb.State() != StateClosed {
		t.Errorf("Initial state = %v, want %v", cb.State(), StateClosed)
	}

	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	// Open circuit
	cb.Execute(context.Background(), fn)
	cb.Execute(context.Background(), fn)

	if cb.State() != StateOpen {
		t.Errorf("State after failures = %v, want %v", cb.State(), StateOpen)
	}
}

// TestFailures tests the Failures() method
func TestFailures(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  5,
		ResetTimeout: 1 * time.Second,
	})

	if cb.Failures() != 0 {
		t.Errorf("Initial failures = %d, want 0", cb.Failures())
	}

	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	for i := 1; i <= 3; i++ {
		cb.Execute(context.Background(), fn)
		if cb.Failures() != i {
			t.Errorf("After %d failure(s), Failures() = %d, want %d", i, cb.Failures(), i)
		}
	}
}

// TestStats tests the Stats() method
func TestStats(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		ResetTimeout: 1 * time.Second,
	})

	stats := cb.Stats()

	if stats.State != StateClosed {
		t.Errorf("Stats.State = %v, want %v", stats.State, StateClosed)
	}
	if stats.Failures != 0 {
		t.Errorf("Stats.Failures = %d, want 0", stats.Failures)
	}

	// Add some failures
	testErr := errors.New("test error")
	fn := func() error {
		return testErr
	}

	cb.Execute(context.Background(), fn)
	cb.Execute(context.Background(), fn)

	stats = cb.Stats()

	if stats.Failures != 2 {
		t.Errorf("Stats.Failures = %d, want 2", stats.Failures)
	}
	if stats.LastFailTime.IsZero() {
		t.Error("Stats.LastFailTime should not be zero")
	}
	if stats.LastStateTime.IsZero() {
		t.Error("Stats.LastStateTime should not be zero")
	}
}

// TestConcurrentExecute tests thread safety
func TestConcurrentExecute(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  10,
		ResetTimeout: 1 * time.Second,
	})

	successCount := 0
	done := make(chan bool)

	fn := func() error {
		return nil
	}

	// Run 100 concurrent executions
	for i := 0; i < 100; i++ {
		go func() {
			err := cb.Execute(context.Background(), fn)
			if err == nil {
				successCount++
			}
			done <- true
		}()
	}

	// Wait for all goroutines
	for i := 0; i < 100; i++ {
		<-done
	}

	// Should still be closed
	if cb.State() != StateClosed {
		t.Errorf("state = %v, want %v after concurrent successes", cb.State(), StateClosed)
	}
}

// TestContextCancellation tests context cancellation handling
func TestContextCancellation(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		ResetTimeout: 1 * time.Second,
	})

	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	fn := func() error {
		<-ctx.Done()
		return ctx.Err()
	}

	err := cb.Execute(ctx, fn)

	if err != context.Canceled {
		t.Errorf("Execute() = %v, want %v", err, context.Canceled)
	}

	// Context cancellation should count as failure
	if cb.Failures() != 1 {
		t.Errorf("failures = %d, want 1 (context errors count as failures)", cb.Failures())
	}
}

// TestStateTransitions tests all state transitions
func TestStateTransitions(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  2,
		Timeout:      50 * time.Millisecond,
		ResetTimeout: 50 * time.Millisecond,
	})

	testErr := errors.New("test error")
	failFn := func() error {
		return testErr
	}
	successFn := func() error {
		return nil
	}

	// Start: Closed
	if cb.State() != StateClosed {
		t.Fatalf("Should start in Closed state")
	}

	// Closed -> Closed (failure but not enough)
	cb.Execute(context.Background(), failFn)
	if cb.State() != StateClosed {
		t.Errorf("Should remain Closed after 1 failure")
	}

	// Closed -> Open (max failures reached)
	cb.Execute(context.Background(), failFn)
	if cb.State() != StateOpen {
		t.Errorf("Should transition to Open after max failures")
	}

	// Open -> Open (still in timeout)
	err := cb.Execute(context.Background(), successFn)
	if err == nil {
		t.Error("Should fail in Open state")
	}
	if cb.State() != StateOpen {
		t.Errorf("Should remain Open during timeout")
	}

	// Wait for reset timeout
	time.Sleep(60 * time.Millisecond)

	// Open -> HalfOpen -> Closed (success)
	err = cb.Execute(context.Background(), successFn)
	if err != nil {
		t.Errorf("Should succeed in HalfOpen state")
	}
	if cb.State() != StateClosed {
		t.Errorf("Should transition to Closed after success in HalfOpen")
	}

	// Open circuit again
	cb.Execute(context.Background(), failFn)
	cb.Execute(context.Background(), failFn)
	time.Sleep(60 * time.Millisecond)

	// Open -> HalfOpen -> Open (failure)
	err = cb.Execute(context.Background(), failFn)
	if err != testErr {
		t.Errorf("Should fail in HalfOpen state")
	}
	if cb.State() != StateOpen {
		t.Errorf("Should transition back to Open after failure in HalfOpen")
	}
}

// TestConfig_Defaults tests default configuration values
func TestConfig_Defaults(t *testing.T) {
	cb := New(nil)

	if cb.config.MaxFailures != 5 {
		t.Errorf("Default MaxFailures = %d, want 5", cb.config.MaxFailures)
	}
	if cb.config.ResetTimeout != 30*time.Second {
		t.Errorf("Default ResetTimeout = %v, want 30s", cb.config.ResetTimeout)
	}
}

// TestSuccessResetsFailureCount tests that success resets failure count
func TestSuccessResetsFailureCount(t *testing.T) {
	cb := New(&Config{
		MaxFailures:  3,
		ResetTimeout: 1 * time.Second,
	})

	testErr := errors.New("test error")
	failFn := func() error {
		return testErr
	}
	successFn := func() error {
		return nil
	}

	// Fail twice
	cb.Execute(context.Background(), failFn)
	cb.Execute(context.Background(), failFn)

	if cb.Failures() != 2 {
		t.Fatalf("Should have 2 failures")
	}

	// Success should reset
	cb.Execute(context.Background(), successFn)

	if cb.Failures() != 0 {
		t.Errorf("failures = %d, want 0 after success", cb.Failures())
	}
}
