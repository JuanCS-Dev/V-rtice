//go:build integration
// +build integration

package integration

import (
	"context"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/verticedev/vcli-go/internal/security"
	"github.com/verticedev/vcli-go/internal/security/auth"
)

func TestDay1_GuardianWithAuthLayer(t *testing.T) {
	// Setup
	jwtSecret := []byte("test-secret-day1")
	authLayer := auth.NewAuthLayer(jwtSecret, 24*time.Hour)

	// Create Guardian (with nil for unimplemented layers)
	guardian := security.NewGuardian(
		authLayer,
		nil, // authz - Day 3
		nil, // sandbox - Day 4-5
		nil, // intent - Day 5-7
		nil, // flow - Day 8-9
		nil, // behavioral - Day 10-12
		nil, // audit - Day 13-14
		nil, // parser - will integrate later
	)

	// Create valid token
	token := createTestToken(t, jwtSecret, "user-day1", []string{"admin"})

	// Parse request
	req := &security.ParseRequest{
		Input: "show pods",
		Token: token,
		ClientContext: &security.ClientContext{
			IP:        "127.0.0.1",
			UserAgent: "vcli-test",
			Timestamp: time.Now(),
		},
	}

	ctx := context.Background()
	result, err := guardian.ParseSecure(ctx, req)

	// Validate
	require.NoError(t, err)
	assert.NotNil(t, result)
	assert.True(t, result.SecurityDecision.Authenticated)
	assert.NotNil(t, result.User)
	assert.Equal(t, "user-day1", result.User.Username)
	assert.Contains(t, result.User.Roles, "admin")
}

func TestDay1_GuardianWithInvalidToken(t *testing.T) {
	// Setup
	jwtSecret := []byte("test-secret-day1")
	authLayer := auth.NewAuthLayer(jwtSecret, 24*time.Hour)

	guardian := security.NewGuardian(
		authLayer,
		nil, nil, nil, nil, nil, nil, nil,
	)

	// Parse request with invalid token
	req := &security.ParseRequest{
		Input: "show pods",
		Token: "invalid-token",
		ClientContext: &security.ClientContext{
			IP:        "127.0.0.1",
			UserAgent: "vcli-test",
			Timestamp: time.Now(),
		},
	}

	ctx := context.Background()
	result, err := guardian.ParseSecure(ctx, req)

	// Should fail authentication
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "authentication failed")
}

func TestDay1_GuardianWithExpiredToken(t *testing.T) {
	// Setup
	jwtSecret := []byte("test-secret-day1")
	authLayer := auth.NewAuthLayer(jwtSecret, 24*time.Hour)

	guardian := security.NewGuardian(
		authLayer,
		nil, nil, nil, nil, nil, nil, nil,
	)

	// Create expired token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id":  "user-day1",
		"username": "testuser",
		"exp":      time.Now().Add(-1 * time.Hour).Unix(), // Expired
	})
	tokenString, err := token.SignedString(jwtSecret)
	require.NoError(t, err)

	// Parse request
	req := &security.ParseRequest{
		Input: "show pods",
		Token: tokenString,
		ClientContext: &security.ClientContext{
			IP:        "127.0.0.1",
			UserAgent: "vcli-test",
			Timestamp: time.Now(),
		},
	}

	ctx := context.Background()
	result, err := guardian.ParseSecure(ctx, req)

	// Should fail authentication
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "expired")
}

func createTestToken(t *testing.T, secret []byte, username string, roles []string) string {
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id":     "test-" + username,
		"username":    username,
		"email":       username + "@test.com",
		"roles":       roles,
		"mfa_enabled": false,
		"exp":         time.Now().Add(1 * time.Hour).Unix(),
	})
	tokenString, err := token.SignedString(secret)
	require.NoError(t, err)
	return tokenString
}
