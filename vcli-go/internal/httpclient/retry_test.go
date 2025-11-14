package httpclient

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/errors"
)

// TestDefaultRetryConfig verifies default retry configuration
func TestDefaultRetryConfig(t *testing.T) {
	config := DefaultRetryConfig()

	assert.Equal(t, 3, config.MaxAttempts)
	assert.Equal(t, 1*time.Second, config.InitialDelay)
	assert.Equal(t, 10*time.Second, config.MaxDelay)
	assert.Equal(t, 2.0, config.Multiplier)
}

// TestNewRetrier verifies retrier creation
func TestNewRetrier(t *testing.T) {
	config := RetryConfig{
		MaxAttempts:  5,
		InitialDelay: 500 * time.Millisecond,
		MaxDelay:     5 * time.Second,
		Multiplier:   3.0,
	}

	retrier := NewRetrier(config)

	assert.NotNil(t, retrier)
	assert.Equal(t, 5, retrier.config.MaxAttempts)
	assert.Equal(t, 500*time.Millisecond, retrier.config.InitialDelay)
	assert.Equal(t, 3.0, retrier.config.Multiplier)
}

// TestRetrier_Do_Success verifies successful operation on first attempt
func TestRetrier_Do_Success(t *testing.T) {
	// GIVEN: Operation that succeeds immediately
	retrier := NewRetrier(DefaultRetryConfig())
	attempts := 0

	operation := func() error {
		attempts++
		return nil
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	err := retrier.Do(ctx, operation)

	// THEN: Succeeds on first attempt
	require.NoError(t, err)
	assert.Equal(t, 1, attempts, "Should only attempt once on success")
}

// TestRetrier_Do_RetryableError verifies retry on retryable errors
func TestRetrier_Do_RetryableError(t *testing.T) {
	// GIVEN: Operation that fails with retryable error
	config := RetryConfig{
		MaxAttempts:  3,
		InitialDelay: 10 * time.Millisecond,
		MaxDelay:     100 * time.Millisecond,
		Multiplier:   2.0,
	}
	retrier := NewRetrier(config)
	attempts := 0

	operation := func() error {
		attempts++
		return errors.NewTimeoutError("test-service", "timeout")
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	err := retrier.Do(ctx, operation)

	// THEN: Retries all 3 attempts
	require.Error(t, err)
	assert.Equal(t, 3, attempts, "Should retry MaxAttempts times")
	assert.Contains(t, err.Error(), "TIMEOUT")
}

// TestRetrier_Do_NonRetryableError verifies immediate failure on non-retryable errors
func TestRetrier_Do_NonRetryableError(t *testing.T) {
	// GIVEN: Operation that fails with non-retryable error (validation error)
	retrier := NewRetrier(DefaultRetryConfig())
	attempts := 0

	operation := func() error {
		attempts++
		return errors.NewValidationError("invalid input")
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	err := retrier.Do(ctx, operation)

	// THEN: Fails immediately without retry
	require.Error(t, err)
	assert.Equal(t, 1, attempts, "Should not retry non-retryable errors")
	assert.Contains(t, err.Error(), "VALIDATION")
}

// TestRetrier_Do_SuccessAfterRetries verifies eventual success
func TestRetrier_Do_SuccessAfterRetries(t *testing.T) {
	// GIVEN: Operation that succeeds on 3rd attempt
	config := RetryConfig{
		MaxAttempts:  5,
		InitialDelay: 10 * time.Millisecond,
		MaxDelay:     100 * time.Millisecond,
		Multiplier:   2.0,
	}
	retrier := NewRetrier(config)
	attempts := 0

	operation := func() error {
		attempts++
		if attempts < 3 {
			return errors.NewUnavailableError("test-service")
		}
		return nil
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	startTime := time.Now()
	err := retrier.Do(ctx, operation)
	duration := time.Since(startTime)

	// THEN: Succeeds on 3rd attempt after backoff delays
	require.NoError(t, err)
	assert.Equal(t, 3, attempts, "Should succeed on 3rd attempt")
	// First retry: 10ms, Second retry: 20ms = ~30ms total
	assert.Greater(t, duration, 25*time.Millisecond, "Should have backoff delays")
}

// TestRetrier_Do_ContextCancelled verifies context cancellation
func TestRetrier_Do_ContextCancelled(t *testing.T) {
	// GIVEN: Slow operation with cancelled context
	retrier := NewRetrier(DefaultRetryConfig())
	attempts := 0

	operation := func() error {
		attempts++
		return errors.NewUnavailableError("test-service")
	}

	// WHEN: Context is cancelled before retry
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	err := retrier.Do(ctx, operation)

	// THEN: Operation is cancelled
	require.Error(t, err)
	assert.Contains(t, err.Error(), "TIMEOUT")
	assert.Contains(t, err.Error(), "cancelled")
}

// TestRetrier_Do_ContextCancelledDuringBackoff verifies cancellation during backoff
func TestRetrier_Do_ContextCancelledDuringBackoff(t *testing.T) {
	// GIVEN: Operation that fails, with context cancelled during backoff
	config := RetryConfig{
		MaxAttempts:  5,
		InitialDelay: 200 * time.Millisecond, // Long delay
		MaxDelay:     1 * time.Second,
		Multiplier:   2.0,
	}
	retrier := NewRetrier(config)
	attempts := 0

	operation := func() error {
		attempts++
		return errors.NewUnavailableError("test-service")
	}

	// WHEN: Context is cancelled during backoff
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	err := retrier.Do(ctx, operation)

	// THEN: Cancellation error is returned
	require.Error(t, err)
	assert.Contains(t, err.Error(), "cancelled during backoff")
	assert.Equal(t, 1, attempts, "Should stop retrying when context cancelled")
}

// TestRetrier_DoWithResult_Success verifies successful operation with result
func TestRetrier_DoWithResult_Success(t *testing.T) {
	// GIVEN: Operation that returns result
	retrier := NewRetrier(DefaultRetryConfig())
	attempts := 0

	operation := func() (interface{}, error) {
		attempts++
		return "success result", nil
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	result, err := retrier.DoWithResult(ctx, operation)

	// THEN: Result is returned
	require.NoError(t, err)
	assert.Equal(t, "success result", result)
	assert.Equal(t, 1, attempts)
}

// TestRetrier_DoWithResult_RetryableError verifies retry with result
func TestRetrier_DoWithResult_RetryableError(t *testing.T) {
	// GIVEN: Operation that fails with retryable error
	config := RetryConfig{
		MaxAttempts:  3,
		InitialDelay: 10 * time.Millisecond,
		MaxDelay:     100 * time.Millisecond,
		Multiplier:   2.0,
	}
	retrier := NewRetrier(config)
	attempts := 0

	operation := func() (interface{}, error) {
		attempts++
		return nil, errors.NewTimeoutError("test-service", "timeout")
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	result, err := retrier.DoWithResult(ctx, operation)

	// THEN: All retries exhausted
	require.Error(t, err)
	assert.Nil(t, result)
	assert.Equal(t, 3, attempts)
}

// TestRetrier_DoWithResult_NonRetryableError verifies immediate failure
func TestRetrier_DoWithResult_NonRetryableError(t *testing.T) {
	// GIVEN: Operation that fails with non-retryable error
	retrier := NewRetrier(DefaultRetryConfig())
	attempts := 0

	operation := func() (interface{}, error) {
		attempts++
		return nil, errors.NewAuthError("test-service", "unauthorized")
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	result, err := retrier.DoWithResult(ctx, operation)

	// THEN: Fails immediately
	require.Error(t, err)
	assert.Nil(t, result)
	assert.Equal(t, 1, attempts, "Should not retry non-retryable errors")
	assert.Contains(t, err.Error(), "AUTH")
}

// TestRetrier_DoWithResult_SuccessAfterRetries verifies eventual success with result
func TestRetrier_DoWithResult_SuccessAfterRetries(t *testing.T) {
	// GIVEN: Operation that succeeds on 2nd attempt
	config := RetryConfig{
		MaxAttempts:  3,
		InitialDelay: 10 * time.Millisecond,
		MaxDelay:     100 * time.Millisecond,
		Multiplier:   2.0,
	}
	retrier := NewRetrier(config)
	attempts := 0

	operation := func() (interface{}, error) {
		attempts++
		if attempts < 2 {
			return nil, errors.Wrap(nil, errors.ErrorTypeNetwork, "network error")
		}
		return map[string]string{"data": "success"}, nil
	}

	// WHEN: Operation is executed
	ctx := context.Background()
	result, err := retrier.DoWithResult(ctx, operation)

	// THEN: Result is returned on 2nd attempt
	require.NoError(t, err)
	assert.Equal(t, 2, attempts)
	resultMap := result.(map[string]string)
	assert.Equal(t, "success", resultMap["data"])
}

// TestRetrier_DoWithResult_ContextCancelled verifies context cancellation
func TestRetrier_DoWithResult_ContextCancelled(t *testing.T) {
	// GIVEN: Operation with cancelled context
	retrier := NewRetrier(DefaultRetryConfig())

	operation := func() (interface{}, error) {
		return nil, errors.NewUnavailableError("test-service")
	}

	// WHEN: Context is already cancelled
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	result, err := retrier.DoWithResult(ctx, operation)

	// THEN: Context error is returned
	require.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "cancelled")
}

// TestRetrier_calculateBackoff verifies exponential backoff calculation
func TestRetrier_calculateBackoff(t *testing.T) {
	tests := []struct {
		name          string
		config        RetryConfig
		attempt       int
		expectedDelay time.Duration
	}{
		{
			name: "first retry (attempt 0)",
			config: RetryConfig{
				InitialDelay: 100 * time.Millisecond,
				MaxDelay:     10 * time.Second,
				Multiplier:   2.0,
			},
			attempt:       0,
			expectedDelay: 100 * time.Millisecond, // 100ms * 2^0
		},
		{
			name: "second retry (attempt 1)",
			config: RetryConfig{
				InitialDelay: 100 * time.Millisecond,
				MaxDelay:     10 * time.Second,
				Multiplier:   2.0,
			},
			attempt:       1,
			expectedDelay: 200 * time.Millisecond, // 100ms * 2^1
		},
		{
			name: "third retry (attempt 2)",
			config: RetryConfig{
				InitialDelay: 100 * time.Millisecond,
				MaxDelay:     10 * time.Second,
				Multiplier:   2.0,
			},
			attempt:       2,
			expectedDelay: 400 * time.Millisecond, // 100ms * 2^2
		},
		{
			name: "capped at max delay",
			config: RetryConfig{
				InitialDelay: 1 * time.Second,
				MaxDelay:     2 * time.Second,
				Multiplier:   2.0,
			},
			attempt:       3,
			expectedDelay: 2 * time.Second, // Would be 8s, but capped at 2s
		},
		{
			name: "multiplier 3.0",
			config: RetryConfig{
				InitialDelay: 100 * time.Millisecond,
				MaxDelay:     10 * time.Second,
				Multiplier:   3.0,
			},
			attempt:       2,
			expectedDelay: 900 * time.Millisecond, // 100ms * 3^2
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// GIVEN: Retrier with specific config
			retrier := NewRetrier(tt.config)

			// WHEN: Backoff is calculated
			delay := retrier.calculateBackoff(tt.attempt)

			// THEN: Delay matches expected value
			assert.Equal(t, tt.expectedDelay, delay)
		})
	}
}

// TestRetrier_Integration_RealTiming verifies actual backoff timing
func TestRetrier_Integration_RealTiming(t *testing.T) {
	// GIVEN: Retrier with precise delays
	config := RetryConfig{
		MaxAttempts:  3,
		InitialDelay: 50 * time.Millisecond,
		MaxDelay:     500 * time.Millisecond,
		Multiplier:   2.0,
	}
	retrier := NewRetrier(config)
	attempts := 0

	operation := func() error {
		attempts++
		return errors.NewUnavailableError("test-service")
	}

	// WHEN: Operation runs through all retries
	ctx := context.Background()
	startTime := time.Now()
	err := retrier.Do(ctx, operation)
	duration := time.Since(startTime)

	// THEN: Total duration includes backoff delays
	require.Error(t, err)
	assert.Equal(t, 3, attempts)
	// Expected delays: 50ms (after 1st attempt) + 100ms (after 2nd attempt) = 150ms
	assert.Greater(t, duration, 140*time.Millisecond, "Should have backoff delays")
	assert.Less(t, duration, 250*time.Millisecond, "Should not exceed expected delays significantly")
}
