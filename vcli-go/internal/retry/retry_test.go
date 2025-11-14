package retry

import (
	"context"
	"errors"
	"testing"
	"time"

	vcliErrors "github.com/verticedev/vcli-go/internal/errors"
)

// TestDefaultStrategy tests the default retry strategy
func TestDefaultStrategy(t *testing.T) {
	strategy := DefaultStrategy()

	if strategy.MaxAttempts != 3 {
		t.Errorf("MaxAttempts = %d, want 3", strategy.MaxAttempts)
	}
	if strategy.InitialDelay != 100*time.Millisecond {
		t.Errorf("InitialDelay = %v, want 100ms", strategy.InitialDelay)
	}
	if strategy.MaxDelay != 5*time.Second {
		t.Errorf("MaxDelay = %v, want 5s", strategy.MaxDelay)
	}
	if strategy.BackoffFactor != 2.0 {
		t.Errorf("BackoffFactor = %f, want 2.0", strategy.BackoffFactor)
	}
	if len(strategy.RetryableErrors) == 0 {
		t.Error("RetryableErrors should not be empty")
	}
}

// TestAggressiveStrategy tests the aggressive retry strategy
func TestAggressiveStrategy(t *testing.T) {
	strategy := AggressiveStrategy()

	if strategy.MaxAttempts != 5 {
		t.Errorf("MaxAttempts = %d, want 5", strategy.MaxAttempts)
	}
	if strategy.InitialDelay != 50*time.Millisecond {
		t.Errorf("InitialDelay = %v, want 50ms", strategy.InitialDelay)
	}
	if strategy.MaxDelay != 10*time.Second {
		t.Errorf("MaxDelay = %v, want 10s", strategy.MaxDelay)
	}
}

// TestConservativeStrategy tests the conservative retry strategy
func TestConservativeStrategy(t *testing.T) {
	strategy := ConservativeStrategy()

	if strategy.MaxAttempts != 2 {
		t.Errorf("MaxAttempts = %d, want 2", strategy.MaxAttempts)
	}
	if strategy.InitialDelay != 500*time.Millisecond {
		t.Errorf("InitialDelay = %v, want 500ms", strategy.InitialDelay)
	}
	if strategy.BackoffFactor != 1.5 {
		t.Errorf("BackoffFactor = %f, want 1.5", strategy.BackoffFactor)
	}
}

// TestDo_Success tests successful execution without retry
func TestDo_Success(t *testing.T) {
	strategy := DefaultStrategy()
	ctx := context.Background()

	callCount := 0
	fn := func() error {
		callCount++
		return nil // Success on first try
	}

	err := strategy.Do(ctx, fn)

	if err != nil {
		t.Errorf("Do() returned error: %v", err)
	}
	if callCount != 1 {
		t.Errorf("Function called %d times, want 1", callCount)
	}
}

// TestDo_RetryableError tests retry on retryable errors
func TestDo_RetryableError(t *testing.T) {
	strategy := &Strategy{
		MaxAttempts:   3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}
	ctx := context.Background()

	callCount := 0
	fn := func() error {
		callCount++
		if callCount < 3 {
			return vcliErrors.NewTimeoutError("test", "timeout")
		}
		return nil // Success on third try
	}

	err := strategy.Do(ctx, fn)

	if err != nil {
		t.Errorf("Do() returned error: %v", err)
	}
	if callCount != 3 {
		t.Errorf("Function called %d times, want 3", callCount)
	}
}

// TestDo_MaxAttemptsExceeded tests max attempts exceeded
func TestDo_MaxAttemptsExceeded(t *testing.T) {
	strategy := &Strategy{
		MaxAttempts:   2,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}
	ctx := context.Background()

	callCount := 0
	fn := func() error {
		callCount++
		return vcliErrors.NewTimeoutError("test", "timeout")
	}

	err := strategy.Do(ctx, fn)

	if err == nil {
		t.Error("Do() should return error when max attempts exceeded")
	}
	if callCount != 2 {
		t.Errorf("Function called %d times, want 2", callCount)
	}
	if err.Error() == "" {
		t.Error("Error message should not be empty")
	}
}

