// Package auth - Redis Client Implementation
//
// Lead Architect: Juan Carlos de Souza
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Production-ready Redis client with connection pooling and error handling
package auth

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/redis/go-redis/v9"
)

// RedisConfig holds Redis connection configuration
type RedisConfig struct {
	Addr         string        // Redis server address (host:port)
	Password     string        // Optional password
	DB           int           // Database number (0-15)
	MaxRetries   int           // Max retries for failed commands
	DialTimeout  time.Duration // Connection timeout
	ReadTimeout  time.Duration // Read timeout
	WriteTimeout time.Duration // Write timeout
	PoolSize     int           // Connection pool size
	MinIdleConns int           // Minimum idle connections
}

// DefaultRedisConfig returns production-ready defaults
func DefaultRedisConfig() RedisConfig {
	return RedisConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           0,
		MaxRetries:   3,
		DialTimeout:  5 * time.Second,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
		PoolSize:     10,
		MinIdleConns: 2,
	}
}

// MockRedisClient implements RedisClient for testing
type MockRedisClient struct {
	data   map[string]string
	errors map[string]error // Inject errors for specific keys
}

// NewMockRedisClient creates a mock Redis client for testing
func NewMockRedisClient() *MockRedisClient {
	return &MockRedisClient{
		data:   make(map[string]string),
		errors: make(map[string]error),
	}
}

// Set implements RedisClient
func (m *MockRedisClient) Set(ctx context.Context, key string, value string, expiration time.Duration) error {
	if err, exists := m.errors[key]; exists {
		return err
	}
	m.data[key] = value
	return nil
}

// Get implements RedisClient
func (m *MockRedisClient) Get(ctx context.Context, key string) (string, error) {
	if err, exists := m.errors[key]; exists {
		return "", err
	}
	val, exists := m.data[key]
	if !exists {
		return "", fmt.Errorf("key not found")
	}
	return val, nil
}

// Del implements RedisClient
func (m *MockRedisClient) Del(ctx context.Context, keys ...string) error {
	for _, key := range keys {
		if err, exists := m.errors[key]; exists {
			return err
		}
		delete(m.data, key)
	}
	return nil
}

// Keys implements RedisClient
func (m *MockRedisClient) Keys(ctx context.Context, pattern string) ([]string, error) {
	keys := make([]string, 0, len(m.data))
	for k := range m.data {
		keys = append(keys, k)
	}
	return keys, nil
}

// Close implements RedisClient
func (m *MockRedisClient) Close() error {
	return nil
}

// InjectError injects an error for testing
func (m *MockRedisClient) InjectError(key string, err error) {
	m.errors[key] = err
}

// Clear clears all data (for testing)
func (m *MockRedisClient) Clear() {
	m.data = make(map[string]string)
	m.errors = make(map[string]error)
}

// RealRedisClient implements RedisClient using actual Redis connection
type RealRedisClient struct {
	client *redis.Client
}

// NewRealRedisClient creates a production Redis client with connection pooling
func NewRealRedisClient(config RedisConfig) (*RealRedisClient, error) {
	debug := os.Getenv("VCLI_DEBUG") == "true"

	if debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] Redis client connecting to %s\n", config.Addr)
	}

	client := redis.NewClient(&redis.Options{
		Addr:         config.Addr,
		Password:     config.Password,
		DB:           config.DB,
		MaxRetries:   config.MaxRetries,
		DialTimeout:  config.DialTimeout,
		ReadTimeout:  config.ReadTimeout,
		WriteTimeout: config.WriteTimeout,
		PoolSize:     config.PoolSize,
		MinIdleConns: config.MinIdleConns,
	})

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("redis connection failed at %s: %w", config.Addr, err)
	}

	if debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] Redis connection established\n")
	}

	return &RealRedisClient{client: client}, nil
}

// Set implements RedisClient
func (r *RealRedisClient) Set(ctx context.Context, key string, value string, expiration time.Duration) error {
	return r.client.Set(ctx, key, value, expiration).Err()
}

// Get implements RedisClient
func (r *RealRedisClient) Get(ctx context.Context, key string) (string, error) {
	val, err := r.client.Get(ctx, key).Result()
	if err == redis.Nil {
		return "", fmt.Errorf("key not found")
	}
	return val, err
}

// Del implements RedisClient
func (r *RealRedisClient) Del(ctx context.Context, keys ...string) error {
	return r.client.Del(ctx, keys...).Err()
}

// Keys implements RedisClient
func (r *RealRedisClient) Keys(ctx context.Context, pattern string) ([]string, error) {
	return r.client.Keys(ctx, pattern).Result()
}

// Close implements RedisClient
func (r *RealRedisClient) Close() error {
	return r.client.Close()
}

// NewRedisClient creates appropriate Redis client based on environment
// If VCLI_REDIS_MOCK=true, returns MockRedisClient (for dev/testing)
// Otherwise, returns RealRedisClient with connection to Redis server
func NewRedisClient() (RedisClient, error) {
	// Check if mock mode is enabled
	if os.Getenv("VCLI_REDIS_MOCK") == "true" {
		if os.Getenv("VCLI_DEBUG") == "true" {
			fmt.Fprintf(os.Stderr, "[DEBUG] Using mock Redis client (dev mode)\n")
		}
		return NewMockRedisClient(), nil
	}

	// Production mode - connect to real Redis
	config := DefaultRedisConfig()

	// Override with env vars if provided
	if addr := os.Getenv("VCLI_REDIS_ADDR"); addr != "" {
		config.Addr = addr
	}
	if password := os.Getenv("VCLI_REDIS_PASSWORD"); password != "" {
		config.Password = password
	}

	return NewRealRedisClient(config)
}
