package auth

import (
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewSessionManager(t *testing.T) {
	t.Run("Valid config", func(t *testing.T) {
		key, _ := GenerateSigningKey()
		config := &SessionConfig{
			TokenDuration:   15 * time.Minute,
			RefreshDuration: 7 * 24 * time.Hour,
			RefreshEnabled:  true,
			Issuer:          "test-issuer",
			SigningKey:      key,
		}

		manager, err := NewSessionManager(config)

		require.NoError(t, err)
		assert.NotNil(t, manager)
		assert.Equal(t, "test-issuer", manager.issuer)
		assert.Equal(t, 15*time.Minute, manager.tokenDuration)
		assert.True(t, manager.refreshEnabled)
	})

	t.Run("Nil config", func(t *testing.T) {
		manager, err := NewSessionManager(nil)

		assert.Error(t, err)
		assert.Nil(t, manager)
		assert.Contains(t, err.Error(), "config cannot be nil")
	})

	t.Run("Weak signing key", func(t *testing.T) {
		config := &SessionConfig{
			SigningKey: []byte("short"),
		}

		manager, err := NewSessionManager(config)

		assert.Error(t, err)
		assert.Nil(t, manager)
		assert.Contains(t, err.Error(), "at least 32 bytes")
	})

	t.Run("Default values", func(t *testing.T) {
		key, _ := GenerateSigningKey()
		config := &SessionConfig{
			SigningKey: key,
		}

		manager, err := NewSessionManager(config)

		require.NoError(t, err)
		assert.Equal(t, 15*time.Minute, manager.tokenDuration)
		assert.Equal(t, "vcli-nlp-guardian", manager.issuer)
	})
}

func TestCreateSession(t *testing.T) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{
		SigningKey:     key,
		RefreshEnabled: true,
	})

	t.Run("Successful creation", func(t *testing.T) {
		session, err := manager.CreateSession("user123", "testuser", []string{"admin"}, true)

		require.NoError(t, err)
		assert.NotNil(t, session)
		assert.NotEmpty(t, session.Token)
		assert.NotEmpty(t, session.RefreshToken)
		assert.Equal(t, "user123", session.Claims.UserID)
		assert.Equal(t, "testuser", session.Claims.Username)
		assert.Equal(t, []string{"admin"}, session.Claims.Roles)
		assert.True(t, session.Claims.MFACompleted)
		assert.True(t, session.Renewable)
		assert.False(t, session.CreatedAt.IsZero())
		assert.False(t, session.ExpiresAt.IsZero())
	})

	t.Run("Empty userID", func(t *testing.T) {
		session, err := manager.CreateSession("", "testuser", []string{}, false)

		assert.Error(t, err)
		assert.Nil(t, session)
		assert.Contains(t, err.Error(), "userID cannot be empty")
	})

	t.Run("No refresh token when disabled", func(t *testing.T) {
		manager2, _ := NewSessionManager(&SessionConfig{
			SigningKey:     key,
			RefreshEnabled: false,
		})

		session, err := manager2.CreateSession("user123", "test", []string{}, false)

		require.NoError(t, err)
		assert.Empty(t, session.RefreshToken)
		assert.False(t, session.Renewable)
	})

	t.Run("Token has correct claims", func(t *testing.T) {
		session, _ := manager.CreateSession("user456", "admin", []string{"admin", "operator"}, true)

		// Parse token to verify claims
		token, err := jwt.ParseWithClaims(session.Token, &SessionClaims{}, func(token *jwt.Token) (interface{}, error) {
			return key, nil
		})

		require.NoError(t, err)
		claims := token.Claims.(*SessionClaims)
		assert.Equal(t, "user456", claims.UserID)
		assert.Equal(t, "admin", claims.Username)
		assert.Contains(t, claims.Roles, "admin")
		assert.Contains(t, claims.Roles, "operator")
		assert.True(t, claims.MFACompleted)
	})
}

