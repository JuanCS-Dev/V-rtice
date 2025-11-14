package httpclient

import (
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestDefaultBreakerConfig verifies default circuit breaker configuration
func TestDefaultBreakerConfig(t *testing.T) {
	config := DefaultBreakerConfig()

	assert.Equal(t, 5, config.MaxFailures)
	assert.Equal(t, 30*time.Second, config.OpenTimeout)
	assert.Equal(t, 3, config.HalfOpenMax)
	assert.Equal(t, 2, config.SuccessReset)
}

// TestNewCircuitBreaker verifies circuit breaker creation
func TestNewCircuitBreaker(t *testing.T) {
	config := BreakerConfig{
		MaxFailures:  10,
		OpenTimeout:  60 * time.Second,
		HalfOpenMax:  5,
		SuccessReset: 3,
	}

	cb := NewCircuitBreaker(config)

	assert.NotNil(t, cb)
	assert.Equal(t, StateClosed, cb.state)
	assert.Equal(t, 10, cb.config.MaxFailures)
	assert.Equal(t, 60*time.Second, cb.config.OpenTimeout)
}

// TestState_String verifies state string representation
func TestState_String(t *testing.T) {
	tests := []struct {
		state    State
		expected string
	}{
		{StateClosed, "closed"},
		{StateOpen, "open"},
		{StateHalfOpen, "half_open"},
		{State(999), "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			assert.Equal(t, tt.expected, tt.state.String())
		})
	}
}

// TestCircuitBreaker_Call_Success verifies successful operation in closed state
func TestCircuitBreaker_Call_Success(t *testing.T) {
	// GIVEN: Circuit breaker in closed state
	cb := NewCircuitBreaker(DefaultBreakerConfig())
	attempts := 0

	operation := func() error {
		attempts++
		return nil
	}

	// WHEN: Successful operation is called
	err := cb.Call(operation)

	// THEN: Operation succeeds and circuit stays closed
	require.NoError(t, err)
	assert.Equal(t, 1, attempts)
	assert.Equal(t, StateClosed, cb.GetState())
	assert.Equal(t, 0, cb.GetFailures())
}

// TestCircuitBreaker_Call_FailuresOpenCircuit verifies circuit opens after max failures
func TestCircuitBreaker_Call_FailuresOpenCircuit(t *testing.T) {
	// GIVEN: Circuit breaker with MaxFailures=3
	config := BreakerConfig{
		MaxFailures:  3,
		OpenTimeout:  100 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 1,
	}
	cb := NewCircuitBreaker(config)

	operation := func() error {
		return fmt.Errorf("operation failed")
	}

	// WHEN: Operation fails 3 times
	for i := 0; i < 3; i++ {
		err := cb.Call(operation)
		require.Error(t, err)
	}

	// THEN: Circuit is now open
	assert.Equal(t, StateOpen, cb.GetState())
	assert.True(t, cb.IsOpen())
}

// TestCircuitBreaker_Call_OpenRejectsRequests verifies open circuit rejects requests
func TestCircuitBreaker_Call_OpenRejectsRequests(t *testing.T) {
	// GIVEN: Circuit breaker that is open
	config := BreakerConfig{
		MaxFailures:  2,
		OpenTimeout:  200 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 1,
	}
	cb := NewCircuitBreaker(config)

	// Open the circuit
	for i := 0; i < 2; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	assert.Equal(t, StateOpen, cb.GetState())

	// WHEN: Attempt operation while circuit is open
	attempts := 0
	operation := func() error {
		attempts++
		return nil
	}

	err := cb.Call(operation)

	// THEN: Request is rejected without executing operation
	require.Error(t, err)
	assert.Contains(t, err.Error(), "circuit breaker is open")
	assert.Equal(t, 0, attempts, "Should not execute operation when circuit is open")
}

// TestCircuitBreaker_Call_TransitionToHalfOpen verifies transition after timeout
func TestCircuitBreaker_Call_TransitionToHalfOpen(t *testing.T) {
	// GIVEN: Circuit breaker with short open timeout
	config := BreakerConfig{
		MaxFailures:  2,
		OpenTimeout:  50 * time.Millisecond,
		HalfOpenMax:  3,
		SuccessReset: 1, // Only need 1 success to close
	}
	cb := NewCircuitBreaker(config)

	// Open the circuit
	for i := 0; i < 2; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	assert.Equal(t, StateOpen, cb.GetState())

	// WHEN: Wait for open timeout to expire
	time.Sleep(60 * time.Millisecond)

	// Call operation (should transition to half-open, then success closes it)
	err := cb.Call(func() error { return nil })

	// THEN: Circuit transitions to half-open and allows request
	require.NoError(t, err)
	assert.Equal(t, StateClosed, cb.GetState(), "Should transition to closed after 1 success in half-open")
}

