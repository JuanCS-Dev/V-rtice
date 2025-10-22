package circuitbreaker

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/verticedev/vcli-go/internal/errors"
)

// State represents the circuit breaker state
type State int

const (
	// StateClosed means the circuit is closed and requests pass through
	StateClosed State = iota
	// StateOpen means the circuit is open and requests are blocked
	StateOpen
	// StateHalfOpen means the circuit is testing if the service recovered
	StateHalfOpen
)

func (s State) String() string {
	switch s {
	case StateClosed:
		return "CLOSED"
	case StateOpen:
		return "OPEN"
	case StateHalfOpen:
		return "HALF_OPEN"
	default:
		return "UNKNOWN"
	}
}

// Config holds circuit breaker configuration
type Config struct {
	// MaxFailures is the number of failures before opening the circuit
	MaxFailures int
	// Timeout is how long to wait before attempting to close the circuit
	Timeout time.Duration
	// ResetTimeout is how long to wait before resetting failure count
	ResetTimeout time.Duration
	// OnStateChange is called when the circuit breaker state changes
	OnStateChange func(from, to State)
}

// DefaultConfig returns a sensible default configuration
func DefaultConfig() *Config {
	return &Config{
		MaxFailures:  5,
		Timeout:      10 * time.Second,
		ResetTimeout: 30 * time.Second,
	}
}

// CircuitBreaker implements the circuit breaker pattern
type CircuitBreaker struct {
	mu            sync.RWMutex
	config        *Config
	state         State
	failures      int
	lastFailTime  time.Time
	lastStateTime time.Time
}

// New creates a new circuit breaker
func New(config *Config) *CircuitBreaker {
	if config == nil {
		config = DefaultConfig()
	}

	return &CircuitBreaker{
		config:        config,
		state:         StateClosed,
		lastStateTime: time.Now(),
	}
}

// Execute runs a function through the circuit breaker
func (cb *CircuitBreaker) Execute(ctx context.Context, fn func() error) error {
	// Check if circuit allows execution
	if err := cb.beforeRequest(); err != nil {
		return err
	}

	// Execute the function
	err := fn()

	// Record result
	cb.afterRequest(err)

	return err
}

// ExecuteWithResult runs a function with a result through the circuit breaker
func ExecuteWithResult[T any](ctx context.Context, cb *CircuitBreaker, fn func() (T, error)) (T, error) {
	var result T

	// Check if circuit allows execution
	if err := cb.beforeRequest(); err != nil {
		return result, err
	}

	// Execute the function
	result, err := fn()

	// Record result
	cb.afterRequest(err)

	return result, err
}

// beforeRequest checks if the request should be allowed
func (cb *CircuitBreaker) beforeRequest() error {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	now := time.Now()

	switch cb.state {
	case StateClosed:
		// Check if we should reset failure count
		if now.Sub(cb.lastFailTime) > cb.config.ResetTimeout {
			cb.failures = 0
		}
		return nil

	case StateOpen:
		// Check if we should transition to half-open
		if now.Sub(cb.lastStateTime) >= cb.config.Timeout {
			cb.setState(StateHalfOpen)
			return nil
		}
		return errors.New(errors.ErrorTypeUnavailable, "circuit breaker is open")

	case StateHalfOpen:
		// Allow one request to test if service recovered
		return nil

	default:
		return errors.New(errors.ErrorTypeInternal, "unknown circuit breaker state")
	}
}

// afterRequest records the result of a request
func (cb *CircuitBreaker) afterRequest(err error) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.onFailure()
	} else {
		cb.onSuccess()
	}
}

// onSuccess is called when a request succeeds
func (cb *CircuitBreaker) onSuccess() {
	switch cb.state {
	case StateClosed:
		// Reset failure count on success
		cb.failures = 0

	case StateHalfOpen:
		// Service recovered, close the circuit
		cb.setState(StateClosed)
		cb.failures = 0
	}
}

// onFailure is called when a request fails
func (cb *CircuitBreaker) onFailure() {
	cb.failures++
	cb.lastFailTime = time.Now()

	switch cb.state {
	case StateClosed:
		// Check if we should open the circuit
		if cb.failures >= cb.config.MaxFailures {
			cb.setState(StateOpen)
		}

	case StateHalfOpen:
		// Service still failing, open the circuit again
		cb.setState(StateOpen)
	}
}

// setState changes the circuit breaker state
func (cb *CircuitBreaker) setState(newState State) {
	if cb.state == newState {
		return
	}

	oldState := cb.state
	cb.state = newState
	cb.lastStateTime = time.Now()

	// Call state change callback
	if cb.config.OnStateChange != nil {
		cb.config.OnStateChange(oldState, newState)
	}
}

// State returns the current state
func (cb *CircuitBreaker) State() State {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// Failures returns the current failure count
func (cb *CircuitBreaker) Failures() int {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.failures
}

// Reset resets the circuit breaker to closed state
func (cb *CircuitBreaker) Reset() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	oldState := cb.state
	cb.state = StateClosed
	cb.failures = 0
	cb.lastStateTime = time.Now()

	if cb.config.OnStateChange != nil && oldState != StateClosed {
		cb.config.OnStateChange(oldState, StateClosed)
	}
}

// Stats returns circuit breaker statistics
type Stats struct {
	State         State
	Failures      int
	LastFailTime  time.Time
	LastStateTime time.Time
	TimeSinceOpen time.Duration
}

// Stats returns current statistics
func (cb *CircuitBreaker) Stats() Stats {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	stats := Stats{
		State:         cb.state,
		Failures:      cb.failures,
		LastFailTime:  cb.lastFailTime,
		LastStateTime: cb.lastStateTime,
	}

	if cb.state == StateOpen {
		stats.TimeSinceOpen = time.Since(cb.lastStateTime)
	}

	return stats
}

// String returns a string representation of the circuit breaker
func (cb *CircuitBreaker) String() string {
	stats := cb.Stats()
	return fmt.Sprintf("CircuitBreaker{state=%s, failures=%d}", stats.State, stats.Failures)
}
