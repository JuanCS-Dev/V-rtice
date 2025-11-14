package httpclient

import (
	"context"
	"math"
	"time"

	"github.com/verticedev/vcli-go/internal/errors"
)

// RetryConfig defines retry behavior
type RetryConfig struct {
	MaxAttempts  int           // Maximum number of attempts (including initial)
	InitialDelay time.Duration // Initial backoff delay
	MaxDelay     time.Duration // Maximum backoff delay
	Multiplier   float64       // Backoff multiplier
}

// DefaultRetryConfig returns conservative defaults
func DefaultRetryConfig() RetryConfig {
	return RetryConfig{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Second,
		MaxDelay:     10 * time.Second,
		Multiplier:   2.0,
	}
}

// Retrier handles retry logic with exponential backoff
type Retrier struct {
	config RetryConfig
}

// NewRetrier creates a new retrier
func NewRetrier(config RetryConfig) *Retrier {
	return &Retrier{config: config}
}

// Do executes an operation with retries
func (r *Retrier) Do(ctx context.Context, operation func() error) error {
	var lastErr error

	for attempt := 0; attempt < r.config.MaxAttempts; attempt++ {
		// Check context before attempting
		select {
		case <-ctx.Done():
			return errors.Wrap(ctx.Err(), errors.ErrorTypeTimeout, "context cancelled")
		default:
		}

		// Execute operation
		err := operation()
		if err == nil {
			return nil // Success
		}

		lastErr = err

		// Don't retry non-retryable errors
		if !errors.IsRetryable(err) {
			return err
		}

		// Don't retry on last attempt
		if attempt == r.config.MaxAttempts-1 {
			break
		}

		// Calculate backoff delay
		delay := r.calculateBackoff(attempt)

		// Wait with context
		select {
		case <-ctx.Done():
			return errors.Wrap(ctx.Err(), errors.ErrorTypeTimeout, "context cancelled during backoff")
		case <-time.After(delay):
			// Continue to next attempt
		}
	}

	return lastErr
}

// calculateBackoff calculates exponential backoff delay
func (r *Retrier) calculateBackoff(attempt int) time.Duration {
	// Exponential backoff: delay = initial * (multiplier ^ attempt)
	delay := float64(r.config.InitialDelay) * math.Pow(r.config.Multiplier, float64(attempt))

	// Cap at max delay
	if delay > float64(r.config.MaxDelay) {
		delay = float64(r.config.MaxDelay)
	}

	return time.Duration(delay)
}

// DoWithResult executes an operation that returns a result
func (r *Retrier) DoWithResult(ctx context.Context, operation func() (interface{}, error)) (interface{}, error) {
	var result interface{}
	var lastErr error

	for attempt := 0; attempt < r.config.MaxAttempts; attempt++ {
		select {
		case <-ctx.Done():
			return nil, errors.Wrap(ctx.Err(), errors.ErrorTypeTimeout, "context cancelled")
		default:
		}

		res, err := operation()
		if err == nil {
			return res, nil
		}

		lastErr = err
		result = res

		if !errors.IsRetryable(err) {
			return result, err
		}

		if attempt == r.config.MaxAttempts-1 {
			break
		}

		delay := r.calculateBackoff(attempt)
		select {
		case <-ctx.Done():
			return result, errors.Wrap(ctx.Err(), errors.ErrorTypeTimeout, "context cancelled during backoff")
		case <-time.After(delay):
		}
	}

	return result, lastErr
}
