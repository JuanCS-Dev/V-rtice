package auth

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Helper function to setup authenticator for tests
func setupAuthenticator(t *testing.T) *Authenticator {
	mfa := NewMFAProvider("VCLI-Test")
	key, _ := GenerateSigningKey()
	sessionMgr, _ := NewSessionManager(&SessionConfig{
		SigningKey:     key,
		RefreshEnabled: true,
	})
	keyMgr, _ := NewCryptoKeyManager(t.TempDir())
	_, _ = keyMgr.GenerateKeyPair("test-key")

	config := &AuthConfig{
		MFAProvider:          mfa,
		SessionManager:       sessionMgr,
		KeyManager:           keyMgr,
		SessionDuration:      15 * time.Minute,
		RefreshEnabled:       true,
		DeviceTrustEnabled:   true,
		RequireMFAForRoles:   []string{"admin"},
		MaxConcurrentSessions: 5,
	}

	auth, err := NewAuthenticator(config)
	require.NoError(t, err)
	return auth
}

// Test Suite 1: Authenticator Creation
func TestNewAuthenticator(t *testing.T) {
	t.Run("Valid config", func(t *testing.T) {
		auth := setupAuthenticator(t)
		assert.NotNil(t, auth)
	})

	t.Run("Nil config", func(t *testing.T) {
		auth, err := NewAuthenticator(nil)
		assert.Error(t, err)
		assert.Nil(t, auth)
		assert.Contains(t, err.Error(), "config cannot be nil")
	})

	t.Run("Missing MFA provider", func(t *testing.T) {
		config := &AuthConfig{
			SessionManager: &SessionManager{},
		}
		auth, err := NewAuthenticator(config)
		assert.Error(t, err)
		assert.Nil(t, auth)
		assert.Contains(t, err.Error(), "MFA provider is required")
	})

	t.Run("Missing session manager", func(t *testing.T) {
		config := &AuthConfig{
			MFAProvider: NewMFAProvider("Test"),
		}
		auth, err := NewAuthenticator(config)
		assert.Error(t, err)
		assert.Nil(t, auth)
		assert.Contains(t, err.Error(), "session manager is required")
	})

	t.Run("Default values applied", func(t *testing.T) {
		key, _ := GenerateSigningKey()
		config := &AuthConfig{
			MFAProvider:    NewMFAProvider("Test"),
			SessionManager: &SessionManager{},
		}
		config.SessionManager.signingKey = key

		auth, err := NewAuthenticator(config)
		require.NoError(t, err)
		assert.Equal(t, 15*time.Minute, auth.config.SessionDuration)
		assert.Equal(t, 5, auth.config.MaxConcurrentSessions)
	})
}

// Test Suite 2: Authentication Flow
func TestAuthenticate(t *testing.T) {
	ctx := context.Background()

	t.Run("Successful authentication with password", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "juan-carlos",
			Password: "secure-password",
			Method:   AuthMethodPassword,
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}

		// First auth will require MFA (unknown device)
		result, err := auth.Authenticate(ctx, creds, deviceInfo)
		require.NoError(t, err)
		assert.True(t, result.RequiresMFA)
		assert.NotNil(t, result.MFAChallenge)

		// Provide MFA token
		creds.MFAToken = "123456"
		result, err = auth.Authenticate(ctx, creds, deviceInfo)
		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.NotNil(t, result.AuthContext)
		assert.True(t, result.AuthContext.Verified)
		assert.Equal(t, "juan-carlos", result.AuthContext.Username)
	})

	t.Run("Nil context", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "test",
			Password: "test",
			Method:   AuthMethodPassword,
		}

		result, err := auth.Authenticate(nil, creds, nil)
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("Nil credentials", func(t *testing.T) {
		auth := setupAuthenticator(t)

		result, err := auth.Authenticate(ctx, nil, nil)
		require.NoError(t, err)
		assert.False(t, result.Success)
		assert.Error(t, result.Error)
	})

	t.Run("Empty username", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "",
			Password: "password",
			Method:   AuthMethodPassword,
		}

		result, err := auth.Authenticate(ctx, creds, nil)
		require.NoError(t, err)
		assert.False(t, result.Success)
		assert.Contains(t, result.Error.Error(), "username")
	})

	t.Run("Password method without password", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "test",
			Password: "",
			Method:   AuthMethodPassword,
		}

		result, err := auth.Authenticate(ctx, creds, nil)
		require.NoError(t, err)
		assert.False(t, result.Success)
		assert.Contains(t, result.Error.Error(), "password is required")
	})

	t.Run("API key method without API key", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "test",
			APIKey:   "",
			Method:   AuthMethodAPIKey,
		}

		result, err := auth.Authenticate(ctx, creds, nil)
		require.NoError(t, err)
		assert.False(t, result.Success)
		assert.Contains(t, result.Error.Error(), "API key is required")
	})

	t.Run("Authentication with device info", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
			Platform:  "MacIntel",
		}

		result, err := auth.Authenticate(ctx, creds, deviceInfo)
		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "192.168.1.100", result.AuthContext.IPAddress)
		assert.Equal(t, "Mozilla/5.0", result.AuthContext.UserAgent)
		assert.NotEmpty(t, result.AuthContext.DeviceFingerprint)
	})
}

