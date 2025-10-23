package oraculo

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"
)

// CircuitState represents the state of the circuit breaker
type CircuitState int

const (
	CircuitClosed CircuitState = iota
	CircuitOpen
	CircuitHalfOpen
)

// cacheEntry represents a cached code generation result
type cacheEntry struct {
	response  *ImplementationResponse
	timestamp time.Time
}

// Client represents an HTTP client for MAXIMUS Oraculo Service
type Client struct {
	baseURL    string
	httpClient *http.Client
	authToken  string

	// Retry configuration
	maxRetries     int
	retryDelay     time.Duration
	retryBackoff   float64

	// Circuit breaker
	mu                sync.RWMutex
	circuitState      CircuitState
	failureCount      int
	successCount      int
	lastFailureTime   time.Time
	failureThreshold  int
	successThreshold  int
	openTimeout       time.Duration

	// Cache
	cache         map[string]*cacheEntry
	cacheEnabled  bool
	cacheTTL      time.Duration
	cacheHits     int64
	cacheMisses   int64

	// Metrics
	totalRequests    int64
	failedRequests   int64
	retriedRequests  int64
}

// ClientOption configures the Oraculo client
type ClientOption func(*Client)

// WithRetry configures retry behavior
func WithRetry(maxRetries int, delay time.Duration, backoff float64) ClientOption {
	return func(c *Client) {
		c.maxRetries = maxRetries
		c.retryDelay = delay
		c.retryBackoff = backoff
	}
}

// WithCircuitBreaker configures circuit breaker
func WithCircuitBreaker(failureThreshold, successThreshold int, openTimeout time.Duration) ClientOption {
	return func(c *Client) {
		c.failureThreshold = failureThreshold
		c.successThreshold = successThreshold
		c.openTimeout = openTimeout
	}
}

// WithCache enables in-memory caching with specified TTL
func WithCache(ttl time.Duration) ClientOption {
	return func(c *Client) {
		c.cacheEnabled = true
		c.cacheTTL = ttl
		c.cache = make(map[string]*cacheEntry)
	}
}

// NewClient creates a new Oraculo API client
func NewClient(baseURL, authToken string, opts ...ClientOption) *Client {
	c := &Client{
		baseURL:   baseURL,
		authToken: authToken,
		httpClient: &http.Client{
			Timeout: 60 * time.Second, // AI code generation can take time
		},
		// Default retry config
		maxRetries:   3,
		retryDelay:   1 * time.Second,
		retryBackoff: 2.0,
		// Default circuit breaker config
		circuitState:     CircuitClosed,
		failureThreshold: 5,
		successThreshold: 2,
		openTimeout:      30 * time.Second,
	}

	// Apply options
	for _, opt := range opts {
		opt(c)
	}

	return c
}

// ImplementationRequest represents a request to auto-implement code
type ImplementationRequest struct {
	TaskDescription string                 `json:"task_description"`
	Context         map[string]interface{} `json:"context,omitempty"`
	TargetLanguage  string                 `json:"target_language"`
}

// ImplementationResponse represents the response from auto-implement endpoint
type ImplementationResponse struct {
	Status    string    `json:"status"`
	Timestamp string    `json:"timestamp"`
	Result    ImplResult `json:"implementation_result"`
}

// ImplResult contains the generated code and implementation details
type ImplResult struct {
	GeneratedCode string        `json:"generated_code"`
	Details       ImplDetails   `json:"details"`
}

// ImplDetails contains metadata about the implementation
type ImplDetails struct {
	Status      string                 `json:"status"`
	Message     string                 `json:"message"`
	Language    string                 `json:"language"`
	ContextUsed map[string]interface{} `json:"context_used,omitempty"`
}

// AutoImplement requests code implementation from Oraculo with retry and circuit breaker
func (c *Client) AutoImplement(ctx context.Context, req ImplementationRequest) (*ImplementationResponse, error) {
	c.mu.Lock()
	c.totalRequests++
	c.mu.Unlock()

	// Check cache first
	if c.cacheEnabled {
		if cached := c.getFromCache(req); cached != nil {
			c.mu.Lock()
			c.cacheHits++
			c.mu.Unlock()
			return cached, nil
		}
		c.mu.Lock()
		c.cacheMisses++
		c.mu.Unlock()
	}

	// Check circuit breaker state
	if err := c.checkCircuitBreaker(); err != nil {
		c.mu.Lock()
		c.failedRequests++
		c.mu.Unlock()
		return nil, err
	}

	var lastErr error
	currentDelay := c.retryDelay

	// Retry loop with exponential backoff
	for attempt := 0; attempt <= c.maxRetries; attempt++ {
		if attempt > 0 {
			c.mu.Lock()
			c.retriedRequests++
			c.mu.Unlock()

			// Wait with exponential backoff
			select {
			case <-ctx.Done():
				return nil, fmt.Errorf("context cancelled during retry: %w", ctx.Err())
			case <-time.After(currentDelay):
				currentDelay = time.Duration(float64(currentDelay) * c.retryBackoff)
			}
		}

		// Execute request
		resp, err := c.executeAutoImplement(ctx, req)
		if err == nil {
			// Success - record and cache
			c.recordSuccess()
			if c.cacheEnabled {
				c.putInCache(req, resp)
			}
			return resp, nil
		}

		lastErr = err

		// Check if error is retryable
		if !c.isRetryableError(err) {
			break
		}
	}

	// All retries exhausted - record failure
	c.recordFailure()
	c.mu.Lock()
	c.failedRequests++
	c.mu.Unlock()

	return nil, fmt.Errorf("all %d retry attempts failed: %w", c.maxRetries, lastErr)
}

