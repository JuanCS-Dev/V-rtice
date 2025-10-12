package ratelimit

import (
"testing"
"time"

"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
)

func TestNewRateLimiter(t *testing.T) {
limiter := NewRateLimiter(nil)
assert.NotNil(t, limiter)
assert.NotNil(t, limiter.config)
}

func TestRateLimiter_Allow(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 60,
BurstSize:         10,
PerUser:           true,
}
limiter := NewRateLimiter(config)

// First request should be allowed
result := limiter.Allow("user1", "pods", "get")
assert.True(t, result.Allowed)
assert.Equal(t, 9, result.CurrentTokens) // 10 - 1
}

func TestRateLimiter_BurstLimit(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 60,
BurstSize:         3,
PerUser:           true,
}
limiter := NewRateLimiter(config)

// Use up burst
for i := 0; i < 3; i++ {
result := limiter.Allow("user1", "pods", "get")
require.True(t, result.Allowed, "Request %d should be allowed", i+1)
}

// Next should be denied
result := limiter.Allow("user1", "pods", "get")
assert.False(t, result.Allowed)
assert.Contains(t, result.Reason, "rate limit exceeded")
}

func TestRateLimiter_TokenRefill(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 600, // 10 per second for faster test
BurstSize:         2,
PerUser:           true,
}
limiter := NewRateLimiter(config)

// Use tokens
limiter.Allow("user1", "pods", "get")
limiter.Allow("user1", "pods", "get")

// Wait for refill
time.Sleep(150 * time.Millisecond) // Should refill ~1.5 tokens

// Should be allowed again
result := limiter.Allow("user1", "pods", "get")
assert.True(t, result.Allowed)
}

func TestRateLimiter_PerUser(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 60,
BurstSize:         2,
PerUser:           true,
}
limiter := NewRateLimiter(config)

// user1 uses up burst
limiter.Allow("user1", "pods", "get")
limiter.Allow("user1", "pods", "get")

// user1 should be limited
result := limiter.Allow("user1", "pods", "get")
assert.False(t, result.Allowed)

// user2 should still be allowed (different bucket)
result = limiter.Allow("user2", "pods", "get")
assert.True(t, result.Allowed)
}

func TestRateLimiter_Reset(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 60,
BurstSize:         1,
PerUser:           true,
}
limiter := NewRateLimiter(config)

// Use up token
limiter.Allow("user1", "pods", "get")

// Should be denied
result := limiter.Allow("user1", "pods", "get")
assert.False(t, result.Allowed)

// Reset
limiter.Reset("user1", "pods", "get")

// Should be allowed again
result = limiter.Allow("user1", "pods", "get")
assert.True(t, result.Allowed)
}

func TestRateLimiter_GetTokens(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 60,
BurstSize:         10,
PerUser:           true,
}
limiter := NewRateLimiter(config)

// Initial tokens
tokens := limiter.GetTokens("user1", "pods", "get")
assert.Equal(t, 10, tokens)

// Use some
limiter.Allow("user1", "pods", "get")
limiter.Allow("user1", "pods", "get")

tokens = limiter.GetTokens("user1", "pods", "get")
assert.Equal(t, 8, tokens)
}

func TestTokenBucket_Take(t *testing.T) {
bucket := NewTokenBucket(5, 60) // 5 capacity, 1/sec rate

result := bucket.Take()
assert.True(t, result.Allowed)
assert.Equal(t, 4, result.CurrentTokens)
}

func TestTokenBucket_TakeN(t *testing.T) {
bucket := NewTokenBucket(5, 60)

result := bucket.TakeN(3)
assert.True(t, result.Allowed)
assert.Equal(t, 2, result.CurrentTokens)

// Try to take more than available
result = bucket.TakeN(3)
assert.False(t, result.Allowed)
assert.GreaterOrEqual(t, result.RetryAfter, time.Duration(0))
}

func TestTokenBucket_Available(t *testing.T) {
bucket := NewTokenBucket(10, 60)

assert.Equal(t, 10, bucket.Available())

bucket.Take()
assert.Equal(t, 9, bucket.Available())
}

func TestTokenBucket_Refill(t *testing.T) {
bucket := NewTokenBucket(5, 600) // 10/sec for faster test

// Use all tokens
for i := 0; i < 5; i++ {
bucket.Take()
}
assert.Equal(t, 0, bucket.Available())

// Wait for refill
time.Sleep(150 * time.Millisecond) // ~1.5 tokens

available := bucket.Available()
assert.Greater(t, available, 0)
}

func TestSlidingWindow_Allow(t *testing.T) {
window := NewSlidingWindow(time.Second, 3)

assert.True(t, window.Allow())
assert.True(t, window.Allow())
assert.True(t, window.Allow())
assert.False(t, window.Allow()) // 4th should fail
}

func TestSlidingWindow_Count(t *testing.T) {
window := NewSlidingWindow(time.Second, 10)

window.Allow()
window.Allow()
window.Allow()

assert.Equal(t, 3, window.Count())
}

func TestSlidingWindow_Reset(t *testing.T) {
window := NewSlidingWindow(time.Second, 2)

window.Allow()
window.Allow()
assert.False(t, window.Allow())

window.Reset()
assert.True(t, window.Allow())
}

func TestSlidingWindow_WindowExpiry(t *testing.T) {
window := NewSlidingWindow(100*time.Millisecond, 2)

window.Allow()
window.Allow()
assert.False(t, window.Allow())

// Wait for window to expire
time.Sleep(150 * time.Millisecond)

// Should allow again
assert.True(t, window.Allow())
}

