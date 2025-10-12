package auth

import (
	"testing"
	"time"

	"github.com/pquerna/otp/totp"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMFAProvider_GenerateSecret(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")

	secret, err := provider.GenerateSecret("test@example.com")

	require.NoError(t, err)
	assert.NotEmpty(t, secret)
	// Base32 encoded 20 bytes should be 32 characters
	assert.Equal(t, 32, len(secret))

	// Should generate different secrets each time
	secret2, err := provider.GenerateSecret("test@example.com")
	require.NoError(t, err)
	assert.NotEqual(t, secret, secret2)
}

func TestMFAProvider_ValidateToken(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")
	secret := "JBSWY3DPEHPK3PXP" // Test secret

	// Generate valid token
	token, err := totp.GenerateCode(secret, time.Now())
	require.NoError(t, err)

	// Should validate correct token
	valid, err := provider.ValidateToken(secret, token)
	assert.NoError(t, err)
	assert.True(t, valid)

	// Should reject invalid token
	valid, err = provider.ValidateToken(secret, "000000")
	assert.Error(t, err)
	assert.False(t, valid)

	// Should reject empty token
	valid, err = provider.ValidateToken(secret, "")
	assert.Error(t, err)
	assert.False(t, valid)
}

func TestMFAProvider_ValidateTokenWithSkew(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")
	secret := "JBSWY3DPEHPK3PXP"

	// Generate token for current time
	token, err := totp.GenerateCode(secret, time.Now())
	require.NoError(t, err)

	// Should validate with skew
	valid, err := provider.ValidateTokenWithSkew(secret, token, 1)
	assert.NoError(t, err)
	assert.True(t, valid)

	// Generate token for 30 seconds ago (one period)
	pastToken, err := totp.GenerateCode(secret, time.Now().Add(-30*time.Second))
	require.NoError(t, err)

	// Should validate past token with skew=1
	valid, err = provider.ValidateTokenWithSkew(secret, pastToken, 1)
	assert.NoError(t, err)
	assert.True(t, valid)

	// Should reject very old token (beyond skew)
	veryOldToken, err := totp.GenerateCode(secret, time.Now().Add(-120*time.Second))
	require.NoError(t, err)
	
	valid, err = provider.ValidateTokenWithSkew(secret, veryOldToken, 1)
	assert.Error(t, err)
	assert.False(t, valid)
}

func TestMFAProvider_ProvisioningURI(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")
	secret := "JBSWY3DPEHPK3PXP"
	userID := "test@example.com"

	uri := provider.ProvisioningURI(userID, secret)

	// Should contain otpauth:// scheme
	assert.Contains(t, uri, "otpauth://totp/")
	// Should contain issuer
	assert.Contains(t, uri, "vCLI-Test")
	// Should contain user ID
	assert.Contains(t, uri, "test@example.com")
	// Should contain secret
	assert.Contains(t, uri, "secret="+secret)
	// Should contain default parameters
	assert.Contains(t, uri, "digits=6")
	assert.Contains(t, uri, "period=30")
}

func TestMFAProvider_GenerateToken(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")
	secret := "JBSWY3DPEHPK3PXP"

	// Generate token
	token, err := provider.GenerateToken(secret)
	require.NoError(t, err)
	assert.Len(t, token, 6) // Should be 6 digits

	// Generated token should be valid
	valid, err := provider.ValidateToken(secret, token)
	assert.NoError(t, err)
	assert.True(t, valid)
}

func TestMFAProvider_NewEnrollment(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")
	userID := "test@example.com"

	enrollment, err := provider.NewEnrollment(userID)
	require.NoError(t, err)
	assert.NotNil(t, enrollment)

	// Check enrollment fields
	assert.Equal(t, userID, enrollment.UserID)
	assert.NotEmpty(t, enrollment.Secret)
	assert.NotEmpty(t, enrollment.ProvisioningURI)
	assert.False(t, enrollment.Verified)
	assert.False(t, enrollment.CreatedAt.IsZero())
	assert.False(t, enrollment.ExpiresAt.IsZero())

	// Expires at should be ~15 minutes from creation
	expectedExpiry := enrollment.CreatedAt.Add(15 * time.Minute)
	assert.WithinDuration(t, expectedExpiry, enrollment.ExpiresAt, time.Second)

	// Provisioning URI should contain the secret
	assert.Contains(t, enrollment.ProvisioningURI, enrollment.Secret)
}

func TestMFAProvider_VerifyEnrollment(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")
	userID := "test@example.com"

	enrollment, err := provider.NewEnrollment(userID)
	require.NoError(t, err)

	// Generate valid token
	token, err := provider.GenerateToken(enrollment.Secret)
	require.NoError(t, err)

	// Should verify with valid token
	valid, err := provider.VerifyEnrollment(enrollment, token)
	assert.NoError(t, err)
	assert.True(t, valid)
	assert.True(t, enrollment.Verified)

	// Should reject invalid token
	enrollment2, err := provider.NewEnrollment(userID)
	require.NoError(t, err)

	valid, err = provider.VerifyEnrollment(enrollment2, "000000")
	assert.Error(t, err)
	assert.False(t, valid)
	assert.False(t, enrollment2.Verified)
}

func TestMFAProvider_VerifyEnrollment_Expired(t *testing.T) {
	provider := NewMFAProvider("vCLI-Test")
	userID := "test@example.com"

	enrollment, err := provider.NewEnrollment(userID)
	require.NoError(t, err)

	// Simulate expired enrollment
	enrollment.ExpiresAt = time.Now().Add(-1 * time.Minute)

	// Generate valid token
	token, err := provider.GenerateToken(enrollment.Secret)
	require.NoError(t, err)

	// Should reject even with valid token if expired
	valid, err := provider.VerifyEnrollment(enrollment, token)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "expired")
	assert.False(t, valid)
	assert.False(t, enrollment.Verified)
}

