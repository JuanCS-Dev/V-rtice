// Package ratelimit implements rate limiting and circuit breaker (Layer 5)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 5 of the "Guardian of Intent" v2.0:
// "CONTROLE DE FLUXO - Com que frequência?"
//
// Provides:
// - Token bucket rate limiting
// - Circuit breaker pattern
// - Violation tracking
package ratelimit

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/verticedev/vcli-go/pkg/security"
	"golang.org/x/time/rate"
)

var (
	// ErrRateLimitExceeded is returned when rate limit is exceeded
	ErrRateLimitExceeded = errors.New("rate limit exceeded")
	
	// ErrCircuitOpen is returned when circuit breaker is open
	ErrCircuitOpen = errors.New("circuit breaker open")
)

// Limiter handles rate limiting with circuit breaker
type Limiter struct {
	limiters  map[string]*userLimiter
	config    security.RateLimitConfig
	breakers  map[string]*CircuitBreaker
	mu        sync.RWMutex
}

// NewLimiter creates a new rate limiter
func NewLimiter(config security.RateLimitConfig) *Limiter {
	return &Limiter{
		limiters: make(map[string]*userLimiter),
		config:   config,
		breakers: make(map[string]*CircuitBreaker),
	}
}

// Allow checks if a request is allowed for a user
//
// Uses token bucket algorithm for smooth rate limiting
func (l *Limiter) Allow(ctx context.Context, userID string) error {
	// Get or create limiter for user
	limiter := l.getUserLimiter(userID)
	
	// Check circuit breaker first
	breaker := l.getCircuitBreaker(userID)
	if !breaker.Allow() {
		return &security.SecurityError{
			Layer:     "ratelimit",
			Type:      security.ErrorTypeRateLimit,
			Message:   "Circuit breaker open",
			Details: map[string]interface{}{
				"state": breaker.State(),
			},
			Timestamp: time.Now(),
			UserID:    userID,
		}
	}
	
	// Check rate limit
	if !limiter.limiter.Allow() {
		// Record violation
		limiter.violations++
		limiter.lastViolation = time.Now()
		
		// Trip circuit breaker if too many violations
		if limiter.violations >= 5 {
			breaker.RecordFailure()
		}
		
		return &security.SecurityError{
			Layer:     "ratelimit",
			Type:      security.ErrorTypeRateLimit,
			Message:   "Rate limit exceeded",
			Details: map[string]interface{}{
				"limit":      l.config.RequestsPerMinute,
				"violations": limiter.violations,
			},
			Timestamp: time.Now(),
			UserID:    userID,
		}
	}
	
	// Request allowed
	limiter.requests++
	
	// Record success in circuit breaker
	breaker.RecordSuccess()
	
	return nil
}

// getUserLimiter gets or creates a limiter for a user
func (l *Limiter) getUserLimiter(userID string) *userLimiter {
	l.mu.Lock()
	defer l.mu.Unlock()
	
	limiter, exists := l.limiters[userID]
	if !exists {
		// Create new limiter with token bucket
		// rate.Limit is requests per second, so convert from per minute
		perSecond := float64(l.config.RequestsPerMinute) / 60.0
		limiter = &userLimiter{
			limiter:       rate.NewLimiter(rate.Limit(perSecond), l.config.BurstSize),
			violations:    0,
			requests:      0,
			lastViolation: time.Time{},
		}
		l.limiters[userID] = limiter
	}
	
	return limiter
}

// getCircuitBreaker gets or creates a circuit breaker for a user
func (l *Limiter) getCircuitBreaker(userID string) *CircuitBreaker {
	l.mu.Lock()
	defer l.mu.Unlock()
	
	breaker, exists := l.breakers[userID]
	if !exists {
		config := security.CircuitBreakerConfig{
			MaxFailures:      5,
			OpenDuration:     60 * time.Second,
			HalfOpenRequests: 1,
		}
		breaker = NewCircuitBreaker(config)
		l.breakers[userID] = breaker
	}
	
	return breaker
}

// GetStats returns rate limiting statistics for a user
func (l *Limiter) GetStats(userID string) *Stats {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	limiter, exists := l.limiters[userID]
	if !exists {
		return &Stats{}
	}
	
	breaker := l.breakers[userID]
	
	return &Stats{
		Requests:      limiter.requests,
		Violations:    limiter.violations,
		LastViolation: limiter.lastViolation,
		BreakerState:  breaker.State(),
	}
}

// Reset resets rate limiting state for a user
func (l *Limiter) Reset(userID string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	
	delete(l.limiters, userID)
	delete(l.breakers, userID)
}

// userLimiter tracks rate limiting state per user
type userLimiter struct {
	limiter       *rate.Limiter
	violations    int
	requests      int64
	lastViolation time.Time
}

// Stats contains rate limiting statistics
type Stats struct {
	Requests      int64
	Violations    int
	LastViolation time.Time
	BreakerState  BreakerState
}

// CircuitBreaker implements circuit breaker pattern
type CircuitBreaker struct {
	config      security.CircuitBreakerConfig
	state       BreakerState
	failures    int
	successes   int
	lastFailure time.Time
	mu          sync.RWMutex
}

// BreakerState represents circuit breaker state
type BreakerState int

const (
	// StateClosed - circuit is closed, requests pass through
	StateClosed BreakerState = iota
	// StateOpen - circuit is open, requests are blocked
	StateOpen
	// StateHalfOpen - circuit is testing if service recovered
	StateHalfOpen
)

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(config security.CircuitBreakerConfig) *CircuitBreaker {
	return &CircuitBreaker{
		config:    config,
		state:     StateClosed,
		failures:  0,
		successes: 0,
	}
}

// Allow checks if request is allowed through circuit breaker
func (cb *CircuitBreaker) Allow() bool {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	
	switch cb.state {
	case StateClosed:
		return true
		
	case StateOpen:
		// Check if we should transition to half-open
		if time.Since(cb.lastFailure) > cb.config.OpenDuration {
			cb.mu.RUnlock()
			cb.mu.Lock()
			cb.state = StateHalfOpen
			cb.successes = 0
			cb.mu.Unlock()
			cb.mu.RLock()
			return true
		}
		return false
		
	case StateHalfOpen:
		// Allow limited requests to test if service recovered
		return cb.successes < cb.config.HalfOpenRequests
		
	default:
		return false
	}
}

// RecordSuccess records a successful request
func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	
	switch cb.state {
	case StateHalfOpen:
		cb.successes++
		// If we've had enough successful half-open requests, close circuit
		if cb.successes >= cb.config.HalfOpenRequests {
			cb.state = StateClosed
			cb.failures = 0
		}
		
	case StateClosed:
		// Reset failure count on success
		cb.failures = 0
	}
}

// RecordFailure records a failed request
func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	
	cb.failures++
	cb.lastFailure = time.Now()
	
	switch cb.state {
	case StateClosed:
		// Trip to open if too many failures
		if cb.failures >= cb.config.MaxFailures {
			cb.state = StateOpen
		}
		
	case StateHalfOpen:
		// Immediately trip to open on failure in half-open
		cb.state = StateOpen
	}
}

// State returns current circuit breaker state
func (cb *CircuitBreaker) State() BreakerState {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// String returns string representation of breaker state
func (s BreakerState) String() string {
	switch s {
	case StateClosed:
		return "closed"
	case StateOpen:
		return "open"
	case StateHalfOpen:
		return "half-open"
	default:
		return "unknown"
	}
}