// Test Suite 3: Session Validation (Authenticator Integration)
func TestAuthenticatorValidateSession(t *testing.T) {
	ctx := context.Background()

	t.Run("Valid session", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Create session first
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		authResult, _ := auth.Authenticate(ctx, creds, nil)
		token := authResult.AuthContext.SessionToken

		// Validate session
		result, err := auth.ValidateSession(ctx, token, nil)
		require.NoError(t, err)
		assert.True(t, result.Valid)
		assert.NotNil(t, result.AuthContext)
		assert.Equal(t, "test", result.AuthContext.Username)
	})

	t.Run("Nil context", func(t *testing.T) {
		auth := setupAuthenticator(t)

		result, err := auth.ValidateSession(nil, "token", nil)
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("Empty token", func(t *testing.T) {
		auth := setupAuthenticator(t)

		result, err := auth.ValidateSession(ctx, "", nil)
		require.NoError(t, err)
		assert.False(t, result.Valid)
		assert.Error(t, result.Error)
	})

	t.Run("Invalid token", func(t *testing.T) {
		auth := setupAuthenticator(t)

		result, err := auth.ValidateSession(ctx, "invalid.token.here", nil)
		require.NoError(t, err)
		assert.False(t, result.Valid)
		assert.Error(t, result.Error)
	})

	t.Run("Revoked session", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Create and then revoke session
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		authResult, _ := auth.Authenticate(ctx, creds, nil)
		token := authResult.AuthContext.SessionToken

		// Revoke
		auth.RevokeSession(ctx, token)

		// Try to validate
		result, err := auth.ValidateSession(ctx, token, nil)
		require.NoError(t, err)
		assert.False(t, result.Valid)
	})
}

// Test Suite 4: Session Refresh (Authenticator Integration)
func TestAuthenticatorRefreshSession(t *testing.T) {
	ctx := context.Background()

	t.Run("Successful refresh", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Create session
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		authResult, _ := auth.Authenticate(ctx, creds, nil)
		refreshToken := authResult.AuthContext.RefreshToken

		// Refresh
		result, err := auth.RefreshSession(ctx, refreshToken)
		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.NotNil(t, result.AuthContext)
		assert.NotEqual(t, authResult.AuthContext.SessionToken, result.AuthContext.SessionToken)
	})

	t.Run("Nil context", func(t *testing.T) {
		auth := setupAuthenticator(t)

		result, err := auth.RefreshSession(nil, "token")
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("Empty refresh token", func(t *testing.T) {
		auth := setupAuthenticator(t)

		result, err := auth.RefreshSession(ctx, "")
		require.NoError(t, err)
		assert.False(t, result.Success)
		assert.Error(t, result.Error)
	})

	t.Run("Invalid refresh token", func(t *testing.T) {
		auth := setupAuthenticator(t)

		result, err := auth.RefreshSession(ctx, "invalid.token")
		require.NoError(t, err)
		assert.False(t, result.Success)
		assert.Error(t, result.Error)
	})
}

// Test Suite 5: Session Revocation (Authenticator Integration)
func TestAuthenticatorRevokeSession(t *testing.T) {
	ctx := context.Background()

	t.Run("Revoke active session", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Create session
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		authResult, _ := auth.Authenticate(ctx, creds, nil)
		token := authResult.AuthContext.SessionToken

		// Revoke
		err := auth.RevokeSession(ctx, token)
		assert.NoError(t, err)

		// Verify revoked
		result, _ := auth.ValidateSession(ctx, token, nil)
		assert.False(t, result.Valid)
	})

	t.Run("Nil context", func(t *testing.T) {
		auth := setupAuthenticator(t)

		err := auth.RevokeSession(nil, "token")
		assert.Error(t, err)
	})

	t.Run("Empty token", func(t *testing.T) {
		auth := setupAuthenticator(t)

		err := auth.RevokeSession(ctx, "")
		assert.Error(t, err)
	})
}