func TestValidateSession(t *testing.T) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{SigningKey: key})

	t.Run("Valid token", func(t *testing.T) {
		session, _ := manager.CreateSession("user123", "test", []string{"viewer"}, false)

		claims, err := manager.ValidateSession(session.Token)

		require.NoError(t, err)
		assert.NotNil(t, claims)
		assert.Equal(t, "user123", claims.UserID)
		assert.Equal(t, "test", claims.Username)
	})

	t.Run("Empty token", func(t *testing.T) {
		claims, err := manager.ValidateSession("")

		assert.Error(t, err)
		assert.Nil(t, claims)
		assert.Contains(t, err.Error(), "token cannot be empty")
	})

	t.Run("Invalid token format", func(t *testing.T) {
		claims, err := manager.ValidateSession("invalid.token.format")

		assert.Error(t, err)
		assert.Nil(t, claims)
	})

	t.Run("Token with wrong signing key", func(t *testing.T) {
		wrongKey, _ := GenerateSigningKey()
		wrongManager, _ := NewSessionManager(&SessionConfig{SigningKey: wrongKey})
		session, _ := wrongManager.CreateSession("user999", "wrong", []string{}, false)

		claims, err := manager.ValidateSession(session.Token)

		assert.Error(t, err)
		assert.Nil(t, claims)
	})

	t.Run("Revoked token", func(t *testing.T) {
		session, _ := manager.CreateSession("user789", "revoked", []string{}, false)
		
		// Revoke the token
		err := manager.RevokeSession(session.Claims.ID)
		require.NoError(t, err)

		// Try to validate
		claims, err := manager.ValidateSession(session.Token)

		assert.Error(t, err)
		assert.Nil(t, claims)
		assert.Contains(t, err.Error(), "revoked")
	})
}

func TestRefreshSession(t *testing.T) {
	key, _ := GenerateSigningKey()

	t.Run("Successful refresh", func(t *testing.T) {
		manager, _ := NewSessionManager(&SessionConfig{
			SigningKey:     key,
			RefreshEnabled: true,
		})

		session, _ := manager.CreateSession("user123", "test", []string{"admin"}, true)

		// Refresh using refresh token
		newSession, err := manager.RefreshSession(session.RefreshToken)

		require.NoError(t, err)
		assert.NotNil(t, newSession)
		assert.NotEqual(t, session.Token, newSession.Token)
		assert.Equal(t, "user123", newSession.Claims.UserID)
		assert.Equal(t, "test", newSession.Claims.Username)
		assert.True(t, newSession.Claims.MFACompleted)
	})

	t.Run("Refresh disabled", func(t *testing.T) {
		manager, _ := NewSessionManager(&SessionConfig{
			SigningKey:     key,
			RefreshEnabled: false,
		})

		newSession, err := manager.RefreshSession("any-token")

		assert.Error(t, err)
		assert.Nil(t, newSession)
		assert.Contains(t, err.Error(), "refresh tokens are disabled")
	})

	t.Run("Empty refresh token", func(t *testing.T) {
		manager, _ := NewSessionManager(&SessionConfig{
			SigningKey:     key,
			RefreshEnabled: true,
		})

		newSession, err := manager.RefreshSession("")

		assert.Error(t, err)
		assert.Nil(t, newSession)
		assert.Contains(t, err.Error(), "refresh token cannot be empty")
	})

	t.Run("Invalid refresh token", func(t *testing.T) {
		manager, _ := NewSessionManager(&SessionConfig{
			SigningKey:     key,
			RefreshEnabled: true,
		})

		newSession, err := manager.RefreshSession("invalid.refresh.token")

		assert.Error(t, err)
		assert.Nil(t, newSession)
	})
}

func TestRevokeSession(t *testing.T) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{SigningKey: key})

	t.Run("Revoke by token ID", func(t *testing.T) {
		err := manager.RevokeSession("token-id-123")

		assert.NoError(t, err)
		assert.True(t, manager.isRevoked("token-id-123"))
	})

	t.Run("Empty token ID", func(t *testing.T) {
		err := manager.RevokeSession("")

		assert.Error(t, err)
		assert.Contains(t, err.Error(), "tokenID cannot be empty")
	})

	t.Run("Revoke by token string", func(t *testing.T) {
		session, _ := manager.CreateSession("user456", "test", []string{}, false)

		err := manager.RevokeSessionByToken(session.Token)

		require.NoError(t, err)
		assert.True(t, manager.isRevoked(session.Claims.ID))

		// Validation should fail
		claims, err := manager.ValidateSession(session.Token)
		assert.Error(t, err)
		assert.Nil(t, claims)
	})

	t.Run("Revoke count tracking", func(t *testing.T) {
		initialCount := manager.GetRevokedTokenCount()

		manager.RevokeSession("token-1")
		manager.RevokeSession("token-2")
		manager.RevokeSession("token-3")

		assert.Equal(t, initialCount+3, manager.GetRevokedTokenCount())
	})
}

func TestIsSessionValid(t *testing.T) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{SigningKey: key})

	t.Run("Valid session", func(t *testing.T) {
		session, _ := manager.CreateSession("user123", "test", []string{}, false)

		valid := manager.IsSessionValid(session.Token)

		assert.True(t, valid)
	})

	t.Run("Invalid session", func(t *testing.T) {
		valid := manager.IsSessionValid("invalid.token")

		assert.False(t, valid)
	})

	t.Run("Revoked session", func(t *testing.T) {
		session, _ := manager.CreateSession("user456", "test", []string{}, false)
		manager.RevokeSession(session.Claims.ID)

		valid := manager.IsSessionValid(session.Token)

		assert.False(t, valid)
	})
}