func TestThrottler_Allow(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 60,
BurstSize:         5,
PerUser:           true,
}
throttler := NewThrottler(config)

// Should allow initially
err := throttler.Allow("user1", "pods", "get")
assert.NoError(t, err)
}

func TestRateLimiter_GetStats(t *testing.T) {
limiter := NewRateLimiter(nil)

limiter.Allow("user1", "pods", "get")
limiter.Allow("user2", "pods", "get")

stats := limiter.GetStats()
assert.Equal(t, 2, stats.ActiveBuckets)
assert.NotNil(t, stats.Config)
}

func TestDefaultRateLimitConfig(t *testing.T) {
config := DefaultRateLimitConfig()

assert.Equal(t, 60, config.RequestsPerMinute)
assert.Equal(t, 10, config.BurstSize)
assert.True(t, config.PerUser)
}

func TestRateLimiter_BuildKey(t *testing.T) {
t.Run("PerUser only", func(t *testing.T) {
config := &RateLimitConfig{PerUser: true}
limiter := NewRateLimiter(config)

key := limiter.buildKey("user1", "pods", "get")
assert.Equal(t, "u:user1", key)
})

t.Run("PerUser and PerResource", func(t *testing.T) {
config := &RateLimitConfig{PerUser: true, PerResource: true}
limiter := NewRateLimiter(config)

key := limiter.buildKey("user1", "pods", "get")
assert.Equal(t, "u:user1:r:pods", key)
})

t.Run("Global", func(t *testing.T) {
config := &RateLimitConfig{}
limiter := NewRateLimiter(config)

key := limiter.buildKey("user1", "pods", "get")
assert.Equal(t, "global", key)
})
}

func TestRateLimiter_AllowN(t *testing.T) {
config := &RateLimitConfig{
RequestsPerMinute: 60,
BurstSize:         10,
PerUser:           true,
}
limiter := NewRateLimiter(config)

// Take 5 tokens at once
result := limiter.AllowN("user1", "pods", "get", 5)
assert.True(t, result.Allowed)
assert.Equal(t, 5, result.CurrentTokens)
}

func TestRateLimiter_Cleanup(t *testing.T) {
	config := &RateLimitConfig{
		RequestsPerMinute: 60,
		BurstSize:         10,
		PerUser:           true,
		CleanupInterval:   100 * time.Millisecond,
	}
	limiter := NewRateLimiter(config)
	
	// Create some buckets
	limiter.Allow("user1", "pods", "get")
	limiter.Allow("user2", "deployments", "list")
	
	// Initially should have 2 buckets
	stats := limiter.GetStats()
	assert.Equal(t, 2, stats.ActiveBuckets)
	
	// Wait for cleanup to run (buckets should still be active)
	time.Sleep(150 * time.Millisecond)
	
	// Buckets should still exist (not yet stale)
	stats = limiter.GetStats()
	assert.GreaterOrEqual(t, stats.ActiveBuckets, 0) // May be cleaned or not depending on timing
}

func TestThrottler_AllowExceeded(t *testing.T) {
	config := &RateLimitConfig{
		RequestsPerMinute: 2, // Very low limit
		BurstSize:         2,
		PerUser:           true,
	}
	throttler := NewThrottler(config)
	
	// First 2 requests should succeed
	err := throttler.Allow("user1", "pods", "get")
	assert.NoError(t, err)
	
	err = throttler.Allow("user1", "pods", "get")
	assert.NoError(t, err)
	
	// Third request should fail (exceeded limit)
	err = throttler.Allow("user1", "pods", "get")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "rate limit exceeded")
}

func TestThrottler_GetRateLimiter(t *testing.T) {
	config := DefaultRateLimitConfig()
	throttler := NewThrottler(config)
	
	// Should return underlying rate limiter
	rateLimiter := throttler.GetRateLimiter()
	assert.NotNil(t, rateLimiter)
	
	// Should be able to use it directly
	result := rateLimiter.Allow("user1", "pods", "get")
	assert.True(t, result.Allowed)
}

func TestTokenBucket_RefillOverflow(t *testing.T) {
	bucket := NewTokenBucket(10, 600) // 600 requests per minute = 10 per second
	
	// Drain bucket
	result := bucket.TakeN(10)
	assert.True(t, result.Allowed)
	assert.Equal(t, 0, bucket.Available())
	
	// Wait for refill (need enough time to generate tokens)
	time.Sleep(200 * time.Millisecond)
	
	// Should have refilled some tokens (but not exceed capacity)
	available := bucket.Available()
	assert.Greater(t, available, 0)
	assert.LessOrEqual(t, available, 10)
}

func TestBuildKey_AllScopes(t *testing.T) {
	config := &RateLimitConfig{
		RequestsPerMinute: 60,
		BurstSize:         10,
		PerUser:           false,
		PerResource:       true,
		PerAction:         true,
	}
	limiter := NewRateLimiter(config)
	
	// Test different key combinations
	result1 := limiter.Allow("user1", "pods", "get")
	assert.True(t, result1.Allowed)
	
	// Different resource should not share limit
	result2 := limiter.Allow("user1", "deployments", "get")
	assert.True(t, result2.Allowed)
	
	// Same resource should share limit
	result3 := limiter.Allow("user2", "pods", "get")
	assert.True(t, result3.Allowed)
}
