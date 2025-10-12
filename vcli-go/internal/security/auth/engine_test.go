package auth

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/pkg/security/types"
)

// mockMFAProvider for testing
type mockMFAProvider struct {
	validateFunc  func(ctx context.Context, userID, code string) error
	generateFunc  func(ctx context.Context, userID string) (string, []byte, error)
	isEnabledFunc func(ctx context.Context, userID string) (bool, error)
}

func (m *mockMFAProvider) Validate(ctx context.Context, userID, code string) error {
	if m.validateFunc != nil {
		return m.validateFunc(ctx, userID, code)
	}
	return nil
}

func (m *mockMFAProvider) Generate(ctx context.Context, userID string) (string, []byte, error) {
	if m.generateFunc != nil {
		return m.generateFunc(ctx, userID)
	}
	return "secret", []byte{}, nil
}

func (m *mockMFAProvider) IsEnabled(ctx context.Context, userID string) (bool, error) {
	if m.isEnabledFunc != nil {
		return m.isEnabledFunc(ctx, userID)
	}
	return false, nil
}

func TestAuthenticationEngine_Authenticate(t *testing.T) {
	// Setup
	secret := []byte("test-secret-key-for-maximus")
	jwtValidator := NewJWTValidator(secret, "vcli", "vcli-users")
	mfaProvider := &mockMFAProvider{}
	sessionStore := NewInMemorySessionStore()
	sessionManager := NewSessionManager(sessionStore, 1*time.Hour)

	engine := NewAuthenticationEngine(jwtValidator, mfaProvider, sessionManager)

	// Create user and token
	user := &types.User{
		ID:       "user123",
		Username: "testuser",
		Email:    "test@example.com",
		Roles:    []string{"user"},
	}

	token, err := jwtValidator.Generate(context.Background(), user, 1*time.Hour)
	require.NoError(t, err)

	// Authenticate
	req := &types.AuthRequest{
		Token: token,
	}

	result, err := engine.Authenticate(context.Background(), req)
	require.NoError(t, err)
	assert.True(t, result.Success)
	assert.NotNil(t, result.User)
	assert.NotNil(t, result.Session)
	assert.Equal(t, user.ID, result.User.ID)
}

func TestAuthenticationEngine_AuthenticateInvalidToken(t *testing.T) {
	// Setup
	secret := []byte("test-secret-key-for-maximus")
	jwtValidator := NewJWTValidator(secret, "vcli", "vcli-users")
	mfaProvider := &mockMFAProvider{}
	sessionStore := NewInMemorySessionStore()
	sessionManager := NewSessionManager(sessionStore, 1*time.Hour)

	engine := NewAuthenticationEngine(jwtValidator, mfaProvider, sessionManager)

	// Try invalid token
	req := &types.AuthRequest{
		Token: "invalid-token",
	}

	result, err := engine.Authenticate(context.Background(), req)
	assert.Error(t, err)
	assert.False(t, result.Success)
}

func TestAuthenticationEngine_AuthenticateWithMFA(t *testing.T) {
	// Setup
	secret := []byte("test-secret-key-for-maximus")
	jwtValidator := NewJWTValidator(secret, "vcli", "vcli-users")

	// Mock MFA provider that expects specific code
	mfaProvider := &mockMFAProvider{
		validateFunc: func(ctx context.Context, userID, code string) error {
			if code == "123456" {
				return nil
			}
			return errors.New("invalid MFA code")
		},
	}

	sessionStore := NewInMemorySessionStore()
	sessionManager := NewSessionManager(sessionStore, 1*time.Hour)

	engine := NewAuthenticationEngine(jwtValidator, mfaProvider, sessionManager)

	// Create user with MFA enabled and token
	user := &types.User{
		ID:         "user123",
		Username:   "testuser",
		Email:      "test@example.com",
		Roles:      []string{"user"},
		MFAEnabled: true,
	}

	token, err := jwtValidator.Generate(context.Background(), user, 1*time.Hour)
	require.NoError(t, err)

	// Authenticate with valid MFA code
	req := &types.AuthRequest{
		Token:   token,
		MFACode: "123456",
	}

	result, err := engine.Authenticate(context.Background(), req)
	require.NoError(t, err)
	assert.True(t, result.Success)
	assert.NotNil(t, result.Session)
}

func TestAuthenticationEngine_AuthenticateWithInvalidMFA(t *testing.T) {
	// Setup
	secret := []byte("test-secret-key-for-maximus")
	jwtValidator := NewJWTValidator(secret, "vcli", "vcli-users")

	// Mock MFA provider that rejects all codes
	mfaProvider := &mockMFAProvider{
		validateFunc: func(ctx context.Context, userID, code string) error {
			return errors.New("invalid MFA code")
		},
	}

	sessionStore := NewInMemorySessionStore()
	sessionManager := NewSessionManager(sessionStore, 1*time.Hour)

	engine := NewAuthenticationEngine(jwtValidator, mfaProvider, sessionManager)

	// Create user with MFA enabled and token
	user := &types.User{
		ID:         "user123",
		Username:   "testuser",
		Email:      "test@example.com",
		Roles:      []string{"user"},
		MFAEnabled: true,
	}

	token, err := jwtValidator.Generate(context.Background(), user, 1*time.Hour)
	require.NoError(t, err)

	// Authenticate with invalid MFA code
	req := &types.AuthRequest{
		Token:   token,
		MFACode: "wrong",
	}

	result, err := engine.Authenticate(context.Background(), req)
	assert.Error(t, err)
	assert.False(t, result.Success)
}

func TestAuthenticationEngine_RevokeSession(t *testing.T) {
	// Setup
	secret := []byte("test-secret-key-for-maximus")
	jwtValidator := NewJWTValidator(secret, "vcli", "vcli-users")
	mfaProvider := &mockMFAProvider{}
	sessionStore := NewInMemorySessionStore()
	sessionManager := NewSessionManager(sessionStore, 1*time.Hour)

	engine := NewAuthenticationEngine(jwtValidator, mfaProvider, sessionManager)

	// Create user and session
	user := &types.User{
		ID:       "user123",
		Username: "testuser",
	}

	session, err := engine.CreateSession(context.Background(), user)
	require.NoError(t, err)

	// Revoke session
	err = engine.RevokeSession(context.Background(), session.ID)
	require.NoError(t, err)

	// Verify session is gone
	_, err = sessionManager.Get(context.Background(), session.ID)
	assert.ErrorIs(t, err, ErrSessionNotFound)
}
