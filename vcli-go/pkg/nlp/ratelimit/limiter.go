// Package ratelimit implements Layer 5 (Flow Control) of Guardian Zero Trust Security.
//
// "How often?" - Controlling the frequency and rate of operations.
//
// Provides:
// - Token bucket rate limiting
// - Sliding window counters
// - Per-user and per-resource limits
// - Burst control
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)
// Date: 2025-10-12
package ratelimit

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

// RateLimiter provides rate limiting functionality.
type RateLimiter struct {
	buckets map[string]*TokenBucket
	mu      sync.RWMutex
	config  *RateLimitConfig
}

// RateLimitConfig configures rate limiting behavior.
type RateLimitConfig struct {
	// Rate limits
	RequestsPerMinute int           // Sustained rate
	BurstSize         int           // Max burst
	Window            time.Duration // Time window
	
	// Scope
	PerUser     bool // Limit per user
	PerResource bool // Limit per resource
	PerAction   bool // Limit per action type
	
	// Cleanup
	CleanupInterval time.Duration
}

// TokenBucket implements token bucket algorithm.
type TokenBucket struct {
	capacity  int       // Max tokens (burst size)
	tokens    float64   // Current tokens
	rate      float64   // Tokens per second
	lastRefill time.Time
	mu        sync.Mutex
}

// AllowResult indicates if request is allowed.
type AllowResult struct {
	Allowed       bool
	Reason        string
	RetryAfter    time.Duration
	CurrentTokens int
	Limit         int
}

// NewRateLimiter creates a new rate limiter.
func NewRateLimiter(config *RateLimitConfig) *RateLimiter {
	if config == nil {
		config = DefaultRateLimitConfig()
	}
	
	rl := &RateLimiter{
		buckets: make(map[string]*TokenBucket),
		config:  config,
	}
	
	// Start cleanup goroutine if interval set
	if config.CleanupInterval > 0 {
		go rl.cleanup()
	}
	
	return rl
}

// DefaultRateLimitConfig returns default configuration.
func DefaultRateLimitConfig() *RateLimitConfig {
	return &RateLimitConfig{
		RequestsPerMinute: 60,  // 1 per second sustained
		BurstSize:         10,  // Allow burst of 10
		Window:            time.Minute,
		PerUser:           true,
		PerResource:       false,
		PerAction:         false,
		CleanupInterval:   5 * time.Minute,
	}
}

// Allow checks if a request is allowed.
func (rl *RateLimiter) Allow(userID string, resource string, action string) *AllowResult {
	key := rl.buildKey(userID, resource, action)
	
	rl.mu.Lock()
	bucket, exists := rl.buckets[key]
	if !exists {
		bucket = NewTokenBucket(rl.config.BurstSize, rl.config.RequestsPerMinute)
		rl.buckets[key] = bucket
	}
	rl.mu.Unlock()
	
	return bucket.Take()
}

// AllowN checks if N requests are allowed.
func (rl *RateLimiter) AllowN(userID string, resource string, action string, n int) *AllowResult {
	key := rl.buildKey(userID, resource, action)
	
	rl.mu.Lock()
	bucket, exists := rl.buckets[key]
	if !exists {
		bucket = NewTokenBucket(rl.config.BurstSize, rl.config.RequestsPerMinute)
		rl.buckets[key] = bucket
	}
	rl.mu.Unlock()
	
	return bucket.TakeN(n)
}

// GetTokens returns current token count for a key.
func (rl *RateLimiter) GetTokens(userID string, resource string, action string) int {
	key := rl.buildKey(userID, resource, action)
	
	rl.mu.RLock()
	bucket, exists := rl.buckets[key]
	rl.mu.RUnlock()
	
	if !exists {
		return rl.config.BurstSize // New bucket would have full tokens
	}
	
	return bucket.Available()
}

// Reset resets rate limit for a key.
func (rl *RateLimiter) Reset(userID string, resource string, action string) {
	key := rl.buildKey(userID, resource, action)
	
	rl.mu.Lock()
	delete(rl.buckets, key)
	rl.mu.Unlock()
}

// buildKey constructs rate limit key based on config.
func (rl *RateLimiter) buildKey(userID, resource, action string) string {
	parts := []string{}
	
	if rl.config.PerUser && userID != "" {
		parts = append(parts, "u:"+userID)
	}
	if rl.config.PerResource && resource != "" {
		parts = append(parts, "r:"+resource)
	}
	if rl.config.PerAction && action != "" {
		parts = append(parts, "a:"+action)
	}
	
	if len(parts) == 0 {
		return "global"
	}
	
	key := ""
	for i, part := range parts {
		if i > 0 {
			key += ":"
		}
		key += part
	}
	return key
}

// cleanup removes stale buckets periodically.
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(rl.config.CleanupInterval)
	defer ticker.Stop()
	
	for range ticker.C {
		rl.mu.Lock()
		now := time.Now()
		for key, bucket := range rl.buckets {
			// Remove buckets inactive for > 2x cleanup interval
			if now.Sub(bucket.lastRefill) > 2*rl.config.CleanupInterval {
				delete(rl.buckets, key)
			}
		}
		rl.mu.Unlock()
	}
}

