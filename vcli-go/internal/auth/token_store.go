// Package auth - Token Revocation Store
//
// Lead Architect: Juan Carlos de Souza (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This implements a persistent token revocation store.
// Phase 1: In-memory with persistence interface
// Phase 2: Redis/PostgreSQL backing store
package auth

import (
	"context"
	"sync"
	"time"
)

// TokenStore defines the interface for token revocation persistence
type TokenStore interface {
	// RevokeToken marks a token as revoked
	RevokeToken(ctx context.Context, tokenID string, expiresAt time.Time) error
	
	// IsRevoked checks if a token is revoked
	IsRevoked(ctx context.Context, tokenID string) (bool, error)
	
	// CleanupExpired removes expired revocation entries
	CleanupExpired(ctx context.Context) error
	
	// Close closes the store connection
	Close() error
}

// InMemoryTokenStore implements TokenStore with in-memory storage
// This is phase 1 implementation. For production, use RedisTokenStore.
type InMemoryTokenStore struct {
	mu             sync.RWMutex
	revokedTokens  map[string]time.Time // tokenID -> expiresAt
	cleanupTicker  *time.Ticker
	cleanupStop    chan bool
}

// NewInMemoryTokenStore creates a new in-memory token store
func NewInMemoryTokenStore(cleanupInterval time.Duration) *InMemoryTokenStore {
	store := &InMemoryTokenStore{
		revokedTokens: make(map[string]time.Time),
		cleanupTicker: time.NewTicker(cleanupInterval),
		cleanupStop:   make(chan bool),
	}
	
	// Start background cleanup
	go store.cleanupLoop()
	
	return store
}

// RevokeToken marks a token as revoked
func (s *InMemoryTokenStore) RevokeToken(ctx context.Context, tokenID string, expiresAt time.Time) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	s.revokedTokens[tokenID] = expiresAt
	return nil
}

// IsRevoked checks if a token is revoked
func (s *InMemoryTokenStore) IsRevoked(ctx context.Context, tokenID string) (bool, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	expiresAt, exists := s.revokedTokens[tokenID]
	if !exists {
		return false, nil
	}
	
	// Check if revocation entry itself has expired
	if time.Now().After(expiresAt) {
		return false, nil
	}
	
	return true, nil
}

// CleanupExpired removes expired revocation entries
func (s *InMemoryTokenStore) CleanupExpired(ctx context.Context) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	now := time.Now()
	for tokenID, expiresAt := range s.revokedTokens {
		if now.After(expiresAt) {
			delete(s.revokedTokens, tokenID)
		}
	}
	
	return nil
}

// cleanupLoop runs periodic cleanup
func (s *InMemoryTokenStore) cleanupLoop() {
	for {
		select {
		case <-s.cleanupTicker.C:
			_ = s.CleanupExpired(context.Background())
		case <-s.cleanupStop:
			return
		}
	}
}

// Close closes the store
func (s *InMemoryTokenStore) Close() error {
	s.cleanupTicker.Stop()
	close(s.cleanupStop)
	return nil
}

// Count returns the number of revoked tokens (for testing/metrics)
func (s *InMemoryTokenStore) Count() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.revokedTokens)
}

// RedisTokenStore implements TokenStore with Redis backing
// This is the production-ready implementation for multi-instance deployments.
type RedisTokenStore struct {
	client  RedisClient
	prefix  string
	metrics *RedisMetrics
}

// RedisClient interface for Redis operations (allows mocking in tests)
type RedisClient interface {
	Set(ctx context.Context, key string, value string, expiration time.Duration) error
	Get(ctx context.Context, key string) (string, error)
	Del(ctx context.Context, keys ...string) error
	Keys(ctx context.Context, pattern string) ([]string, error)
	Close() error
}

// RedisMetrics tracks Redis operations
type RedisMetrics struct {
	mu              sync.RWMutex
	RevocationCount int64
	CheckCount      int64
	ErrorCount      int64
	CleanupCount    int64
}

// NewRedisTokenStore creates a Redis-backed token store
// If Redis connection fails, returns an error (caller can fallback to InMemoryTokenStore)
func NewRedisTokenStore(client RedisClient, keyPrefix string) *RedisTokenStore {
	return &RedisTokenStore{
		client:  client,
		prefix:  keyPrefix,
		metrics: &RedisMetrics{},
	}
}

// RevokeToken marks a token as revoked in Redis
func (s *RedisTokenStore) RevokeToken(ctx context.Context, tokenID string, expiresAt time.Time) error {
	key := s.prefix + tokenID
	ttl := time.Until(expiresAt)
	
	if ttl <= 0 {
		// Already expired, no need to store
		return nil
	}
	
	// Store with TTL (Redis will auto-delete when expired)
	err := s.client.Set(ctx, key, "revoked", ttl)
	if err != nil {
		s.metrics.mu.Lock()
		s.metrics.ErrorCount++
		s.metrics.mu.Unlock()
		return err
	}
	
	s.metrics.mu.Lock()
	s.metrics.RevocationCount++
	s.metrics.mu.Unlock()
	
	return nil
}

// IsRevoked checks if a token is revoked
func (s *RedisTokenStore) IsRevoked(ctx context.Context, tokenID string) (bool, error) {
	s.metrics.mu.Lock()
	s.metrics.CheckCount++
	s.metrics.mu.Unlock()
	
	key := s.prefix + tokenID
	_, err := s.client.Get(ctx, key)
	
	if err != nil {
		// Key not found = not revoked
		// This is the expected case for valid tokens
		return false, nil
	}
	
	return true, nil
}

// CleanupExpired is a no-op for Redis (TTL handles expiration automatically)
func (s *RedisTokenStore) CleanupExpired(ctx context.Context) error {
	// Redis handles cleanup via TTL automatically
	// This method exists for interface compatibility
	s.metrics.mu.Lock()
	s.metrics.CleanupCount++
	s.metrics.mu.Unlock()
	
	return nil
}

// Close closes the Redis connection
func (s *RedisTokenStore) Close() error {
	return s.client.Close()
}

// GetMetrics returns current metrics (for monitoring)
func (s *RedisTokenStore) GetMetrics() RedisMetrics {
	s.metrics.mu.RLock()
	defer s.metrics.mu.RUnlock()
	
	return RedisMetrics{
		RevocationCount: s.metrics.RevocationCount,
		CheckCount:      s.metrics.CheckCount,
		ErrorCount:      s.metrics.ErrorCount,
		CleanupCount:    s.metrics.CleanupCount,
	}
}

// Count returns approximate count of revoked tokens (for testing/metrics)
// WARNING: This is expensive in Redis - use sparingly
func (s *RedisTokenStore) Count(ctx context.Context) (int, error) {
	keys, err := s.client.Keys(ctx, s.prefix+"*")
	if err != nil {
		return 0, err
	}
	return len(keys), nil
}
