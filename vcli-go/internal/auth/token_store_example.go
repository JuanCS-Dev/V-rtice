// Package auth - TokenStore Usage Examples
//
// This file demonstrates how to use TokenStore in production
package auth

import (
	"context"
	"fmt"
	"time"
)

// Example 1: Single-instance deployment (development/small deployments)
func ExampleInMemoryTokenStore() {
	// Create in-memory store with 5-minute cleanup interval
	store := NewInMemoryTokenStore(5 * time.Minute)
	defer store.Close()

	ctx := context.Background()

	// Revoke a token
	tokenID := "user-123-token-abc"
	expiresAt := time.Now().Add(24 * time.Hour)
	err := store.RevokeToken(ctx, tokenID, expiresAt)
	if err != nil {
		fmt.Printf("Error revoking token: %v\n", err)
		return
	}

	// Check if token is revoked
	revoked, err := store.IsRevoked(ctx, tokenID)
	if err != nil {
		fmt.Printf("Error checking token: %v\n", err)
		return
	}

	if revoked {
		fmt.Println("Token is revoked - access denied")
	} else {
		fmt.Println("Token is valid - access granted")
	}

	// Get metrics
	count := store.Count()
	fmt.Printf("Currently tracking %d revoked tokens\n", count)
}

// Example 2: Multi-instance deployment with Redis (production)
func ExampleRedisTokenStore() {
	// In production, use real Redis client
	// For this example, we use mock
	redisClient := NewMockRedisClient()
	
	store := NewRedisTokenStore(redisClient, "vcli:revoked:")
	defer store.Close()

	ctx := context.Background()

	// Revoke a token (stored in Redis)
	tokenID := "user-456-token-xyz"
	expiresAt := time.Now().Add(24 * time.Hour)
	err := store.RevokeToken(ctx, tokenID, expiresAt)
	if err != nil {
		fmt.Printf("Error revoking token: %v\n", err)
		return
	}

	// Check if token is revoked (works across all instances)
	revoked, err := store.IsRevoked(ctx, tokenID)
	if err != nil {
		fmt.Printf("Error checking token: %v\n", err)
		return
	}

	if revoked {
		fmt.Println("Token is revoked - access denied")
	}

	// Get metrics
	metrics := store.GetMetrics()
	fmt.Printf("Revocations: %d, Checks: %d, Errors: %d\n",
		metrics.RevocationCount,
		metrics.CheckCount,
		metrics.ErrorCount,
	)
}

// Example 3: Graceful fallback pattern (production best practice)
func ExampleGracefulFallback() {
	ctx := context.Background()

	// Try to connect to Redis
	var store TokenStore
	
	// In production:
	// redisClient, err := NewRealRedisClient(DefaultRedisConfig())
	// For this example:
	redisClient := NewMockRedisClient()
	err := error(nil) // Simulate success
	
	if err != nil {
		// Redis unavailable - fallback to in-memory
		fmt.Println("⚠️  Redis unavailable - using in-memory store (single instance only)")
		store = NewInMemoryTokenStore(5 * time.Minute)
	} else {
		// Redis available - use it
		fmt.Println("✅ Redis connected - using distributed store")
		store = NewRedisTokenStore(redisClient, "vcli:revoked:")
	}
	defer store.Close()

	// Use store transparently (same interface)
	tokenID := "user-789-token-def"
	expiresAt := time.Now().Add(1 * time.Hour)
	
	_ = store.RevokeToken(ctx, tokenID, expiresAt)
	revoked, _ := store.IsRevoked(ctx, tokenID)
	
	if revoked {
		fmt.Println("Token revoked successfully")
	}
}

// Example 4: Integration with JWT validator
func ExampleIntegrationWithJWT() {
	store := NewInMemoryTokenStore(5 * time.Minute)
	defer store.Close()

	ctx := context.Background()

	// When user logs out, revoke their token
	logoutHandler := func(tokenID string, expiresAt time.Time) error {
		return store.RevokeToken(ctx, tokenID, expiresAt)
	}

	// When validating JWT, check if revoked
	validateToken := func(tokenID string) (bool, error) {
		// First check if revoked
		revoked, err := store.IsRevoked(ctx, tokenID)
		if err != nil {
			return false, err
		}
		if revoked {
			return false, fmt.Errorf("token has been revoked")
		}

		// Then validate JWT signature, expiry, etc.
		// ... JWT validation logic ...

		return true, nil
	}

	// Usage
	tokenID := "user-token-123"
	expiresAt := time.Now().Add(24 * time.Hour)

	// User logs out
	err := logoutHandler(tokenID, expiresAt)
	if err != nil {
		fmt.Printf("Logout failed: %v\n", err)
		return
	}

	// Try to use token (should fail)
	valid, err := validateToken(tokenID)
	if !valid {
		fmt.Println("Token validation failed - user logged out")
	}
}

// Example 5: Performance monitoring
func ExampleMetricsMonitoring() {
	redisClient := NewMockRedisClient()
	store := NewRedisTokenStore(redisClient, "vcli:")
	defer store.Close()

	ctx := context.Background()

	// Simulate operations
	for i := 0; i < 100; i++ {
		tokenID := fmt.Sprintf("token-%d", i)
		expiresAt := time.Now().Add(1 * time.Hour)
		_ = store.RevokeToken(ctx, tokenID, expiresAt)
		_, _ = store.IsRevoked(ctx, tokenID)
	}

	// Get metrics
	metrics := store.GetMetrics()
	
	fmt.Println("=== TokenStore Metrics ===")
	fmt.Printf("Revocations: %d\n", metrics.RevocationCount)
	fmt.Printf("Checks: %d\n", metrics.CheckCount)
	fmt.Printf("Errors: %d\n", metrics.ErrorCount)
	fmt.Printf("Cleanups: %d\n", metrics.CleanupCount)
	
	if metrics.ErrorCount > 0 {
		errorRate := float64(metrics.ErrorCount) / float64(metrics.CheckCount) * 100
		fmt.Printf("⚠️  Error rate: %.2f%%\n", errorRate)
	}
}