// TestDo_NonRetryableError tests that non-retryable errors are not retried
func TestDo_NonRetryableError(t *testing.T) {
	strategy := DefaultStrategy()
	ctx := context.Background()

	callCount := 0
	fn := func() error {
		callCount++
		return vcliErrors.NewAuthError("test", "auth failed")
	}

	err := strategy.Do(ctx, fn)

	if err == nil {
		t.Error("Do() should return error for non-retryable error")
	}
	if callCount != 1 {
		t.Errorf("Function called %d times, want 1 (no retry)", callCount)
	}
}

// TestDo_ContextCancellation tests context cancellation
func TestDo_ContextCancellation(t *testing.T) {
	strategy := &Strategy{
		MaxAttempts:   5,
		InitialDelay:  100 * time.Millisecond,
		MaxDelay:      1 * time.Second,
		BackoffFactor: 2.0,
	}

	ctx, cancel := context.WithCancel(context.Background())

	callCount := 0
	fn := func() error {
		callCount++
		if callCount == 2 {
			cancel() // Cancel after second attempt
		}
		return vcliErrors.NewTimeoutError("test", "timeout")
	}

	err := strategy.Do(ctx, fn)

	if err != context.Canceled {
		t.Errorf("Do() should return context.Canceled, got: %v", err)
	}
}

// TestDoWithResult_Success tests successful execution with result
func TestDoWithResult_Success(t *testing.T) {
	strategy := DefaultStrategy()
	ctx := context.Background()

	fn := func() (string, error) {
		return "success", nil
	}

	result, err := DoWithResult(ctx, strategy, fn)

	if err != nil {
		t.Errorf("DoWithResult() returned error: %v", err)
	}
	if result != "success" {
		t.Errorf("Result = %q, want %q", result, "success")
	}
}

// TestDoWithResult_Retry tests retry with result
func TestDoWithResult_Retry(t *testing.T) {
	strategy := &Strategy{
		MaxAttempts:   3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}
	ctx := context.Background()

	callCount := 0
	fn := func() (int, error) {
		callCount++
		if callCount < 2 {
			return 0, vcliErrors.NewTimeoutError("test", "timeout")
		}
		return 42, nil
	}

	result, err := DoWithResult(ctx, strategy, fn)

	if err != nil {
		t.Errorf("DoWithResult() returned error: %v", err)
	}
	if result != 42 {
		t.Errorf("Result = %d, want 42", result)
	}
	if callCount != 2 {
		t.Errorf("Function called %d times, want 2", callCount)
	}
}

// TestDoWithResult_MaxAttemptsExceeded tests max attempts with result
func TestDoWithResult_MaxAttemptsExceeded(t *testing.T) {
	strategy := &Strategy{
		MaxAttempts:   2,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}
	ctx := context.Background()

	fn := func() (string, error) {
		return "", vcliErrors.NewTimeoutError("test", "timeout")
	}

	result, err := DoWithResult(ctx, strategy, fn)

	if err == nil {
		t.Error("DoWithResult() should return error when max attempts exceeded")
	}
	if result != "" {
		t.Errorf("Result should be zero value, got %q", result)
	}
}

// TestDoWithCallback tests retry with callback
func TestDoWithCallback(t *testing.T) {
	strategy := &Strategy{
		MaxAttempts:   3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}
	ctx := context.Background()

	callCount := 0
	callbackCount := 0
	var attempts []Attempt

	fn := func() error {
		callCount++
		if callCount < 3 {
			return vcliErrors.NewTimeoutError("test", "timeout")
		}
		return nil
	}

	onRetry := func(attempt Attempt) {
		callbackCount++
		attempts = append(attempts, attempt)
	}

	err := strategy.DoWithCallback(ctx, fn, onRetry)

	if err != nil {
		t.Errorf("DoWithCallback() returned error: %v", err)
	}
	if callbackCount != 2 {
		t.Errorf("Callback called %d times, want 2", callbackCount)
	}
	if len(attempts) != 2 {
		t.Errorf("Captured %d attempts, want 2", len(attempts))
	}
	for i, attempt := range attempts {
		if attempt.Number != i+1 {
			t.Errorf("Attempt %d: Number = %d, want %d", i, attempt.Number, i+1)
		}
		if attempt.Error == nil {
			t.Errorf("Attempt %d: Error should not be nil", i)
		}
	}
}