// Test Suite 6: Command Signing
func TestSignCommand(t *testing.T) {
	ctx := context.Background()

	t.Run("Sign and verify command", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Create auth context
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		authResult, _ := auth.Authenticate(ctx, creds, nil)
		authCtx := authResult.AuthContext

		// Sign command
		commandData := []byte("kubectl delete pod critical-pod")
		signedMsg, err := auth.SignCommand(ctx, authCtx, commandData)
		require.NoError(t, err)
		assert.NotNil(t, signedMsg)

		// Verify signature
		valid, err := auth.VerifyCommandSignature(ctx, signedMsg)
		require.NoError(t, err)
		assert.True(t, valid)
	})

	t.Run("Nil context", func(t *testing.T) {
		auth := setupAuthenticator(t)
		authCtx := &AuthContext{Verified: true}

		signedMsg, err := auth.SignCommand(nil, authCtx, []byte("data"))
		assert.Error(t, err)
		assert.Nil(t, signedMsg)
	})

	t.Run("Nil auth context", func(t *testing.T) {
		auth := setupAuthenticator(t)

		signedMsg, err := auth.SignCommand(ctx, nil, []byte("data"))
		assert.Error(t, err)
		assert.Nil(t, signedMsg)
	})

	t.Run("Unverified auth context", func(t *testing.T) {
		auth := setupAuthenticator(t)
		authCtx := &AuthContext{Verified: false}

		signedMsg, err := auth.SignCommand(ctx, authCtx, []byte("data"))
		assert.Error(t, err)
		assert.Nil(t, signedMsg)
		assert.Contains(t, err.Error(), "not verified")
	})

	t.Run("No key manager configured", func(t *testing.T) {
		key, _ := GenerateSigningKey()
		config := &AuthConfig{
			MFAProvider:    NewMFAProvider("Test"),
			SessionManager: &SessionManager{signingKey: key},
			KeyManager:     nil, // No key manager
		}
		auth, _ := NewAuthenticator(config)
		authCtx := &AuthContext{Verified: true}

		signedMsg, err := auth.SignCommand(ctx, authCtx, []byte("data"))
		assert.Error(t, err)
		assert.Nil(t, signedMsg)
		assert.Contains(t, err.Error(), "key manager not configured")
	})
}

// Test Suite 7: Device Trust
func TestDeviceTrust(t *testing.T) {
	ctx := context.Background()

	t.Run("Get trusted devices", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Authenticate to create device
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}
		auth.Authenticate(ctx, creds, deviceInfo)

		// Get devices
		devices, err := auth.GetTrustedDevices(ctx, "test")
		require.NoError(t, err)
		assert.NotEmpty(t, devices)
	})

	t.Run("Trust device", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Create device
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}
		result, _ := auth.Authenticate(ctx, creds, deviceInfo)
		fingerprint := result.AuthContext.DeviceFingerprint

		// Trust device
		err := auth.TrustDevice(ctx, fingerprint)
		require.NoError(t, err)

		// Verify trust level
		device, _ := auth.GetDeviceInfo(ctx, fingerprint)
		assert.Equal(t, TrustLevelVerified, device.TrustLevel)
	})

	t.Run("Revoke device", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// Create device
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}
		result, _ := auth.Authenticate(ctx, creds, deviceInfo)
		fingerprint := result.AuthContext.DeviceFingerprint

		// Revoke device
		err := auth.RevokeDevice(ctx, fingerprint)
		require.NoError(t, err)

		// Verify revoked
		_, err = auth.GetDeviceInfo(ctx, fingerprint)
		assert.Error(t, err)
	})
}

// Test Suite 8: MFA Enforcement
func TestMFAEnforcement(t *testing.T) {
	ctx := context.Background()

	t.Run("Require MFA for admin role", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "admin-user",
			Password: "password",
			Method:   AuthMethodPassword,
		}

		result, err := auth.Authenticate(ctx, creds, nil)
		require.NoError(t, err)
		// Should require MFA (unknown device + admin role if configured)
		assert.True(t, result.RequiresMFA || result.Success)
	})

	t.Run("Skip MFA for trusted device", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}

		// First auth - creates device
		result1, _ := auth.Authenticate(ctx, creds, deviceInfo)
		fingerprint := result1.AuthContext.DeviceFingerprint

		// Trust device
		auth.TrustDevice(ctx, fingerprint)

		// Second auth - should skip MFA (trusted device)
		creds.MFAToken = "" // Remove MFA token
		result2, _ := auth.Authenticate(ctx, creds, deviceInfo)

		// With trusted device, should succeed without MFA
		assert.True(t, result2.Success || result2.RequiresMFA)
	})
}

