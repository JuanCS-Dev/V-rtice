// Package auth implements Layer 1 of the Guardian: Authentication
//
// "Who are you?" - Irrefutable proof of identity before any processing.
//
// Components:
// - MFA (Multi-Factor Authentication) using TOTP
// - Cryptographic keys (Ed25519)
// - JWT session management
// - Credential revocation
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)
// Date: 2025-10-12
package auth

import (
	"crypto/rand"
	"encoding/base32"
	"fmt"
	"time"

	"github.com/pquerna/otp/totp"
)

// MFAProvider handles multi-factor authentication using TOTP (Time-based One-Time Password).
// It provides QR code provisioning for authenticator apps like Google Authenticator.
type MFAProvider struct {
	// issuer is the name shown in authenticator apps
	issuer string

	// digits is the number of digits in the OTP (default 6)
	digits int

	// period is the time step in seconds (default 30)
	period uint
}

// NewMFAProvider creates a new MFA provider with default settings.
func NewMFAProvider(issuer string) *MFAProvider {
	return &MFAProvider{
		issuer: issuer,
		digits: 6,
		period: 30,
	}
}

// GenerateSecret creates a new TOTP secret for a user.
// The secret should be stored securely and associated with the user.
//
// Returns:
//   - secret: Base32-encoded secret string
//   - error: nil on success
func (m *MFAProvider) GenerateSecret(userID string) (string, error) {
	// Generate 20 random bytes (160 bits) for security
	secretBytes := make([]byte, 20)
	if _, err := rand.Read(secretBytes); err != nil {
		return "", fmt.Errorf("failed to generate random secret: %w", err)
	}

	// Encode as Base32 (standard for TOTP secrets)
	secret := base32.StdEncoding.EncodeToString(secretBytes)
	return secret, nil
}

// ValidateToken verifies a TOTP token against a secret.
//
// Parameters:
//   - secret: The user's Base32-encoded TOTP secret
//   - token: The 6-digit OTP token from authenticator app
//
// Returns:
//   - bool: true if token is valid
//   - error: nil on success, error if validation fails
func (m *MFAProvider) ValidateToken(secret, token string) (bool, error) {
	// Validate token using TOTP algorithm
	valid := totp.Validate(token, secret)
	if !valid {
		return false, fmt.Errorf("invalid MFA token")
	}
	return true, nil
}

// ValidateTokenWithSkew validates a token with time skew tolerance.
// This allows for clock drift between client and server.
//
// Parameters:
//   - secret: The user's Base32-encoded TOTP secret
//   - token: The 6-digit OTP token
//   - skew: Number of time steps to check (e.g., 1 = ±30 seconds)
//
// Returns:
//   - bool: true if token is valid within skew window
//   - error: nil on success
func (m *MFAProvider) ValidateTokenWithSkew(secret, token string, skew uint) (bool, error) {
	// Check current time window
	if totp.Validate(token, secret) {
		return true, nil
	}

	// Check past windows within skew
	for i := uint(1); i <= skew; i++ {
		pastTime := time.Now().Add(-time.Duration(i*m.period) * time.Second)
		pastToken, err := totp.GenerateCode(secret, pastTime)
		if err != nil {
			return false, fmt.Errorf("failed to generate past token: %w", err)
		}
		if token == pastToken {
			return true, nil
		}
	}

	// Check future windows within skew
	for i := uint(1); i <= skew; i++ {
		futureTime := time.Now().Add(time.Duration(i*m.period) * time.Second)
		futureToken, err := totp.GenerateCode(secret, futureTime)
		if err != nil {
			return false, fmt.Errorf("failed to generate future token: %w", err)
		}
		if token == futureToken {
			return true, nil
		}
	}

	return false, fmt.Errorf("invalid MFA token (checked with skew=%d)", skew)
}

