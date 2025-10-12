// Package auth provides Layer 1 (Authentication) of Guardian Zero Trust Security.
//
// "Who are you?" - Irrefutable proof of identity before any processing.
//
// The auth package implements complete authentication orchestration including:
// - Multi-factor authentication (TOTP)
// - Cryptographic key management (Ed25519)
// - JWT session management
// - Device fingerprinting and trust
// - Context-aware authentication decisions
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)
// Date: 2025-10-12
package auth

import (
	"time"
)

// AuthContext represents complete authentication state for a user session.
// This is the primary artifact passed between security layers in the Guardian architecture.
//
// AuthContext serves as a "passport" - containing all necessary information about
// who the user is, how they authenticated, and what context surrounds their session.
type AuthContext struct {
	// Identity Information
	UserID   string `json:"user_id"`
	Username string `json:"username"`
	Email    string `json:"email,omitempty"`

	// Authorization Hints (populated by Layer 2 - Authorization)
	Roles       []string `json:"roles"`
	Permissions []string `json:"permissions,omitempty"`

	// Session Information
	SessionID    string    `json:"session_id"`
	SessionToken string    `json:"session_token"`
	RefreshToken string    `json:"refresh_token,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
	ExpiresAt    time.Time `json:"expires_at"`

	// Authentication Method & Security Context
	AuthMethod        AuthMethod   `json:"auth_method"`
	MFACompleted      bool         `json:"mfa_completed"`
	MFAMethod         string       `json:"mfa_method,omitempty"` // "totp", "sms", "email"
	DeviceFingerprint string       `json:"device_fingerprint"`
	DeviceTrusted     bool         `json:"device_trusted"`
	IPAddress         string       `json:"ip_address"`
	GeoLocation       *GeoLocation `json:"geo_location,omitempty"`
	UserAgent         string       `json:"user_agent,omitempty"`

	// State & Flags
	Verified       bool      `json:"verified"`
	RequiresMFA    bool      `json:"requires_mfa"`
	RequiresReauth bool      `json:"requires_reauth"`
	LastActivity   time.Time `json:"last_activity"`

	// Risk Signals (used by Layer 6 - Behavioral Analysis)
	RiskScore      float64  `json:"risk_score,omitempty"`      // 0.0 (safe) - 1.0 (high risk)
	AnomalyFactors []string `json:"anomaly_factors,omitempty"` // Detected anomalies
}

// AuthMethod represents how the user authenticated.
type AuthMethod string

const (
	// AuthMethodPassword represents username/password authentication
	AuthMethodPassword AuthMethod = "password"

	// AuthMethodAPIKey represents API key authentication
	AuthMethodAPIKey AuthMethod = "apikey"

	// AuthMethodCertificate represents client certificate authentication
	AuthMethodCertificate AuthMethod = "certificate"

	// AuthMethodOAuth represents OAuth 2.0 authentication
	AuthMethodOAuth AuthMethod = "oauth"

	// AuthMethodSSO represents Single Sign-On authentication
	AuthMethodSSO AuthMethod = "sso"
)

// GeoLocation represents user geographic location.
// Used for geo-fencing and anomaly detection.
type GeoLocation struct {
	Country   string  `json:"country"`
	Region    string  `json:"region"`
	City      string  `json:"city"`
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	ISP       string  `json:"isp,omitempty"`
}

// Credentials represents user authentication credentials.
// Contains all information needed to authenticate a user.
type Credentials struct {
	// Primary credentials
	Username string
	Password string
	APIKey   string

	// Multi-factor authentication
	MFAToken string

	// Authentication method
	Method AuthMethod
}

// AuthConfig configures the Authenticator behavior.
// Provides policy controls for authentication decisions.
type AuthConfig struct {
	// Component Dependencies
	MFAProvider    *MFAProvider
	KeyManager     *CryptoKeyManager
	SessionManager *SessionManager

	// Session Policies
	SessionDuration       time.Duration // Default session duration
	RefreshEnabled        bool          // Allow refresh tokens
	MaxConcurrentSessions int           // 0 = unlimited

	// MFA Policies
	RequireMFAForRoles []string // Roles that always require MFA
	MFASkewTolerance   uint     // Time skew tolerance for TOTP (seconds)

	// Device Trust Policies
	DeviceTrustEnabled bool // Enable device fingerprinting and trust

	// Security Enforcement
	EnforceIPMatch     bool     // Require IP to match throughout session
	EnforceDeviceMatch bool     // Require device fingerprint match
	GeoFencingEnabled  bool     // Check geographic restrictions
	AllowedCountries   []string // If geo-fencing enabled

	// Rate Limiting (prepared for Layer 5)
	MaxAuthAttempts      int           // Max failed attempts before lockout
	LockoutDuration      time.Duration // How long to lock out after max attempts
	RateLimitWindow      time.Duration // Time window for rate limiting
	MaxRequestsPerWindow int           // Max requests in rate limit window
}

// AuthenticationResult represents the outcome of an authentication attempt.
type AuthenticationResult struct {
	// Outcome
	Success bool
	Error   error

	// If successful
	AuthContext *AuthContext

	// If MFA required
	RequiresMFA  bool
	MFAChallenge *MFAChallenge
}

// MFAChallenge represents an MFA challenge issued to user.
// Contains information needed to complete the MFA flow.
type MFAChallenge struct {
	ChallengeID string    // Unique challenge identifier
	Method      string    // "totp", "sms", "email"
	ExpiresAt   time.Time // When challenge expires
	Attempts    int       // Current attempt count
	MaxAttempts int       // Maximum allowed attempts
}

// ValidationResult represents session validation outcome.
// Returned when validating an existing session token.
type ValidationResult struct {
	// Validation outcome
	Valid bool
	Error error

	// If valid
	AuthContext *AuthContext

	// Required actions
	RequiresAction string // "mfa", "reauth", "renew", "" (none)
}

// IsValid checks if the AuthContext is valid (not expired).
func (ac *AuthContext) IsValid() bool {
	if !ac.Verified {
		return false
	}
	return time.Now().Before(ac.ExpiresAt)
}

// IsExpiringSoon checks if session will expire within the given duration.
// Useful for proactive refresh.
func (ac *AuthContext) IsExpiringSoon(within time.Duration) bool {
	return time.Until(ac.ExpiresAt) < within
}

// HasRole checks if the user has a specific role.
func (ac *AuthContext) HasRole(role string) bool {
	for _, r := range ac.Roles {
		if r == role {
			return true
		}
	}
	return false
}

// HasAnyRole checks if the user has any of the specified roles.
func (ac *AuthContext) HasAnyRole(roles ...string) bool {
	for _, role := range roles {
		if ac.HasRole(role) {
			return true
		}
	}
	return false
}

// HasPermission checks if the user has a specific permission.
func (ac *AuthContext) HasPermission(permission string) bool {
	for _, p := range ac.Permissions {
		if p == permission {
			return true
		}
	}
	return false
}

// UpdateActivity updates the last activity timestamp to now.
func (ac *AuthContext) UpdateActivity() {
	ac.LastActivity = time.Now()
}

// IsHighRisk checks if the session is considered high risk.
// Threshold: 0.7 or above is considered high risk.
func (ac *AuthContext) IsHighRisk() bool {
	return ac.RiskScore >= 0.7
}

// IsMediumRisk checks if the session is considered medium risk.
// Threshold: 0.4-0.69 is considered medium risk.
func (ac *AuthContext) IsMediumRisk() bool {
	return ac.RiskScore >= 0.4 && ac.RiskScore < 0.7
}

// SessionRemaining returns the time remaining until session expires.
func (ac *AuthContext) SessionRemaining() time.Duration {
	return time.Until(ac.ExpiresAt)
}

// SessionAge returns how long the session has been active.
func (ac *AuthContext) SessionAge() time.Duration {
	return time.Since(ac.CreatedAt)
}

// String returns a safe string representation of AuthContext.
// Does not include sensitive information like tokens.
func (ac *AuthContext) String() string {
	return "AuthContext{UserID:" + ac.UserID +
		", Username:" + ac.Username +
		", Verified:" + boolToString(ac.Verified) +
		", MFACompleted:" + boolToString(ac.MFACompleted) +
		", DeviceTrusted:" + boolToString(ac.DeviceTrusted) +
		"}"
}

// Helper function for String()
func boolToString(b bool) string {
	if b {
		return "true"
	}
	return "false"
}
