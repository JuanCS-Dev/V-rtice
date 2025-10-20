// Package auth - Token Store Tests
package auth

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestInMemoryTokenStore_RevokeAndCheck(t *testing.T) {
	store := NewInMemoryTokenStore(1 * time.Second)
	defer store.Close()

	ctx := context.Background()
	tokenID := "test-token-123"
	expiresAt := time.Now().Add(1 * time.Hour)

	// Token should not be revoked initially
	revoked, err := store.IsRevoked(ctx, tokenID)
	require.NoError(t, err)
	assert.False(t, revoked)

	// Revoke token
	err = store.RevokeToken(ctx, tokenID, expiresAt)
	require.NoError(t, err)

	// Token should now be revoked
	revoked, err = store.IsRevoked(ctx, tokenID)
	require.NoError(t, err)
	assert.True(t, revoked)

	// Count should be 1
	assert.Equal(t, 1, store.Count())
}

func TestInMemoryTokenStore_ExpiredRevocation(t *testing.T) {
	store := NewInMemoryTokenStore(100 * time.Millisecond)
	defer store.Close()

	ctx := context.Background()
	tokenID := "expired-token"
	expiresAt := time.Now().Add(200 * time.Millisecond)

	// Revoke token
	err := store.RevokeToken(ctx, tokenID, expiresAt)
	require.NoError(t, err)

	// Should be revoked immediately
	revoked, err := store.IsRevoked(ctx, tokenID)
	require.NoError(t, err)
	assert.True(t, revoked)

	// Wait for expiration
	time.Sleep(300 * time.Millisecond)

	// Should no longer be revoked (expired)
	revoked, err = store.IsRevoked(ctx, tokenID)
	require.NoError(t, err)
	assert.False(t, revoked)
}

func TestInMemoryTokenStore_Cleanup(t *testing.T) {
	store := NewInMemoryTokenStore(1 * time.Second)
	defer store.Close()

	ctx := context.Background()

	// Add expired token
	expiredToken := "expired"
	err := store.RevokeToken(ctx, expiredToken, time.Now().Add(-1*time.Hour))
	require.NoError(t, err)

	// Add valid token
	validToken := "valid"
	err = store.RevokeToken(ctx, validToken, time.Now().Add(1*time.Hour))
	require.NoError(t, err)

	// Should have 2 tokens before cleanup
	assert.Equal(t, 2, store.Count())

	// Run cleanup
	err = store.CleanupExpired(ctx)
	require.NoError(t, err)

	// Should have 1 token after cleanup (expired removed)
	assert.Equal(t, 1, store.Count())

	// Valid token should still be revoked
	revoked, err := store.IsRevoked(ctx, validToken)
	require.NoError(t, err)
	assert.True(t, revoked)
}

func TestRedisTokenStore_RevokeAndCheck(t *testing.T) {
	mockClient := NewMockRedisClient()
	store := NewRedisTokenStore(mockClient, "test:")
	defer store.Close()

	ctx := context.Background()
	tokenID := "redis-token-123"
	expiresAt := time.Now().Add(1 * time.Hour)

	// Token should not be revoked initially
	revoked, err := store.IsRevoked(ctx, tokenID)
	require.NoError(t, err)
	assert.False(t, revoked)

	// Revoke token
	err = store.RevokeToken(ctx, tokenID, expiresAt)
	require.NoError(t, err)

	// Token should now be revoked
	revoked, err = store.IsRevoked(ctx, tokenID)
	require.NoError(t, err)
	assert.True(t, revoked)

	// Check metrics
	metrics := store.GetMetrics()
	assert.Equal(t, int64(1), metrics.RevocationCount)
	assert.Equal(t, int64(2), metrics.CheckCount) // 2 checks
	assert.Equal(t, int64(0), metrics.ErrorCount)
}

func TestRedisTokenStore_AlreadyExpired(t *testing.T) {
	mockClient := NewMockRedisClient()
	store := NewRedisTokenStore(mockClient, "test:")
	defer store.Close()

	ctx := context.Background()
	tokenID := "expired-token"
	expiresAt := time.Now().Add(-1 * time.Hour) // Already expired

	// Revoke expired token (should be no-op)
	err := store.RevokeToken(ctx, tokenID, expiresAt)
	require.NoError(t, err)

	// Should not be stored
	count, err := store.Count(ctx)
	require.NoError(t, err)
	assert.Equal(t, 0, count)
}

func TestRedisTokenStore_ErrorHandling(t *testing.T) {
	mockClient := NewMockRedisClient()
	store := NewRedisTokenStore(mockClient, "test:")
	defer store.Close()

	ctx := context.Background()
	tokenID := "error-token"
	expiresAt := time.Now().Add(1 * time.Hour)

	// Inject error
	mockClient.InjectError("test:"+tokenID, assert.AnError)

	// Revoke should fail
	err := store.RevokeToken(ctx, tokenID, expiresAt)
	assert.Error(t, err)

	// Error count should increment
	metrics := store.GetMetrics()
	assert.Equal(t, int64(1), metrics.ErrorCount)
}

func TestRedisTokenStore_CleanupNoOp(t *testing.T) {
	mockClient := NewMockRedisClient()
	store := NewRedisTokenStore(mockClient, "test:")
	defer store.Close()

	ctx := context.Background()

	// Cleanup should be no-op (Redis handles TTL automatically)
	err := store.CleanupExpired(ctx)
	require.NoError(t, err)

	// Should increment cleanup count
	metrics := store.GetMetrics()
	assert.Equal(t, int64(1), metrics.CleanupCount)
}

func TestTokenStore_InterfaceCompliance(t *testing.T) {
	// Ensure both implementations satisfy TokenStore interface
	var _ TokenStore = &InMemoryTokenStore{}
	var _ TokenStore = &RedisTokenStore{}
}

func BenchmarkInMemoryTokenStore_IsRevoked(b *testing.B) {
	store := NewInMemoryTokenStore(1 * time.Minute)
	defer store.Close()

	ctx := context.Background()
	tokenID := "bench-token"
	expiresAt := time.Now().Add(1 * time.Hour)
	_ = store.RevokeToken(ctx, tokenID, expiresAt)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = store.IsRevoked(ctx, tokenID)
	}
}

func BenchmarkRedisTokenStore_IsRevoked(b *testing.B) {
	mockClient := NewMockRedisClient()
	store := NewRedisTokenStore(mockClient, "bench:")
	defer store.Close()

	ctx := context.Background()
	tokenID := "bench-token"
	expiresAt := time.Now().Add(1 * time.Hour)
	_ = store.RevokeToken(ctx, tokenID, expiresAt)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = store.IsRevoked(ctx, tokenID)
	}
}