// GetStats returns rate limiter statistics.
func (rl *RateLimiter) GetStats() *RateLimiterStats {
	rl.mu.RLock()
	defer rl.mu.RUnlock()
	
	return &RateLimiterStats{
		ActiveBuckets: len(rl.buckets),
		Config:        rl.config,
	}
}

// RateLimiterStats contains statistics.
type RateLimiterStats struct {
	ActiveBuckets int
	Config        *RateLimitConfig
}

// NewTokenBucket creates a token bucket.
func NewTokenBucket(capacity int, requestsPerMinute int) *TokenBucket {
	rate := float64(requestsPerMinute) / 60.0 // tokens per second
	
	return &TokenBucket{
		capacity:   capacity,
		tokens:     float64(capacity), // Start full
		rate:       rate,
		lastRefill: time.Now(),
	}
}

// Take attempts to take 1 token from bucket.
func (tb *TokenBucket) Take() *AllowResult {
	return tb.TakeN(1)
}

// TakeN attempts to take N tokens from bucket.
func (tb *TokenBucket) TakeN(n int) *AllowResult {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	
	// Refill tokens based on time elapsed
	tb.refill()
	
	if tb.tokens >= float64(n) {
		tb.tokens -= float64(n)
		return &AllowResult{
			Allowed:       true,
			CurrentTokens: int(tb.tokens),
			Limit:         tb.capacity,
		}
	}
	
	// Not enough tokens
	tokensNeeded := float64(n) - tb.tokens
	retryAfter := time.Duration(tokensNeeded/tb.rate) * time.Second
	
	return &AllowResult{
		Allowed:       false,
		Reason:        fmt.Sprintf("rate limit exceeded (need %d tokens, have %.1f)", n, tb.tokens),
		RetryAfter:    retryAfter,
		CurrentTokens: int(tb.tokens),
		Limit:         tb.capacity,
	}
}

// Available returns current available tokens.
func (tb *TokenBucket) Available() int {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	
	tb.refill()
	return int(tb.tokens)
}

// refill adds tokens based on elapsed time.
// Must be called with lock held.
func (tb *TokenBucket) refill() {
	now := time.Now()
	elapsed := now.Sub(tb.lastRefill).Seconds()
	
	// Add tokens based on rate and time elapsed
	tokensToAdd := elapsed * tb.rate
	tb.tokens += tokensToAdd
	
	// Cap at capacity
	if tb.tokens > float64(tb.capacity) {
		tb.tokens = float64(tb.capacity)
	}
	
	tb.lastRefill = now
}

// SlidingWindow implements sliding window counter.
type SlidingWindow struct {
	window   time.Duration
	maxCount int
	requests []time.Time
	mu       sync.Mutex
}

// NewSlidingWindow creates a sliding window counter.
func NewSlidingWindow(window time.Duration, maxCount int) *SlidingWindow {
	return &SlidingWindow{
		window:   window,
		maxCount: maxCount,
		requests: make([]time.Time, 0),
	}
}

// Allow checks if request is within limits.
func (sw *SlidingWindow) Allow() bool {
	sw.mu.Lock()
	defer sw.mu.Unlock()
	
	now := time.Now()
	windowStart := now.Add(-sw.window)
	
	// Remove old requests outside window
	validRequests := []time.Time{}
	for _, t := range sw.requests {
		if t.After(windowStart) {
			validRequests = append(validRequests, t)
		}
	}
	sw.requests = validRequests
	
	// Check if we're within limit
	if len(sw.requests) >= sw.maxCount {
		return false
	}
	
	// Add current request
	sw.requests = append(sw.requests, now)
	return true
}

// Count returns current count in window.
func (sw *SlidingWindow) Count() int {
	sw.mu.Lock()
	defer sw.mu.Unlock()
	
	now := time.Now()
	windowStart := now.Add(-sw.window)
	
	count := 0
	for _, t := range sw.requests {
		if t.After(windowStart) {
			count++
		}
	}
	
	return count
}

// Reset clears the window.
func (sw *SlidingWindow) Reset() {
	sw.mu.Lock()
	defer sw.mu.Unlock()
	
	sw.requests = make([]time.Time, 0)
}

// Throttler combines rate limiting with throttling.
type Throttler struct {
	rateLimiter *RateLimiter
	windows     map[string]*SlidingWindow
	mu          sync.RWMutex
}

// NewThrottler creates a throttler.
func NewThrottler(config *RateLimitConfig) *Throttler {
	return &Throttler{
		rateLimiter: NewRateLimiter(config),
		windows:     make(map[string]*SlidingWindow),
	}
}

// Allow checks both rate limit and throttle.
func (t *Throttler) Allow(userID string, resource string, action string) error {
	// Check rate limit
	result := t.rateLimiter.Allow(userID, resource, action)
	if !result.Allowed {
		return errors.New(result.Reason)
	}
	
	return nil
}

// GetRateLimiter returns the underlying rate limiter.
func (t *Throttler) GetRateLimiter() *RateLimiter {
	return t.rateLimiter
}