func TestDefaultMFAConfig(t *testing.T) {
	config := DefaultMFAConfig()

	assert.True(t, config.Enabled)
	assert.Contains(t, config.EnforcedForRoles, "admin")
	assert.Contains(t, config.EnforcedForRoles, "operator")
	assert.Equal(t, 24*time.Hour, config.GracePeriod)
	assert.Equal(t, 3, config.MaxAttempts)
	assert.Equal(t, 15*time.Minute, config.LockoutDuration)
}

func TestMFAConfig_RequiresMFA(t *testing.T) {
	tests := []struct {
		name     string
		config   *MFAConfig
		roles    []string
		expected bool
	}{
		{
			name: "Disabled MFA",
			config: &MFAConfig{
				Enabled:          false,
				EnforcedForRoles: []string{"admin"},
			},
			roles:    []string{"admin"},
			expected: false,
		},
		{
			name: "Admin role requires MFA",
			config: &MFAConfig{
				Enabled:          true,
				EnforcedForRoles: []string{"admin", "operator"},
			},
			roles:    []string{"admin"},
			expected: true,
		},
		{
			name: "Viewer role does not require MFA",
			config: &MFAConfig{
				Enabled:          true,
				EnforcedForRoles: []string{"admin", "operator"},
			},
			roles:    []string{"viewer"},
			expected: false,
		},
		{
			name: "Multiple roles, one requires MFA",
			config: &MFAConfig{
				Enabled:          true,
				EnforcedForRoles: []string{"admin"},
			},
			roles:    []string{"viewer", "admin"},
			expected: true,
		},
		{
			name: "Empty enforcement list means all require MFA",
			config: &MFAConfig{
				Enabled:          true,
				EnforcedForRoles: []string{},
			},
			roles:    []string{"any-role"},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.config.RequiresMFA(tt.roles)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// Benchmark tests
func BenchmarkMFAProvider_GenerateSecret(b *testing.B) {
	provider := NewMFAProvider("vCLI-Bench")
	for i := 0; i < b.N; i++ {
		_, _ = provider.GenerateSecret("test@example.com")
	}
}

func BenchmarkMFAProvider_ValidateToken(b *testing.B) {
	provider := NewMFAProvider("vCLI-Bench")
	secret := "JBSWY3DPEHPK3PXP"
	token, _ := totp.GenerateCode(secret, time.Now())

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = provider.ValidateToken(secret, token)
	}
}

func BenchmarkMFAProvider_NewEnrollment(b *testing.B) {
	provider := NewMFAProvider("vCLI-Bench")
	for i := 0; i < b.N; i++ {
		_, _ = provider.NewEnrollment("test@example.com")
	}
}
