package auth

import (
	"context"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestAuthLayer_ValidateToken_Success(t *testing.T) {
	secret := []byte("test-secret")
	layer := NewAuthLayer(secret, 24*time.Hour)

	// Create valid token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id":     "user-123",
		"username":    "testuser",
		"email":       "test@example.com",
		"roles":       []string{"admin"},
		"mfa_enabled": true,
		"exp":         time.Now().Add(1 * time.Hour).Unix(),
	})
	tokenString, err := token.SignedString(secret)
	require.NoError(t, err)

	// Validate
	ctx := context.Background()
	user, err := layer.ValidateToken(ctx, tokenString)

	assert.NoError(t, err)
	assert.NotNil(t, user)
	assert.Equal(t, "user-123", user.UserID)
	assert.Equal(t, "testuser", user.Username)
	assert.Equal(t, "test@example.com", user.Email)
	assert.Contains(t, user.Roles, "admin")
	assert.True(t, user.MFAEnabled)
}

func TestAuthLayer_ValidateToken_Expired(t *testing.T) {
	secret := []byte("test-secret")
	layer := NewAuthLayer(secret, 24*time.Hour)

	// Create expired token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id": "user-123",
		"exp":     time.Now().Add(-1 * time.Hour).Unix(), // Expired
	})
	tokenString, err := token.SignedString(secret)
	require.NoError(t, err)

	// Validate
	ctx := context.Background()
	user, err := layer.ValidateToken(ctx, tokenString)

	assert.Error(t, err)
	assert.Nil(t, user)
	assert.Contains(t, err.Error(), "expired")
}

func TestAuthLayer_ValidateToken_Invalid(t *testing.T) {
	secret := []byte("test-secret")
	layer := NewAuthLayer(secret, 24*time.Hour)

	// Invalid token string
	ctx := context.Background()
	user, err := layer.ValidateToken(ctx, "invalid-token")

	assert.Error(t, err)
	assert.Nil(t, user)
}

func TestAuthLayer_ValidateToken_WrongSecret(t *testing.T) {
	secret := []byte("test-secret")
	wrongSecret := []byte("wrong-secret")
	layer := NewAuthLayer(secret, 24*time.Hour)

	// Create token with wrong secret
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id": "user-123",
		"exp":     time.Now().Add(1 * time.Hour).Unix(),
	})
	tokenString, err := token.SignedString(wrongSecret)
	require.NoError(t, err)

	// Validate
	ctx := context.Background()
	user, err := layer.ValidateToken(ctx, tokenString)

	assert.Error(t, err)
	assert.Nil(t, user)
}

func TestAuthLayer_ValidateToken_Revoked(t *testing.T) {
	secret := []byte("test-secret")
	layer := NewAuthLayer(secret, 24*time.Hour)

	// Create valid token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id": "user-123",
		"exp":     time.Now().Add(1 * time.Hour).Unix(),
	})
	tokenString, err := token.SignedString(secret)
	require.NoError(t, err)

	// Revoke token
	ctx := context.Background()
	err = layer.RevokeToken(ctx, tokenString)
	require.NoError(t, err)

	// Try to validate
	user, err := layer.ValidateToken(ctx, tokenString)

	assert.Error(t, err)
	assert.Nil(t, user)
	assert.Contains(t, err.Error(), "revoked")
}

func TestAuthLayer_RequireMFA(t *testing.T) {
	layer := NewAuthLayer([]byte("test-secret"), 24*time.Hour)
	ctx := context.Background()

	tests := []struct {
		name       string
		actionRisk ActionRisk
		expected   bool
	}{
		{"Safe action no MFA", RiskSafe, false},
		{"Moderate action no MFA", RiskModerate, false},
		{"Destructive action requires MFA", RiskDestructive, true},
		{"Critical action requires MFA", RiskCritical, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			requireMFA, err := layer.RequireMFA(ctx, "user-123", tt.actionRisk)
			assert.NoError(t, err)
			assert.Equal(t, tt.expected, requireMFA)
		})
	}
}

func TestAuthLayer_RevokeToken(t *testing.T) {
	layer := NewAuthLayer([]byte("test-secret"), 24*time.Hour)
	ctx := context.Background()

	// Revoke a token
	err := layer.RevokeToken(ctx, "some-token")
	assert.NoError(t, err)

	// Revoke another
	err = layer.RevokeToken(ctx, "another-token")
	assert.NoError(t, err)
}