func TestExtendSession(t *testing.T) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{SigningKey: key})

	t.Run("Successful extension", func(t *testing.T) {
		session, _ := manager.CreateSession("user123", "test", []string{"admin"}, true)
		originalExpiry := session.ExpiresAt

		// Extend by 1 hour
		extendedSession, err := manager.ExtendSession(session.Token, 1*time.Hour)

		require.NoError(t, err)
		assert.NotNil(t, extendedSession)
		assert.NotEqual(t, session.Token, extendedSession.Token)
		assert.True(t, extendedSession.ExpiresAt.After(originalExpiry))
		assert.Equal(t, "user123", extendedSession.Claims.UserID)

		// Old token should be revoked
		assert.True(t, manager.isRevoked(session.Claims.ID))
	})

	t.Run("Extend invalid session", func(t *testing.T) {
		extendedSession, err := manager.ExtendSession("invalid.token", 1*time.Hour)

		assert.Error(t, err)
		assert.Nil(t, extendedSession)
		assert.Contains(t, err.Error(), "cannot extend invalid session")
	})
}

func TestCleanupRevokedTokens(t *testing.T) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{SigningKey: key})

	t.Run("Cleanup old revoked tokens", func(t *testing.T) {
		// Add some revoked tokens with old timestamps
		oldTime := time.Now().Add(-25 * time.Hour)
		manager.revokedTokens["old-token-1"] = oldTime
		manager.revokedTokens["old-token-2"] = oldTime

		// Add recent revoked token
		manager.revokedTokens["recent-token"] = time.Now()

		initialCount := manager.GetRevokedTokenCount()
		cleaned := manager.CleanupRevokedTokens()

		assert.Equal(t, 2, cleaned)
		assert.Equal(t, initialCount-2, manager.GetRevokedTokenCount())
		assert.False(t, manager.isRevoked("old-token-1"))
		assert.False(t, manager.isRevoked("old-token-2"))
		assert.True(t, manager.isRevoked("recent-token"))
	})

	t.Run("No cleanup needed", func(t *testing.T) {
		manager2, _ := NewSessionManager(&SessionConfig{SigningKey: key})
		manager2.RevokeSession("recent-token")

		cleaned := manager2.CleanupRevokedTokens()

		assert.Equal(t, 0, cleaned)
		assert.Equal(t, 1, manager2.GetRevokedTokenCount())
	})
}

func TestGenerateSigningKey(t *testing.T) {
	t.Run("Generate valid key", func(t *testing.T) {
		key, err := GenerateSigningKey()

		require.NoError(t, err)
		assert.NotNil(t, key)
		assert.Equal(t, 64, len(key))
	})

	t.Run("Generate different keys", func(t *testing.T) {
		key1, _ := GenerateSigningKey()
		key2, _ := GenerateSigningKey()

		assert.NotEqual(t, key1, key2)
	})
}

func TestGenerateTokenID(t *testing.T) {
	t.Run("Generate valid ID", func(t *testing.T) {
		id, err := generateTokenID()

		require.NoError(t, err)
		assert.NotEmpty(t, id)
		assert.Greater(t, len(id), 32)
	})

	t.Run("Generate unique IDs", func(t *testing.T) {
		id1, _ := generateTokenID()
		id2, _ := generateTokenID()

		assert.NotEqual(t, id1, id2)
	})
}

// Benchmarks
func BenchmarkCreateSession(b *testing.B) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{
		SigningKey:     key,
		RefreshEnabled: true,
	})

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = manager.CreateSession("user123", "test", []string{"admin"}, true)
	}
}

func BenchmarkValidateSession(b *testing.B) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{SigningKey: key})
	session, _ := manager.CreateSession("user123", "test", []string{}, false)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = manager.ValidateSession(session.Token)
	}
}

func BenchmarkRevokeSession(b *testing.B) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{SigningKey: key})

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = manager.RevokeSession("token-id")
	}
}

func BenchmarkRefreshSession(b *testing.B) {
	key, _ := GenerateSigningKey()
	manager, _ := NewSessionManager(&SessionConfig{
		SigningKey:     key,
		RefreshEnabled: true,
	})
	session, _ := manager.CreateSession("user123", "test", []string{}, false)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = manager.RefreshSession(session.RefreshToken)
	}
}
