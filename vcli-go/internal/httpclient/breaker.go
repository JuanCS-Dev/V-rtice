package httpclient

import (
	"sync"
	"time"

	"github.com/verticedev/vcli-go/internal/errors"
)

// State represents circuit breaker state
type State int

const (
	StateClosed State = iota // Normal operation
	StateOpen                // Failing, reject requests
	StateHalfOpen            // Testing recovery
)

func (s State) String() string {
	switch s {
	case StateClosed:
		return "closed"
	case StateOpen:
		return "open"
	case StateHalfOpen:
		return "half_open"
	default:
		return "unknown"
	}
}

// BreakerConfig defines circuit breaker behavior
type BreakerConfig struct {
	MaxFailures  int           // Failures before opening
	OpenTimeout  time.Duration // Time before attempting half-open
	HalfOpenMax  int           // Max requests in half-open state
	SuccessReset int           // Successes to reset from half-open
}

// DefaultBreakerConfig returns conservative defaults
func DefaultBreakerConfig() BreakerConfig {
	return BreakerConfig{
		MaxFailures:  5,
		OpenTimeout:  30 * time.Second,
		HalfOpenMax:  3,
		SuccessReset: 2,
	}
}

// CircuitBreaker protects against cascading failures
type CircuitBreaker struct {
	config BreakerConfig

	mu               sync.RWMutex
	state            State
	failures         int
	successes        int
	halfOpenAttempts int
	openedAt         time.Time
}

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(config BreakerConfig) *CircuitBreaker {
	return &CircuitBreaker{
		config: config,
		state:  StateClosed,
	}
}

// Call executes an operation through the circuit breaker
func (cb *CircuitBreaker) Call(operation func() error) error {
	// Check if we can proceed
	if err := cb.beforeCall(); err != nil {
		return err
	}

	// Execute operation
	err := operation()

	// Update state based on result
	cb.afterCall(err)

	return err
}

// CallWithResult executes an operation that returns a result
func (cb *CircuitBreaker) CallWithResult(operation func() (interface{}, error)) (interface{}, error) {
	if err := cb.beforeCall(); err != nil {
		return nil, err
	}

	result, err := operation()
	cb.afterCall(err)

	return result, err
}

// beforeCall checks if operation can proceed
func (cb *CircuitBreaker) beforeCall() error {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.state {
	case StateClosed:
		// Normal operation
		return nil

	case StateOpen:
		// Check if timeout expired
		if time.Since(cb.openedAt) >= cb.config.OpenTimeout {
			// Transition to half-open
			cb.state = StateHalfOpen
			cb.halfOpenAttempts = 1 // Count this request
			cb.successes = 0
			return nil
		}
		// Still open, reject request
		return errors.New(errors.ErrorTypeCircuitOpen, "circuit breaker is open")

	case StateHalfOpen:
		// Allow limited requests
		if cb.halfOpenAttempts >= cb.config.HalfOpenMax {
			return errors.New(errors.ErrorTypeCircuitOpen, "circuit breaker half-open limit reached")
		}
		cb.halfOpenAttempts++
		return nil

	default:
		return errors.New(errors.ErrorTypeInternal, "invalid circuit breaker state")
	}
}

// afterCall updates state based on operation result
func (cb *CircuitBreaker) afterCall(err error) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err == nil {
		// Success
		cb.onSuccess()
	} else {
		// Failure
		cb.onFailure()
	}
}

// onSuccess handles successful operation
func (cb *CircuitBreaker) onSuccess() {
	switch cb.state {
	case StateClosed:
		// Reset failure counter
		cb.failures = 0

	case StateHalfOpen:
		cb.successes++
		// Check if we can close
		if cb.successes >= cb.config.SuccessReset {
			cb.state = StateClosed
			cb.failures = 0
			cb.successes = 0
			cb.halfOpenAttempts = 0
		}
	}
}

// onFailure handles failed operation
func (cb *CircuitBreaker) onFailure() {
	switch cb.state {
	case StateClosed:
		cb.failures++
		// Check if we should open
		if cb.failures >= cb.config.MaxFailures {
			cb.state = StateOpen
			cb.openedAt = time.Now()
		}

	case StateHalfOpen:
		// Immediate open on failure in half-open
		cb.state = StateOpen
		cb.openedAt = time.Now()
		cb.halfOpenAttempts = 0
		cb.successes = 0
	}
}

// GetState returns current state (thread-safe)
func (cb *CircuitBreaker) GetState() State {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// GetFailures returns failure count (thread-safe)
func (cb *CircuitBreaker) GetFailures() int {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.failures
}

// Reset resets the circuit breaker to closed state
func (cb *CircuitBreaker) Reset() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.state = StateClosed
	cb.failures = 0
	cb.successes = 0
	cb.halfOpenAttempts = 0
}

// IsOpen checks if circuit is open (thread-safe)
func (cb *CircuitBreaker) IsOpen() bool {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state == StateOpen
}
