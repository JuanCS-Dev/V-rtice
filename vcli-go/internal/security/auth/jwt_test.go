package auth

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/pkg/security/types"
)

func TestJWTValidator_Validate(t *testing.T) {
	secret := []byte("test-secret-key-for-maximus")
	validator := NewJWTValidator(secret, "vcli", "vcli-users")

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
		Email:    "test@example.com",
		Roles:    []string{"user"},
	}

	// Generate valid token
	token, err := validator.Generate(context.Background(), user, 1*time.Hour)
	require.NoError(t, err)

	// Validate token
	validatedUser, err := validator.Validate(context.Background(), token)
	require.NoError(t, err)
	assert.Equal(t, user.ID, validatedUser.ID)
	assert.Equal(t, user.Username, validatedUser.Username)
	assert.Equal(t, user.Email, validatedUser.Email)
}

func TestJWTValidator_ExpiredToken(t *testing.T) {
	secret := []byte("test-secret-key-for-maximus")
	validator := NewJWTValidator(secret, "vcli", "vcli-users")

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	// Generate expired token
	token, err := validator.Generate(context.Background(), user, -1*time.Hour)
	require.NoError(t, err)

	// Validate should fail
	_, err = validator.Validate(context.Background(), token)
	assert.ErrorIs(t, err, ErrTokenExpired)
}

func TestJWTValidator_InvalidSignature(t *testing.T) {
	secret := []byte("test-secret-key-for-maximus")
	validator := NewJWTValidator(secret, "vcli", "vcli-users")

	// Create validator with different secret
	otherValidator := NewJWTValidator([]byte("other-secret-key"), "vcli", "vcli-users")

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	// Generate token with other secret
	token, err := otherValidator.Generate(context.Background(), user, 1*time.Hour)
	require.NoError(t, err)

	// Validate with original validator should fail
	_, err = validator.Validate(context.Background(), token)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid")
}

func TestJWTValidator_MissingClaims(t *testing.T) {
	secret := []byte("test-secret-key-for-maximus")
	validator := NewJWTValidator(secret, "vcli", "vcli-users")

	// User with missing required fields
	user := &types.User{
		ID:       "", // Missing ID
		Username: "", // Missing username
	}

	// Should fail to generate token or validation should fail
	token, err := validator.Generate(context.Background(), user, 1*time.Hour)
	if err == nil {
		_, err = validator.Validate(context.Background(), token)
		assert.ErrorIs(t, err, ErrMissingClaims)
	}
}

func TestJWTValidator_InvalidAudience(t *testing.T) {
	secret := []byte("test-secret-key-for-maximus")
	validator := NewJWTValidator(secret, "vcli", "vcli-users")
	otherValidator := NewJWTValidator(secret, "vcli", "other-audience")

	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	// Generate token with different audience
	token, err := otherValidator.Generate(context.Background(), user, 1*time.Hour)
	require.NoError(t, err)

	// Validate with original audience should fail
	_, err = validator.Validate(context.Background(), token)
	assert.ErrorIs(t, err, ErrInvalidToken)
}
