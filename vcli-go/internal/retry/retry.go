package retry

import (
	"context"
	"fmt"
	"math"
	"time"

	"github.com/verticedev/vcli-go/internal/errors"
)

// Strategy defines retry behavior
type Strategy struct {
	MaxAttempts     int
	InitialDelay    time.Duration
	MaxDelay        time.Duration
	BackoffFactor   float64
	RetryableErrors []errors.ErrorType
}

// DefaultStrategy returns a sensible default retry strategy
func DefaultStrategy() *Strategy {
	return &Strategy{
		MaxAttempts:   3,
		InitialDelay:  100 * time.Millisecond,
		MaxDelay:      5 * time.Second,
		BackoffFactor: 2.0,
		RetryableErrors: []errors.ErrorType{
			errors.ErrorTypeTimeout,
			errors.ErrorTypeNetwork,
			errors.ErrorTypeConnection,
			errors.ErrorTypeUnavailable,
		},
	}
}

// AggressiveStrategy returns a more aggressive retry strategy
func AggressiveStrategy() *Strategy {
	return &Strategy{
		MaxAttempts:   5,
		InitialDelay:  50 * time.Millisecond,
		MaxDelay:      10 * time.Second,
		BackoffFactor: 2.0,
		RetryableErrors: []errors.ErrorType{
			errors.ErrorTypeTimeout,
			errors.ErrorTypeNetwork,
			errors.ErrorTypeConnection,
			errors.ErrorTypeUnavailable,
		},
	}
}

// ConservativeStrategy returns a conservative retry strategy
func ConservativeStrategy() *Strategy {
	return &Strategy{
		MaxAttempts:   2,
		InitialDelay:  500 * time.Millisecond,
		MaxDelay:      3 * time.Second,
		BackoffFactor: 1.5,
		RetryableErrors: []errors.ErrorType{
			errors.ErrorTypeTimeout,
			errors.ErrorTypeNetwork,
		},
	}
}

// Do executes a function with retry logic
func (s *Strategy) Do(ctx context.Context, fn func() error) error {
	var lastErr error

	for attempt := 1; attempt <= s.MaxAttempts; attempt++ {
		// Execute the function
		err := fn()
		if err == nil {
			return nil // Success!
		}

		lastErr = err

		// Check if we should retry
		if !s.shouldRetry(err, attempt) {
			return err
		}

		// Calculate delay with exponential backoff
		delay := s.calculateDelay(attempt)

		// Wait or check for context cancellation
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(delay):
			// Continue to next attempt
		}
	}

	return fmt.Errorf("max retry attempts (%d) exceeded: %w", s.MaxAttempts, lastErr)
}

// DoWithResult executes a function with retry logic and returns a result
func DoWithResult[T any](ctx context.Context, strategy *Strategy, fn func() (T, error)) (T, error) {
	var result T
	var lastErr error

	for attempt := 1; attempt <= strategy.MaxAttempts; attempt++ {
		// Execute the function
		res, err := fn()
		if err == nil {
			return res, nil // Success!
		}

		lastErr = err

		// Check if we should retry
		if !strategy.shouldRetry(err, attempt) {
			return result, err
		}

		// Calculate delay with exponential backoff
		delay := strategy.calculateDelay(attempt)

		// Wait or check for context cancellation
		select {
		case <-ctx.Done():
			return result, ctx.Err()
		case <-time.After(delay):
			// Continue to next attempt
		}
	}

	return result, fmt.Errorf("max retry attempts (%d) exceeded: %w", strategy.MaxAttempts, lastErr)
}

// shouldRetry determines if an error should be retried
func (s *Strategy) shouldRetry(err error, attempt int) bool {
	// Don't retry if we've exhausted attempts
	if attempt >= s.MaxAttempts {
		return false
	}

	// Check if it's a VCLIError and if it's retryable
	if vcliErr, ok := err.(*errors.VCLIError); ok {
		return vcliErr.IsRetryable()
	}

	// For unknown errors, don't retry by default
	return false
}

// calculateDelay calculates the delay for a given attempt using exponential backoff
func (s *Strategy) calculateDelay(attempt int) time.Duration {
	// Calculate exponential backoff: initialDelay * (backoffFactor ^ (attempt - 1))
	delay := float64(s.InitialDelay) * math.Pow(s.BackoffFactor, float64(attempt-1))

	// Cap at max delay
	if delay > float64(s.MaxDelay) {
		delay = float64(s.MaxDelay)
	}

	return time.Duration(delay)
}

// Attempt represents a single retry attempt
type Attempt struct {
	Number int
	Delay  time.Duration
	Error  error
}

// OnRetry is a callback function called before each retry
type OnRetry func(attempt Attempt)

// DoWithCallback executes a function with retry logic and callbacks
func (s *Strategy) DoWithCallback(ctx context.Context, fn func() error, onRetry OnRetry) error {
	var lastErr error

	for attempt := 1; attempt <= s.MaxAttempts; attempt++ {
		// Execute the function
		err := fn()
		if err == nil {
			return nil // Success!
		}

		lastErr = err

		// Check if we should retry
		if !s.shouldRetry(err, attempt) {
			return err
		}

		// Calculate delay
		delay := s.calculateDelay(attempt)

		// Call retry callback
		if onRetry != nil {
			onRetry(Attempt{
				Number: attempt,
				Delay:  delay,
				Error:  err,
			})
		}

		// Wait or check for context cancellation
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(delay):
			// Continue to next attempt
		}
	}

	return fmt.Errorf("max retry attempts (%d) exceeded: %w", s.MaxAttempts, lastErr)
}
