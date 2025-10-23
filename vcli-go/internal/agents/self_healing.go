package agents

import (
	"context"
	"fmt"
	"log"
	"time"
)

// SelfHealingExecutor implements the self-healing retry loop pattern
// Based on Anthropic best practices and industry standards (2025)
type SelfHealingExecutor struct {
	config RetryConfig
	logger *log.Logger
}

// NewSelfHealingExecutor creates a new self-healing executor
func NewSelfHealingExecutor(config RetryConfig, logger *log.Logger) *SelfHealingExecutor {
	// Set defaults if not configured
	if config.MaxRetries == 0 {
		config.MaxRetries = 3
	}
	if config.BackoffStrategy == "" {
		config.BackoffStrategy = "exponential"
	}
	if config.InitialBackoff == 0 {
		config.InitialBackoff = 1 * time.Second
	}
	if config.MaxReflectionDepth == 0 {
		config.MaxReflectionDepth = 2
	}

	return &SelfHealingExecutor{
		config: config,
		logger: logger,
	}
}

// ExecuteWithRetry executes a function with retry logic and self-healing
// attemptFunc: Function to execute (should return error if failed)
// validateFunc: Function to validate result (compilation, tests, etc)
// reflectFunc: Function to reflect on error and suggest fix (optional, can be nil)
func (s *SelfHealingExecutor) ExecuteWithRetry(
	ctx context.Context,
	attemptFunc func(attempt int) error,
	validateFunc func() (bool, string, error),
	reflectFunc func(err error, attemptNum int) (string, string),
) *SelfHealingResult {

	if !s.config.Enabled {
		// Self-healing disabled, run once
		err := attemptFunc(1)
		return &SelfHealingResult{
			Success:       err == nil,
			TotalAttempts: 1,
			Attempts:      []RetryAttempt{{AttemptNumber: 1, Error: err, Timestamp: time.Now()}},
			FinalError:    err,
			Recovered:     false,
			Duration:      0,
		}
	}

	startTime := time.Now()
	result := &SelfHealingResult{
		Success:   false,
		Attempts:  make([]RetryAttempt, 0),
		Recovered: false,
	}

	for attempt := 1; attempt <= s.config.MaxRetries; attempt++ {
		s.logger.Printf("[Self-Healing] Attempt %d/%d", attempt, s.config.MaxRetries)

		// Execute attempt
		attemptStart := time.Now()
		err := attemptFunc(attempt)

		// Validate result
		valid, errorType, validationErr := validateFunc()

		// Track attempt
		attemptResult := RetryAttempt{
			AttemptNumber: attempt,
			Error:         err,
			ErrorType:     errorType,
			Timestamp:     attemptStart,
		}

		if err == nil && valid && validationErr == nil {
			// Success!
			attemptResult.ActionTaken = "Succeeded on attempt"
			result.Attempts = append(result.Attempts, attemptResult)
			result.Success = true
			result.Recovered = attempt > 1 // Recovered if not first attempt
			result.TotalAttempts = attempt
			result.Duration = time.Since(startTime)

			if result.Recovered {
				s.logger.Printf("[Self-Healing] ✅ Recovered after %d attempts", attempt)
			} else {
				s.logger.Printf("[Self-Healing] ✅ Succeeded on first attempt")
			}
			return result
		}

		// Failed - determine error
		actualError := err
		if actualError == nil {
			actualError = validationErr
		}
		attemptResult.Error = actualError

		// Reflection (if enabled and function provided)
		if s.config.EnableReflection && reflectFunc != nil && attempt < s.config.MaxRetries {
			s.logger.Printf("[Self-Healing] 🔍 Reflecting on error: %s", errorType)
			reflection, action := reflectFunc(actualError, attempt)
			attemptResult.Reflection = reflection
			attemptResult.ActionTaken = action

			s.logger.Printf("[Self-Healing] 💡 Reflection: %s", reflection)
			s.logger.Printf("[Self-Healing] 🔧 Action: %s", action)
		} else {
			attemptResult.ActionTaken = "Retry without reflection"
		}

		result.Attempts = append(result.Attempts, attemptResult)

		// Last attempt failed
		if attempt == s.config.MaxRetries {
			result.Success = false
			result.FinalError = actualError
			result.TotalAttempts = attempt
			result.Duration = time.Since(startTime)
			s.logger.Printf("[Self-Healing] ❌ Failed after %d attempts", attempt)
			return result
		}

		// Backoff before next retry
		backoffDuration := s.calculateBackoff(attempt)
		s.logger.Printf("[Self-Healing] ⏳ Backing off for %v before retry...", backoffDuration)

		select {
		case <-time.After(backoffDuration):
			// Continue to next attempt
		case <-ctx.Done():
			// Context cancelled
			result.Success = false
			result.FinalError = ctx.Err()
			result.TotalAttempts = attempt
			result.Duration = time.Since(startTime)
			return result
		}
	}

	// Should not reach here
	result.Success = false
	result.FinalError = fmt.Errorf("unexpected end of retry loop")
	result.Duration = time.Since(startTime)
	return result
}

// calculateBackoff calculates backoff duration based on strategy
func (s *SelfHealingExecutor) calculateBackoff(attempt int) time.Duration {
	switch s.config.BackoffStrategy {
	case "none":
		return 0
	case "linear":
		return s.config.InitialBackoff * time.Duration(attempt)
	case "exponential":
		// 1s, 2s, 4s, 8s, ...
		multiplier := 1 << (attempt - 1) // 2^(attempt-1)
		return s.config.InitialBackoff * time.Duration(multiplier)
	default:
		return s.config.InitialBackoff
	}
}

// ParseCompilationError parses compilation error to extract actionable information
func ParseCompilationError(errorOutput string) (errorType string, suggestions []string) {
	// Simplified parser - real implementation would be more sophisticated
	if errorOutput == "" {
		return "unknown", []string{"No error output available"}
	}

	// Common patterns
	if contains(errorOutput, "undefined") {
		return "undefined_symbol", []string{
			"Check for missing imports",
			"Verify variable/function names",
			"Check for typos",
		}
	}

	if contains(errorOutput, "syntax error") {
		return "syntax_error", []string{
			"Check for missing brackets/parentheses",
			"Verify proper indentation",
			"Check for missing semicolons (if applicable)",
		}
	}

	if contains(errorOutput, "type") && contains(errorOutput, "mismatch") {
		return "type_mismatch", []string{
			"Check type compatibility",
			"Add type conversion if needed",
			"Verify function signatures",
		}
	}

	return "compilation_error", []string{"Review compilation output for details"}
}

// contains is a simple helper for string matching
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && (
		s[:len(substr)] == substr ||
		s[len(s)-len(substr):] == substr ||
		findSubstring(s, substr)))
}

func findSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
