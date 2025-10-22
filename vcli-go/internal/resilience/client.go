package resilience

import (
	"context"
	"fmt"
	"os"

	"github.com/verticedev/vcli-go/internal/circuitbreaker"
	"github.com/verticedev/vcli-go/internal/retry"
)

// Client wraps a service with resilience patterns
type Client struct {
	name           string
	circuitBreaker *circuitbreaker.CircuitBreaker
	retryStrategy  *retry.Strategy
	debug          bool
}

// Config holds resilience configuration
type Config struct {
	ServiceName       string
	CircuitBreaker    *circuitbreaker.Config
	RetryStrategy     *retry.Strategy
	EnableDebug       bool
}

// DefaultConfig returns sensible defaults
func DefaultConfig(serviceName string) *Config {
	return &Config{
		ServiceName:    serviceName,
		CircuitBreaker: circuitbreaker.DefaultConfig(),
		RetryStrategy:  retry.DefaultStrategy(),
		EnableDebug:    os.Getenv("VCLI_DEBUG") == "true",
	}
}

// NewClient creates a new resilient client
func NewClient(config *Config) *Client {
	if config == nil {
		config = DefaultConfig("unknown")
	}

	// Add state change logging if debug enabled
	if config.EnableDebug && config.CircuitBreaker != nil {
		config.CircuitBreaker.OnStateChange = func(from, to circuitbreaker.State) {
			fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Circuit breaker state: %s → %s\n",
				config.ServiceName, from, to)
		}
	}

	return &Client{
		name:           config.ServiceName,
		circuitBreaker: circuitbreaker.New(config.CircuitBreaker),
		retryStrategy:  config.RetryStrategy,
		debug:          config.EnableDebug,
	}
}

// Execute runs a function with full resilience: retry + circuit breaker
func (c *Client) Execute(ctx context.Context, fn func() error) error {
	if c.debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Executing with resilience (state=%s)\n",
			c.name, c.circuitBreaker.State())
	}

	// Wrap function with circuit breaker
	wrappedFn := func() error {
		return c.circuitBreaker.Execute(ctx, fn)
	}

	// Execute with retry
	err := c.retryStrategy.DoWithCallback(ctx, wrappedFn, func(attempt retry.Attempt) {
		if c.debug {
			fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Retry attempt %d after %v (error: %v)\n",
				c.name, attempt.Number, attempt.Delay, attempt.Error)
		}
	})

	return err
}

// ExecuteWithResult runs a function with resilience and returns a result
func ExecuteWithResult[T any](ctx context.Context, c *Client, fn func() (T, error)) (T, error) {
	if c.debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Executing with resilience (state=%s)\n",
			c.name, c.circuitBreaker.State())
	}

	// Wrap function with circuit breaker
	wrappedFn := func() (T, error) {
		return circuitbreaker.ExecuteWithResult(ctx, c.circuitBreaker, fn)
	}

	// Execute with retry
	result, err := retry.DoWithResult(ctx, c.retryStrategy, wrappedFn)

	return result, err
}

// CircuitBreakerState returns the current circuit breaker state
func (c *Client) CircuitBreakerState() circuitbreaker.State {
	return c.circuitBreaker.State()
}

// CircuitBreakerStats returns circuit breaker statistics
func (c *Client) CircuitBreakerStats() circuitbreaker.Stats {
	return c.circuitBreaker.Stats()
}

// Reset resets the circuit breaker
func (c *Client) Reset() {
	c.circuitBreaker.Reset()
	if c.debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Circuit breaker reset\n", c.name)
	}
}

// WithoutRetry creates a copy of the client without retry
func (c *Client) WithoutRetry() *Client {
	return &Client{
		name:           c.name,
		circuitBreaker: c.circuitBreaker,
		retryStrategy:  &retry.Strategy{MaxAttempts: 1},
		debug:          c.debug,
	}
}

// WithRetryStrategy creates a copy with a custom retry strategy
func (c *Client) WithRetryStrategy(strategy *retry.Strategy) *Client {
	return &Client{
		name:           c.name,
		circuitBreaker: c.circuitBreaker,
		retryStrategy:  strategy,
		debug:          c.debug,
	}
}