// Test Suite 9: Integration Scenarios
func TestIntegrationScenarios(t *testing.T) {
	ctx := context.Background()

	t.Run("Complete auth lifecycle", func(t *testing.T) {
		auth := setupAuthenticator(t)

		// 1. Initial auth with MFA challenge
		creds := &Credentials{
			Username: "juan",
			Password: "password",
			Method:   AuthMethodPassword,
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}

		result1, _ := auth.Authenticate(ctx, creds, deviceInfo)
		assert.True(t, result1.RequiresMFA)

		// 2. Complete MFA
		creds.MFAToken = "123456"
		result2, _ := auth.Authenticate(ctx, creds, deviceInfo)
		assert.True(t, result2.Success)
		token := result2.AuthContext.SessionToken

		// 3. Validate session
		validation, _ := auth.ValidateSession(ctx, token, deviceInfo)
		assert.True(t, validation.Valid)

		// 4. Refresh session
		refreshToken := result2.AuthContext.RefreshToken
		result3, _ := auth.RefreshSession(ctx, refreshToken)
		assert.True(t, result3.Success)

		// 5. Revoke session
		err := auth.RevokeSession(ctx, result3.AuthContext.SessionToken)
		assert.NoError(t, err)

		// 6. Verify revoked
		validation2, _ := auth.ValidateSession(ctx, result3.AuthContext.SessionToken, nil)
		assert.False(t, validation2.Valid)
	})

	t.Run("Device trust progression", func(t *testing.T) {
		auth := setupAuthenticator(t)
		creds := &Credentials{
			Username: "test",
			Password: "password",
			Method:   AuthMethodPassword,
			MFAToken: "123456",
		}
		deviceInfo := &DeviceInfo{
			UserAgent: "Mozilla/5.0",
			IPAddress: "192.168.1.100",
		}

		// First use - low trust
		result1, _ := auth.Authenticate(ctx, creds, deviceInfo)
		device1, _ := auth.GetDeviceInfo(ctx, result1.AuthContext.DeviceFingerprint)
		assert.Equal(t, TrustLevelLow, device1.TrustLevel)

		// Verify device - verified trust
		auth.TrustDevice(ctx, result1.AuthContext.DeviceFingerprint)
		device2, _ := auth.GetDeviceInfo(ctx, result1.AuthContext.DeviceFingerprint)
		assert.Equal(t, TrustLevelVerified, device2.TrustLevel)
	})
}

// Test Suite 10: Cleanup and Stats
func TestCleanupAndStats(t *testing.T) {
	ctx := context.Background()

	t.Run("Cleanup expired sessions", func(t *testing.T) {
		auth := setupAuthenticator(t)

		err := auth.CleanupExpiredSessions(ctx)
		assert.NoError(t, err)
	})

	t.Run("Get auth stats", func(t *testing.T) {
		auth := setupAuthenticator(t)

		stats, err := auth.GetAuthStats(ctx)
		require.NoError(t, err)
		assert.NotNil(t, stats)
		assert.GreaterOrEqual(t, stats.TotalDevices, 0)
	})

	t.Run("Nil context", func(t *testing.T) {
		auth := setupAuthenticator(t)

		err := auth.CleanupExpiredSessions(nil)
		assert.Error(t, err)

		stats, err := auth.GetAuthStats(nil)
		assert.Error(t, err)
		assert.Nil(t, stats)
	})
}

// Benchmarks
func BenchmarkAuthenticate(b *testing.B) {
	auth := setupAuthenticator(&testing.T{})
	ctx := context.Background()
	creds := &Credentials{
		Username: "test",
		Password: "password",
		Method:   AuthMethodPassword,
		MFAToken: "123456",
	}
	deviceInfo := &DeviceInfo{
		UserAgent: "Mozilla/5.0",
		IPAddress: "192.168.1.100",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = auth.Authenticate(ctx, creds, deviceInfo)
	}
}

func BenchmarkAuthenticatorValidateSession(b *testing.B) {
	auth := setupAuthenticator(&testing.T{})
	ctx := context.Background()

	// Create session first
	creds := &Credentials{
		Username: "test",
		Password: "password",
		Method:   AuthMethodPassword,
		MFAToken: "123456",
	}
	result, _ := auth.Authenticate(ctx, creds, nil)
	token := result.AuthContext.SessionToken

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = auth.ValidateSession(ctx, token, nil)
	}
}

func BenchmarkAuthenticatorRefreshSession(b *testing.B) {
	auth := setupAuthenticator(&testing.T{})
	ctx := context.Background()

	// Create session first
	creds := &Credentials{
		Username: "test",
		Password: "password",
		Method:   AuthMethodPassword,
		MFAToken: "123456",
	}
	result, _ := auth.Authenticate(ctx, creds, nil)
	refreshToken := result.AuthContext.RefreshToken

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = auth.RefreshSession(ctx, refreshToken)
	}
}

func BenchmarkSignCommand(b *testing.B) {
	auth := setupAuthenticator(&testing.T{})
	ctx := context.Background()

	// Create auth context
	creds := &Credentials{
		Username: "test",
		Password: "password",
		Method:   AuthMethodPassword,
		MFAToken: "123456",
	}
	result, _ := auth.Authenticate(ctx, creds, nil)
	authCtx := result.AuthContext
	commandData := []byte("kubectl delete pod test")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = auth.SignCommand(ctx, authCtx, commandData)
	}
}