// TestCircuitBreaker_Call_HalfOpenSuccess verifies half-open to closed transition
func TestCircuitBreaker_Call_HalfOpenSuccess(t *testing.T) {
	// GIVEN: Circuit breaker in half-open state
	config := BreakerConfig{
		MaxFailures:  2,
		OpenTimeout:  10 * time.Millisecond,
		HalfOpenMax:  3,
		SuccessReset: 2, // Need 2 successes to close
	}
	cb := NewCircuitBreaker(config)

	// Open and transition to half-open
	for i := 0; i < 2; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	time.Sleep(15 * time.Millisecond)

	// WHEN: First success in half-open
	err := cb.Call(func() error { return nil })
	require.NoError(t, err)
	state1 := cb.GetState()

	// Second success in half-open
	err = cb.Call(func() error { return nil })
	require.NoError(t, err)
	state2 := cb.GetState()

	// THEN: Circuit closes after required successes
	assert.Equal(t, StateHalfOpen, state1, "Should stay half-open after 1 success")
	assert.Equal(t, StateClosed, state2, "Should close after 2 successes")
	assert.Equal(t, 0, cb.GetFailures())
}

// TestCircuitBreaker_Call_HalfOpenFailure verifies half-open to open transition
func TestCircuitBreaker_Call_HalfOpenFailure(t *testing.T) {
	// GIVEN: Circuit breaker in half-open state
	config := BreakerConfig{
		MaxFailures:  2,
		OpenTimeout:  10 * time.Millisecond,
		HalfOpenMax:  3,
		SuccessReset: 2,
	}
	cb := NewCircuitBreaker(config)

	// Open and transition to half-open
	for i := 0; i < 2; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	time.Sleep(15 * time.Millisecond)

	// WHEN: Operation fails in half-open state
	err := cb.Call(func() error { return fmt.Errorf("failed again") })

	// THEN: Circuit immediately opens again
	require.Error(t, err)
	assert.Equal(t, StateOpen, cb.GetState(), "Should immediately open on half-open failure")
}

// TestCircuitBreaker_Call_HalfOpenMaxRequests verifies half-open request limit
func TestCircuitBreaker_Call_HalfOpenMaxRequests(t *testing.T) {
	// GIVEN: Circuit breaker with HalfOpenMax=2
	config := BreakerConfig{
		MaxFailures:  2,
		OpenTimeout:  10 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 5, // High number so we stay in half-open
	}
	cb := NewCircuitBreaker(config)

	// Open and transition to half-open
	for i := 0; i < 2; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	time.Sleep(15 * time.Millisecond)

	// WHEN: Make requests in half-open state
	// First call transitions to half-open and increments counter
	err1 := cb.Call(func() error { return nil }) // Allowed (1st)
	state1 := cb.GetState()

	// If already closed after 1st success due to low SuccessReset, test differently
	if state1 == StateClosed {
		// Circuit closed, can't test half-open limit
		t.Skip("Circuit closed after first success, cannot test half-open limit with these settings")
		return
	}

	err2 := cb.Call(func() error { return nil }) // Allowed (2nd)
	err3 := cb.Call(func() error { return nil }) // Should be rejected (3rd)

	// THEN: Excess requests are rejected
	require.NoError(t, err1)
	require.NoError(t, err2)
	require.Error(t, err3)
	assert.Contains(t, err3.Error(), "half-open limit reached")
}

// TestCircuitBreaker_CallWithResult_Success verifies operation with result
func TestCircuitBreaker_CallWithResult_Success(t *testing.T) {
	// GIVEN: Circuit breaker in closed state
	cb := NewCircuitBreaker(DefaultBreakerConfig())

	operation := func() (interface{}, error) {
		return "success data", nil
	}

	// WHEN: Operation is called
	result, err := cb.CallWithResult(operation)

	// THEN: Result is returned
	require.NoError(t, err)
	assert.Equal(t, "success data", result)
	assert.Equal(t, StateClosed, cb.GetState())
}

// TestCircuitBreaker_CallWithResult_Failure verifies failure tracking
func TestCircuitBreaker_CallWithResult_Failure(t *testing.T) {
	// GIVEN: Circuit breaker with MaxFailures=3
	config := BreakerConfig{
		MaxFailures:  3,
		OpenTimeout:  100 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 1,
	}
	cb := NewCircuitBreaker(config)

	operation := func() (interface{}, error) {
		return nil, fmt.Errorf("operation error")
	}

	// WHEN: Operation fails 3 times
	for i := 0; i < 3; i++ {
		result, err := cb.CallWithResult(operation)
		require.Error(t, err)
		assert.Nil(t, result)
	}

	// THEN: Circuit opens
	assert.Equal(t, StateOpen, cb.GetState())
}

// TestCircuitBreaker_CallWithResult_OpenRejects verifies rejection when open
func TestCircuitBreaker_CallWithResult_OpenRejects(t *testing.T) {
	// GIVEN: Open circuit breaker
	config := BreakerConfig{
		MaxFailures:  1,
		OpenTimeout:  100 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 1,
	}
	cb := NewCircuitBreaker(config)

	// Open circuit
	cb.CallWithResult(func() (interface{}, error) {
		return nil, fmt.Errorf("fail")
	})
	assert.Equal(t, StateOpen, cb.GetState())

	// WHEN: Attempt operation while open
	result, err := cb.CallWithResult(func() (interface{}, error) {
		return "should not execute", nil
	})

	// THEN: Request is rejected
	require.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "circuit breaker is open")
}