// executeAutoImplement performs the actual HTTP request
func (c *Client) executeAutoImplement(ctx context.Context, req ImplementationRequest) (*ImplementationResponse, error) {
	// Build request body
	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		fmt.Sprintf("%s/auto_implement", c.baseURL),
		bytes.NewReader(reqBody),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	httpReq.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	// Execute request
	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer httpResp.Body.Close()

	// Read response body
	respBody, err := io.ReadAll(httpResp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if httpResp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("oraculo returned error status %d: %s", httpResp.StatusCode, string(respBody))
	}

	// Parse response
	var resp ImplementationResponse
	if err := json.Unmarshal(respBody, &resp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &resp, nil
}

// Circuit breaker methods

func (c *Client) checkCircuitBreaker() error {
	c.mu.RLock()
	state := c.circuitState
	lastFailure := c.lastFailureTime
	c.mu.RUnlock()

	switch state {
	case CircuitOpen:
		// Check if we should transition to half-open
		if time.Since(lastFailure) > c.openTimeout {
			c.mu.Lock()
			c.circuitState = CircuitHalfOpen
			c.successCount = 0
			c.mu.Unlock()
			return nil
		}
		return fmt.Errorf("circuit breaker is OPEN (service unavailable)")
	case CircuitHalfOpen:
		// Allow request through in half-open state
		return nil
	default: // CircuitClosed
		return nil
	}
}

func (c *Client) recordSuccess() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.failureCount = 0

	if c.circuitState == CircuitHalfOpen {
		c.successCount++
		if c.successCount >= c.successThreshold {
			// Transition to closed
			c.circuitState = CircuitClosed
			c.successCount = 0
		}
	}
}

func (c *Client) recordFailure() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.failureCount++
	c.lastFailureTime = time.Now()

	if c.circuitState == CircuitHalfOpen {
		// Transition back to open
		c.circuitState = CircuitOpen
		c.successCount = 0
	} else if c.failureCount >= c.failureThreshold {
		// Transition to open
		c.circuitState = CircuitOpen
	}
}

func (c *Client) isRetryableError(err error) bool {
	// Network errors and 5xx errors are retryable
	// 4xx errors (bad request) are not retryable
	if err == nil {
		return false
	}
	// For now, retry all errors except context errors
	errStr := err.Error()
	return errStr != "context cancelled during retry: context canceled"
}

// Cache methods

func (c *Client) getCacheKey(req ImplementationRequest) string {
	// Create deterministic cache key from request
	h := sha256.New()
	h.Write([]byte(req.TaskDescription))
	h.Write([]byte(req.TargetLanguage))
	// Add context to key if present
	if req.Context != nil {
		contextJSON, _ := json.Marshal(req.Context)
		h.Write(contextJSON)
	}
	return fmt.Sprintf("%x", h.Sum(nil))
}

func (c *Client) getFromCache(req ImplementationRequest) *ImplementationResponse {
	c.mu.RLock()
	defer c.mu.RUnlock()

	key := c.getCacheKey(req)
	entry, exists := c.cache[key]
	if !exists {
		return nil
	}

	// Check if entry expired
	if time.Since(entry.timestamp) > c.cacheTTL {
		// Entry expired - remove it
		delete(c.cache, key)
		return nil
	}

	return entry.response
}

func (c *Client) putInCache(req ImplementationRequest, resp *ImplementationResponse) {
	c.mu.Lock()
	defer c.mu.Unlock()

	key := c.getCacheKey(req)
	c.cache[key] = &cacheEntry{
		response:  resp,
		timestamp: time.Now(),
	}
}

// ClearCache removes all cached entries
func (c *Client) ClearCache() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.cache = make(map[string]*cacheEntry)
	c.cacheHits = 0
	c.cacheMisses = 0
}

// GetMetrics returns current client metrics
func (c *Client) GetMetrics() map[string]int64 {
	c.mu.RLock()
	defer c.mu.RUnlock()

	metrics := map[string]int64{
		"total_requests":   c.totalRequests,
		"failed_requests":  c.failedRequests,
		"retried_requests": c.retriedRequests,
	}

	if c.cacheEnabled {
		metrics["cache_hits"] = c.cacheHits
		metrics["cache_misses"] = c.cacheMisses
		metrics["cache_size"] = int64(len(c.cache))
	}

	return metrics
}

// GetCircuitState returns the current circuit breaker state
func (c *Client) GetCircuitState() string {
	c.mu.RLock()
	defer c.mu.RUnlock()

	switch c.circuitState {
	case CircuitOpen:
		return "OPEN"
	case CircuitHalfOpen:
		return "HALF_OPEN"
	default:
		return "CLOSED"
	}
}

// HealthCheck checks if Oraculo service is healthy
func (c *Client) HealthCheck(ctx context.Context) error {
	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodGet,
		fmt.Sprintf("%s/health", c.baseURL),
		nil,
	)
	if err != nil {
		return fmt.Errorf("failed to create health check request: %w", err)
	}

	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return fmt.Errorf("health check returned status %d", httpResp.StatusCode)
	}

	return nil
}