// ProvisioningURI generates a QR code URI for authenticator apps.
// This URI can be converted to a QR code for easy scanning.
//
// Parameters:
//   - userID: User identifier (e.g., email or username)
//   - secret: The Base32-encoded TOTP secret
//
// Returns:
//   - string: otpauth:// URI for QR code generation
func (m *MFAProvider) ProvisioningURI(userID, secret string) string {
	return fmt.Sprintf(
		"otpauth://totp/%s:%s?secret=%s&issuer=%s&digits=%d&period=%d",
		m.issuer,
		userID,
		secret,
		m.issuer,
		m.digits,
		m.period,
	)
}

// GenerateToken generates a TOTP token for testing purposes.
// WARNING: This should only be used in tests, never in production.
func (m *MFAProvider) GenerateToken(secret string) (string, error) {
	token, err := totp.GenerateCode(secret, time.Now())
	if err != nil {
		return "", fmt.Errorf("failed to generate token: %w", err)
	}
	return token, nil
}

// MFAEnrollment represents an MFA enrollment session.
type MFAEnrollment struct {
	// UserID is the user being enrolled
	UserID string

	// Secret is the generated TOTP secret
	Secret string

	// ProvisioningURI is the QR code URI
	ProvisioningURI string

	// CreatedAt is when the enrollment was created
	CreatedAt time.Time

	// ExpiresAt is when the enrollment expires (typically 15 minutes)
	ExpiresAt time.Time

	// Verified indicates if the user has verified with a valid token
	Verified bool
}

// NewEnrollment creates a new MFA enrollment for a user.
func (m *MFAProvider) NewEnrollment(userID string) (*MFAEnrollment, error) {
	// Generate secret
	secret, err := m.GenerateSecret(userID)
	if err != nil {
		return nil, fmt.Errorf("failed to generate secret: %w", err)
	}

	// Create provisioning URI
	uri := m.ProvisioningURI(userID, secret)

	// Create enrollment with 15-minute expiry
	enrollment := &MFAEnrollment{
		UserID:          userID,
		Secret:          secret,
		ProvisioningURI: uri,
		CreatedAt:       time.Now(),
		ExpiresAt:       time.Now().Add(15 * time.Minute),
		Verified:        false,
	}

	return enrollment, nil
}

// VerifyEnrollment verifies an enrollment by validating a token.
// This should be called after the user scans the QR code.
func (m *MFAProvider) VerifyEnrollment(enrollment *MFAEnrollment, token string) (bool, error) {
	// Check if enrollment has expired
	if time.Now().After(enrollment.ExpiresAt) {
		return false, fmt.Errorf("enrollment expired")
	}

	// Validate token with generous skew (for first-time setup)
	valid, err := m.ValidateTokenWithSkew(enrollment.Secret, token, 2)
	if err != nil {
		return false, err
	}

	if valid {
		enrollment.Verified = true
	}

	return valid, nil
}

// MFAConfig holds MFA configuration options.
type MFAConfig struct {
	// Enabled indicates if MFA is required
	Enabled bool

	// EnforcedForRoles lists roles that require MFA
	EnforcedForRoles []string

	// GracePeriod is how long a session can last without re-MFA
	GracePeriod time.Duration

	// MaxAttempts is maximum failed attempts before lockout
	MaxAttempts int

	// LockoutDuration is how long to lock out after max attempts
	LockoutDuration time.Duration
}

// DefaultMFAConfig returns default MFA configuration.
func DefaultMFAConfig() *MFAConfig {
	return &MFAConfig{
		Enabled:          true,
		EnforcedForRoles: []string{"admin", "operator"},
		GracePeriod:      24 * time.Hour,
		MaxAttempts:      3,
		LockoutDuration:  15 * time.Minute,
	}
}

// RequiresMFA checks if MFA is required for given roles.
func (c *MFAConfig) RequiresMFA(roles []string) bool {
	if !c.Enabled {
		return false
	}

	// If no enforcement list, MFA required for everyone
	if len(c.EnforcedForRoles) == 0 {
		return true
	}

	// Check if any user role is in enforcement list
	for _, userRole := range roles {
		for _, enforcedRole := range c.EnforcedForRoles {
			if userRole == enforcedRole {
				return true
			}
		}
	}

	return false
}