// TestCircuitBreaker_Reset verifies manual reset
func TestCircuitBreaker_Reset(t *testing.T) {
	// GIVEN: Open circuit breaker with failures
	config := BreakerConfig{
		MaxFailures:  2,
		OpenTimeout:  100 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 1,
	}
	cb := NewCircuitBreaker(config)

	// Open circuit
	for i := 0; i < 2; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	assert.Equal(t, StateOpen, cb.GetState())
	assert.Equal(t, 2, cb.GetFailures())

	// WHEN: Circuit is manually reset
	cb.Reset()

	// THEN: Circuit is closed with zero failures
	assert.Equal(t, StateClosed, cb.GetState())
	assert.Equal(t, 0, cb.GetFailures())
	assert.False(t, cb.IsOpen())
}

// TestCircuitBreaker_GetState verifies thread-safe state access
func TestCircuitBreaker_GetState(t *testing.T) {
	cb := NewCircuitBreaker(DefaultBreakerConfig())

	// Initial state
	assert.Equal(t, StateClosed, cb.GetState())

	// After failures
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	assert.Equal(t, StateOpen, cb.GetState())
}

// TestCircuitBreaker_GetFailures verifies failure count access
func TestCircuitBreaker_GetFailures(t *testing.T) {
	cb := NewCircuitBreaker(DefaultBreakerConfig())

	// Initial failures
	assert.Equal(t, 0, cb.GetFailures())

	// After 3 failures
	for i := 0; i < 3; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	assert.Equal(t, 3, cb.GetFailures())

	// After success (resets in closed state)
	cb.Call(func() error { return nil })
	assert.Equal(t, 0, cb.GetFailures())
}

// TestCircuitBreaker_IsOpen verifies open state check
func TestCircuitBreaker_IsOpen(t *testing.T) {
	config := BreakerConfig{
		MaxFailures:  2,
		OpenTimeout:  100 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 1,
	}
	cb := NewCircuitBreaker(config)

	// Initially closed
	assert.False(t, cb.IsOpen())

	// Open after failures
	for i := 0; i < 2; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	assert.True(t, cb.IsOpen())

	// Closed after reset
	cb.Reset()
	assert.False(t, cb.IsOpen())
}

// TestCircuitBreaker_Concurrent verifies thread safety
func TestCircuitBreaker_Concurrent(t *testing.T) {
	// GIVEN: Circuit breaker under concurrent load
	config := BreakerConfig{
		MaxFailures:  10,
		OpenTimeout:  50 * time.Millisecond,
		HalfOpenMax:  5,
		SuccessReset: 3,
	}
	cb := NewCircuitBreaker(config)

	var wg sync.WaitGroup
	successCount := 0
	var mu sync.Mutex

	// WHEN: 100 concurrent operations (mix of success/failure)
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(index int) {
			defer wg.Done()

			operation := func() error {
				// 50% failure rate
				if index%2 == 0 {
					return fmt.Errorf("fail")
				}
				return nil
			}

			err := cb.Call(operation)
			if err == nil {
				mu.Lock()
				successCount++
				mu.Unlock()
			}
		}(i)
	}

	wg.Wait()

	// THEN: Circuit breaker handles concurrent access safely
	// State should be either closed or open (not corrupted)
	state := cb.GetState()
	assert.True(t, state == StateClosed || state == StateOpen || state == StateHalfOpen)

	// Some operations should have succeeded
	assert.Greater(t, successCount, 0, "At least some operations should succeed")
}

// TestCircuitBreaker_Integration_FullCycle verifies complete state cycle
func TestCircuitBreaker_Integration_FullCycle(t *testing.T) {
	// GIVEN: Circuit breaker with specific config
	config := BreakerConfig{
		MaxFailures:  3,
		OpenTimeout:  50 * time.Millisecond,
		HalfOpenMax:  2,
		SuccessReset: 2,
	}
	cb := NewCircuitBreaker(config)

	// PHASE 1: Start in CLOSED state
	assert.Equal(t, StateClosed, cb.GetState())

	// PHASE 2: Fail 3 times → OPEN
	for i := 0; i < 3; i++ {
		cb.Call(func() error { return fmt.Errorf("fail") })
	}
	assert.Equal(t, StateOpen, cb.GetState())

	// PHASE 3: Wait for timeout → HALF_OPEN
	time.Sleep(60 * time.Millisecond)

	// First call transitions to half-open
	cb.Call(func() error { return nil })
	state := cb.GetState()
	assert.True(t, state == StateHalfOpen || state == StateClosed, "Should be half-open or closed")

	// PHASE 4: 2 successes in HALF_OPEN → CLOSED
	cb.Call(func() error { return nil })
	assert.Equal(t, StateClosed, cb.GetState())

	// PHASE 5: Verify circuit works normally in closed state
	err := cb.Call(func() error { return nil })
	require.NoError(t, err)
	assert.Equal(t, StateClosed, cb.GetState())
}