// TestDoWithCallback_NilCallback tests nil callback handling
func TestDoWithCallback_NilCallback(t *testing.T) {
	strategy := DefaultStrategy()
	ctx := context.Background()

	fn := func() error {
		return nil
	}

	// Should not panic with nil callback
	err := strategy.DoWithCallback(ctx, fn, nil)

	if err != nil {
		t.Errorf("DoWithCallback() returned error: %v", err)
	}
}

// TestShouldRetry tests retry decision logic
func TestShouldRetry(t *testing.T) {
	strategy := DefaultStrategy()

	tests := []struct {
		name      string
		err       error
		attempt   int
		wantRetry bool
	}{
		{
			name:      "retryable error, first attempt",
			err:       vcliErrors.NewTimeoutError("test", "timeout"),
			attempt:   1,
			wantRetry: true,
		},
		{
			name:      "retryable error, last attempt",
			err:       vcliErrors.NewTimeoutError("test", "timeout"),
			attempt:   3,
			wantRetry: false,
		},
		{
			name:      "non-retryable error",
			err:       vcliErrors.NewAuthError("test", "auth failed"),
			attempt:   1,
			wantRetry: false,
		},
		{
			name:      "standard error",
			err:       errors.New("standard error"),
			attempt:   1,
			wantRetry: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := strategy.shouldRetry(tt.err, tt.attempt)
			if got != tt.wantRetry {
				t.Errorf("shouldRetry() = %v, want %v", got, tt.wantRetry)
			}
		})
	}
}

// TestCalculateDelay tests delay calculation with exponential backoff
func TestCalculateDelay(t *testing.T) {
	strategy := &Strategy{
		InitialDelay:  100 * time.Millisecond,
		MaxDelay:      1 * time.Second,
		BackoffFactor: 2.0,
	}

	tests := []struct {
		attempt int
		want    time.Duration
	}{
		{1, 100 * time.Millisecond},  // 100 * 2^0
		{2, 200 * time.Millisecond},  // 100 * 2^1
		{3, 400 * time.Millisecond},  // 100 * 2^2
		{4, 800 * time.Millisecond},  // 100 * 2^3
		{5, 1 * time.Second},         // 100 * 2^4 = 1600ms, capped at 1000ms
		{10, 1 * time.Second},        // Should be capped at MaxDelay
	}

	for _, tt := range tests {
		t.Run("", func(t *testing.T) {
			got := strategy.calculateDelay(tt.attempt)
			if got != tt.want {
				t.Errorf("calculateDelay(%d) = %v, want %v", tt.attempt, got, tt.want)
			}
		})
	}
}

// TestAttemptStruct tests the Attempt struct
func TestAttemptStruct(t *testing.T) {
	err := errors.New("test error")
	delay := 100 * time.Millisecond

	attempt := Attempt{
		Number: 1,
		Delay:  delay,
		Error:  err,
	}

	if attempt.Number != 1 {
		t.Errorf("Number = %d, want 1", attempt.Number)
	}
	if attempt.Delay != delay {
		t.Errorf("Delay = %v, want %v", attempt.Delay, delay)
	}
	if attempt.Error != err {
		t.Errorf("Error = %v, want %v", attempt.Error, err)
	}
}

// TestDo_StandardError tests behavior with standard errors
func TestDo_StandardError(t *testing.T) {
	strategy := DefaultStrategy()
	ctx := context.Background()

	stdErr := errors.New("standard error")
	fn := func() error {
		return stdErr
	}

	err := strategy.Do(ctx, fn)

	// Standard errors should not be retried
	if err != stdErr {
		t.Errorf("Do() = %v, want %v", err, stdErr)
	}
}
