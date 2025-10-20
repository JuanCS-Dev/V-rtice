// Package flow_control - Layer 5: Flow Control (Rate Limiting)
//
// Prevents abuse through rate limiting
package flow_control

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// FlowControlLayer implements rate limiting
type FlowControlLayer interface {
	// CheckRate validates if request is within rate limits
	CheckRate(ctx context.Context, userID string, action string) (*RateDecision, error)
}

// RateDecision represents rate limit check result
type RateDecision struct {
	Allowed       bool
	Reason        string
	RetryAfter    time.Duration
	RemainingCall int
}

// RateLimit defines limits per action type
type RateLimit struct {
	MaxRequests int
	Window      time.Duration
}

type flowController struct {
	mu      sync.RWMutex
	buckets map[string]*rateBucket // userID:action -> bucket
	limits  map[string]RateLimit   // action -> limit
}

type rateBucket struct {
	requests  int
	resetTime time.Time
}

// NewFlowController creates flow control layer
func NewFlowController() FlowControlLayer {
	return &flowController{
		buckets: make(map[string]*rateBucket),
		limits:  initDefaultLimits(),
	}
}

// CheckRate implements FlowControlLayer
func (f *flowController) CheckRate(ctx context.Context, userID string, action string) (*RateDecision, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	key := fmt.Sprintf("%s:%s", userID, action)
	limit, exists := f.limits[action]
	if !exists {
		limit = f.limits["default"]
	}

	bucket, exists := f.buckets[key]
	now := time.Now()

	if !exists || now.After(bucket.resetTime) {
		// Create new bucket
		f.buckets[key] = &rateBucket{
			requests:  1,
			resetTime: now.Add(limit.Window),
		}

		return &RateDecision{
			Allowed:       true,
			Reason:        "Within rate limit",
			RemainingCall: limit.MaxRequests - 1,
		}, nil
	}

	// Check if limit exceeded
	if bucket.requests >= limit.MaxRequests {
		retryAfter := bucket.resetTime.Sub(now)
		return &RateDecision{
			Allowed:       false,
			Reason:        fmt.Sprintf("Rate limit exceeded (%d/%d)", bucket.requests, limit.MaxRequests),
			RetryAfter:    retryAfter,
			RemainingCall: 0,
		}, nil
	}

	// Increment counter
	bucket.requests++

	return &RateDecision{
		Allowed:       true,
		Reason:        "Within rate limit",
		RemainingCall: limit.MaxRequests - bucket.requests,
	}, nil
}

// initDefaultLimits sets up rate limits
func initDefaultLimits() map[string]RateLimit {
	return map[string]RateLimit{
		"default": {
			MaxRequests: 100,
			Window:      1 * time.Minute,
		},
		"search": {
			MaxRequests: 30,
			Window:      1 * time.Minute,
		},
		"execute": {
			MaxRequests: 20,
			Window:      1 * time.Minute,
		},
		"delete": {
			MaxRequests: 10,
			Window:      1 * time.Minute,
		},
	}
}

