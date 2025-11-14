package httpclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/verticedev/vcli-go/internal/errors"
)

// Client is a composable HTTP client with retry and circuit breaker
type Client struct {
	BaseURL    string
	HTTPClient *http.Client
	Retrier    *Retrier
	Breaker    *CircuitBreaker
	Logger     *log.Logger
	Headers    map[string]string
}

// ClientConfig holds configuration for HTTP client
type ClientConfig struct {
	BaseURL       string
	Timeout       time.Duration
	RetryConfig   RetryConfig
	BreakerConfig BreakerConfig
	Headers       map[string]string
}

// DefaultClientConfig returns conservative defaults
func DefaultClientConfig(baseURL string) ClientConfig {
	return ClientConfig{
		BaseURL:       baseURL,
		Timeout:       30 * time.Second,
		RetryConfig:   DefaultRetryConfig(),
		BreakerConfig: DefaultBreakerConfig(),
		Headers:       make(map[string]string),
	}
}

// NewClient creates a new HTTP client
func NewClient(config ClientConfig) *Client {
	if config.Headers == nil {
		config.Headers = make(map[string]string)
	}

	// Set default headers
	if config.Headers["Content-Type"] == "" {
		config.Headers["Content-Type"] = "application/json"
	}
	if config.Headers["Accept"] == "" {
		config.Headers["Accept"] = "application/json"
	}
	if config.Headers["User-Agent"] == "" {
		config.Headers["User-Agent"] = "vcli-go/2.0"
	}

	return &Client{
		BaseURL: config.BaseURL,
		HTTPClient: &http.Client{
			Timeout: config.Timeout,
		},
		Retrier: NewRetrier(config.RetryConfig),
		Breaker: NewCircuitBreaker(config.BreakerConfig),
		Logger:  log.New(io.Discard, "", 0), // Default: no logging
		Headers: config.Headers,
	}
}

// SetLogger sets the logger for the client
func (c *Client) SetLogger(logger *log.Logger) {
	c.Logger = logger
}

// Get performs a GET request
func (c *Client) Get(ctx context.Context, path string) ([]byte, error) {
	return c.DoRequest(ctx, "GET", path, nil)
}

// Post performs a POST request
func (c *Client) Post(ctx context.Context, path string, body []byte) ([]byte, error) {
	return c.DoRequest(ctx, "POST", path, body)
}

// PostJSON performs a POST request with JSON payload
func (c *Client) PostJSON(ctx context.Context, path string, payload interface{}) ([]byte, error) {
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, errors.Wrap(err, errors.ErrorTypeValidation, "failed to marshal JSON")
	}
	return c.Post(ctx, path, body)
}

// Put performs a PUT request
func (c *Client) Put(ctx context.Context, path string, body []byte) ([]byte, error) {
	return c.DoRequest(ctx, "PUT", path, body)
}

// Delete performs a DELETE request
func (c *Client) Delete(ctx context.Context, path string) ([]byte, error) {
	return c.DoRequest(ctx, "DELETE", path, nil)
}

// DoRequest performs an HTTP request with retry and circuit breaker
func (c *Client) DoRequest(ctx context.Context, method, path string, body []byte) ([]byte, error) {
	url := c.BaseURL + path
	startTime := time.Now()

	// Log request start
	c.Logger.Printf("[HTTP] %s %s", method, url)

	// Execute through circuit breaker and retrier
	result, err := c.Breaker.CallWithResult(func() (interface{}, error) {
		return c.Retrier.DoWithResult(ctx, func() (interface{}, error) {
			return c.executeRequest(ctx, method, url, body)
		})
	})

	elapsed := time.Since(startTime)

	if err != nil {
		c.Logger.Printf("[HTTP] %s %s - FAILED after %v: %v", method, url, elapsed, err)
		return nil, err
	}

	responseBody := result.([]byte)
	c.Logger.Printf("[HTTP] %s %s - SUCCESS in %v (%d bytes)", method, url, elapsed, len(responseBody))

	return responseBody, nil
}

// executeRequest performs the actual HTTP request (single attempt)
func (c *Client) executeRequest(ctx context.Context, method, url string, body []byte) ([]byte, error) {
	// Create request
	var bodyReader io.Reader
	if body != nil {
		bodyReader = bytes.NewReader(body)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, bodyReader)
	if err != nil {
		return nil, errors.Wrap(err, errors.ErrorTypeInternal, "failed to create request")
	}

	// Set headers
	for key, value := range c.Headers {
		req.Header.Set(key, value)
	}

	// Execute request
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		// Network error (retryable)
		return nil, errors.Wrap(err, errors.ErrorTypeNetwork, "network request failed")
	}
	defer resp.Body.Close()

	// Read response body
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, errors.Wrap(err, errors.ErrorTypeNetwork, "failed to read response body")
	}

	// Check status code
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		httpErr := errors.NewHTTPError(resp.StatusCode, string(responseBody))
		return nil, httpErr
	}

	return responseBody, nil
}

// GetJSON performs a GET request and unmarshals JSON response
func (c *Client) GetJSON(ctx context.Context, path string, result interface{}) error {
	body, err := c.Get(ctx, path)
	if err != nil {
		return err
	}

	if err := json.Unmarshal(body, result); err != nil {
		return errors.Wrap(err, errors.ErrorTypeInternal, "failed to unmarshal JSON response")
	}

	return nil
}

// PostJSONResponse performs a POST request and unmarshals JSON response
func (c *Client) PostJSONResponse(ctx context.Context, path string, payload, result interface{}) error {
	body, err := c.PostJSON(ctx, path, payload)
	if err != nil {
		return err
	}

	if err := json.Unmarshal(body, result); err != nil {
		return errors.Wrap(err, errors.ErrorTypeInternal, "failed to unmarshal JSON response")
	}

	return nil
}

// HealthCheck performs a health check request
func (c *Client) HealthCheck(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	_, err := c.Get(ctx, "/health")
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	return nil
}

// GetCircuitBreakerState returns current circuit breaker state
func (c *Client) GetCircuitBreakerState() string {
	return c.Breaker.GetState().String()
}

// ResetCircuitBreaker resets the circuit breaker
func (c *Client) ResetCircuitBreaker() {
	c.Breaker.Reset()
}
