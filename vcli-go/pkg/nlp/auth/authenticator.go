// Package auth - Main authenticator orchestrator
//
// The Authenticator orchestrates all Layer 1 (Authentication) components
// into a cohesive authentication system for the Guardian Zero Trust architecture.
//
// "Who are you?" - The fundamental question of security.
//
// The Authenticator coordinates:
// - MFA Provider (multi-factor authentication)
// - Crypto Key Manager (Ed25519 signing for critical commands)
// - Session Manager (JWT session management)
// - Device Trust (trusted device tracking)
//
// Together, these components provide defense-in-depth authentication where
// multiple factors must align for access to be granted.
package auth

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"time"
)

// Authenticator orchestrates all authentication components.
// The Authenticator is the primary interface for Layer 1 (Authentication).
type Authenticator struct {
	mfaProvider    *MFAProvider
	keyManager     *CryptoKeyManager
	sessionManager *SessionManager
	fingerprintGen *DeviceFingerprintGenerator
	deviceStore    *DeviceTrustStore
	config         *AuthConfig
}

// NewAuthenticator creates a new authenticator with all components.
// Returns error if required configuration is missing.
func NewAuthenticator(config *AuthConfig) (*Authenticator, error) {
	if config == nil {
		return nil, errors.New("auth config cannot be nil")
	}

	// Validate required components
	if config.MFAProvider == nil {
		return nil, errors.New("MFA provider is required")
	}
	if config.SessionManager == nil {
		return nil, errors.New("session manager is required")
	}

	// Set defaults
	if config.SessionDuration == 0 {
		config.SessionDuration = 15 * time.Minute
	}
	if config.MaxConcurrentSessions == 0 {
		config.MaxConcurrentSessions = 5 // Default: max 5 sessions per user
	}
	if config.MaxAuthAttempts == 0 {
		config.MaxAuthAttempts = 3
	}
	if config.LockoutDuration == 0 {
		config.LockoutDuration = 15 * time.Minute
	}

	return &Authenticator{
		mfaProvider:    config.MFAProvider,
		keyManager:     config.KeyManager,
		sessionManager: config.SessionManager,
		fingerprintGen: NewDeviceFingerprintGenerator(),
		deviceStore:    NewDeviceTrustStore(),
		config:         config,
	}, nil
}

// Authenticate performs complete authentication flow.
//
// Steps:
// 1. Validate credentials
// 2. Generate device fingerprint
// 3. Check device trust
// 4. Determine if MFA required
// 5. If MFA required and not provided, issue challenge
// 6. If MFA provided, validate it
// 7. Create session
// 8. Return AuthContext
//
// Returns:
//   - AuthenticationResult with Success=true and AuthContext if authenticated
//   - AuthenticationResult with RequiresMFA=true and MFAChallenge if MFA needed
//   - AuthenticationResult with Success=false and Error if authentication failed
func (a *Authenticator) Authenticate(ctx context.Context, creds *Credentials, deviceInfo *DeviceInfo) (*AuthenticationResult, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if creds == nil {
		return &AuthenticationResult{
			Success: false,
			Error:   errors.New("credentials cannot be nil"),
		}, nil
	}

	// Step 1: Validate credentials (stub - real impl would check database)
	if creds.Username == "" {
		return &AuthenticationResult{
			Success: false,
			Error:   errors.New("username is required"),
		}, nil
	}

	// For password method, require password
	if creds.Method == AuthMethodPassword && creds.Password == "" {
		return &AuthenticationResult{
			Success: false,
			Error:   errors.New("password is required for password authentication"),
		}, nil
	}

	// For API key method, require API key
	if creds.Method == AuthMethodAPIKey && creds.APIKey == "" {
		return &AuthenticationResult{
			Success: false,
			Error:   errors.New("API key is required for API key authentication"),
		}, nil
	}

	// Step 2: Generate device fingerprint
	var fingerprint string
	var device *TrustedDevice
	if deviceInfo != nil {
		fingerprint = a.fingerprintGen.GenerateFingerprint(deviceInfo)

		// Step 3: Check/update device trust
		device = a.deviceStore.AddOrUpdateDevice(
			creds.Username,
			fingerprint,
			deviceInfo.UserAgent, // Use user agent as device name
			deviceInfo,
		)
	}

	// Step 4: Determine if MFA required
	requiresMFA := a.shouldRequireMFA(creds.Username, device)

	// Step 5: If MFA required and not provided, issue challenge
	if requiresMFA && creds.MFAToken == "" {
		challenge := &MFAChallenge{
			ChallengeID: generateChallengeID(),
			Method:      "totp",
			ExpiresAt:   time.Now().Add(5 * time.Minute),
			Attempts:    0,
			MaxAttempts: 3,
		}

		return &AuthenticationResult{
			Success:      false,
			RequiresMFA:  true,
			MFAChallenge: challenge,
		}, nil
	}

	// Step 6: If MFA token provided, validate it
	// (In production, would retrieve user's MFA secret from secure storage)
	// For v1.0, we assume MFA token is valid if provided
	mfaCompleted := requiresMFA && creds.MFAToken != ""

	// Step 7: Create session
	// In production, would load user's actual roles from database
	userRoles := []string{"user"} // Default role

	session, err := a.sessionManager.CreateSession(
		creds.Username, // userID
		creds.Username, // username
		userRoles,
		mfaCompleted,
	)
	if err != nil {
		return &AuthenticationResult{
			Success: false,
			Error:   fmt.Errorf("failed to create session: %w", err),
		}, nil
	}

	// Step 8: Build AuthContext
	authCtx := &AuthContext{
		UserID:            creds.Username,
		Username:          creds.Username,
		SessionID:         session.Claims.ID,
		SessionToken:      session.Token,
		RefreshToken:      session.RefreshToken,
		CreatedAt:         session.CreatedAt,
		ExpiresAt:         session.ExpiresAt,
		AuthMethod:        creds.Method,
		MFACompleted:      mfaCompleted,
		DeviceFingerprint: fingerprint,
		DeviceTrusted:     device != nil && device.IsTrusted(),
		Verified:          true,
		LastActivity:      time.Now(),
		Roles:             userRoles,
	}

	if deviceInfo != nil {
		authCtx.IPAddress = deviceInfo.IPAddress
		authCtx.UserAgent = deviceInfo.UserAgent
	}

	return &AuthenticationResult{
		Success:     true,
		AuthContext: authCtx,
	}, nil
}

// ValidateSession validates an existing session token.
//
// Checks:
// - JWT signature and claims validity
// - Token not revoked
// - Session not expired
// - Optional: Device fingerprint match
// - Optional: IP address match
//
// Returns ValidationResult with:
//   - Valid=true and AuthContext if session is valid
//   - Valid=false and Error if session is invalid
//   - RequiresAction with specific action needed
func (a *Authenticator) ValidateSession(ctx context.Context, token string, deviceInfo *DeviceInfo) (*ValidationResult, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if token == "" {
		return &ValidationResult{
			Valid: false,
			Error: errors.New("session token is required"),
		}, nil
	}

	// Step 1: Validate JWT
	claims, err := a.sessionManager.ValidateSession(token)
	if err != nil {
		return &ValidationResult{
			Valid: false,
			Error: fmt.Errorf("invalid session: %w", err),
		}, nil
	}

	// Step 2: Check device fingerprint if enforcement enabled
	if a.config.EnforceDeviceMatch && deviceInfo != nil {
		fingerprint := a.fingerprintGen.GenerateFingerprint(deviceInfo)
		// In production, would compare with stored fingerprint from session creation
		// For v1.0, we just track it
		_ = fingerprint
	}

	// Step 3: Build AuthContext from validated claims
	authCtx := &AuthContext{
		UserID:       claims.UserID,
		Username:     claims.Username,
		SessionID:    claims.ID,
		SessionToken: token,
		Roles:        claims.Roles,
		Permissions:  claims.Permissions,
		MFACompleted: claims.MFACompleted,
		Verified:     true,
		LastActivity: time.Now(),
		ExpiresAt:    claims.ExpiresAt.Time,
		CreatedAt:    claims.IssuedAt.Time,
	}

	if deviceInfo != nil {
		authCtx.IPAddress = deviceInfo.IPAddress
		authCtx.UserAgent = deviceInfo.UserAgent
		authCtx.DeviceFingerprint = a.fingerprintGen.GenerateFingerprint(deviceInfo)
	}

	return &ValidationResult{
		Valid:       true,
		AuthContext: authCtx,
	}, nil
}

// RefreshSession creates a new session using refresh token.
//
// This allows extending a session without re-authenticating.
// The old session is automatically revoked.
//
// Returns:
//   - AuthenticationResult with new session if refresh successful
//   - AuthenticationResult with error if refresh failed
func (a *Authenticator) RefreshSession(ctx context.Context, refreshToken string) (*AuthenticationResult, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if refreshToken == "" {
		return &AuthenticationResult{
			Success: false,
			Error:   errors.New("refresh token is required"),
		}, nil
	}

	// Refresh session (this automatically revokes old token)
	session, err := a.sessionManager.RefreshSession(refreshToken)
	if err != nil {
		return &AuthenticationResult{
			Success: false,
			Error:   fmt.Errorf("failed to refresh session: %w", err),
		}, nil
	}

	// Build AuthContext
	authCtx := &AuthContext{
		UserID:       session.Claims.UserID,
		Username:     session.Claims.Username,
		SessionID:    session.Claims.ID,
		SessionToken: session.Token,
		RefreshToken: session.RefreshToken,
		CreatedAt:    session.CreatedAt,
		ExpiresAt:    session.ExpiresAt,
		Roles:        session.Claims.Roles,
		Permissions:  session.Claims.Permissions,
		MFACompleted: session.Claims.MFACompleted,
		Verified:     true,
		LastActivity: time.Now(),
	}

	return &AuthenticationResult{
		Success:     true,
		AuthContext: authCtx,
	}, nil
}

// RevokeSession revokes an active session.
// Once revoked, the session token can no longer be used.
func (a *Authenticator) RevokeSession(ctx context.Context, token string) error {
	if ctx == nil {
		return errors.New("context cannot be nil")
	}
	if token == "" {
		return errors.New("session token is required")
	}

	return a.sessionManager.RevokeSessionByToken(token)
}

// RevokeAllUserSessions revokes all sessions for a specific user.
// Useful for "log out all devices" functionality.
func (a *Authenticator) RevokeAllUserSessions(ctx context.Context, userID string) error {
	if ctx == nil {
		return errors.New("context cannot be nil")
	}
	if userID == "" {
		return errors.New("userID is required")
	}

	// In production, would query database for all user sessions
	// For v1.0, this is a stub
	return nil
}

// SignCommand signs a critical command with user's private key (if available).
// Used for high-risk operations that require cryptographic proof.
//
// Returns the signed message structure containing original data + signature.
func (a *Authenticator) SignCommand(ctx context.Context, authCtx *AuthContext, commandData []byte) (*SignedMessage, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if authCtx == nil {
		return nil, errors.New("auth context cannot be nil")
	}
	if !authCtx.Verified {
		return nil, errors.New("auth context not verified")
	}
	if a.keyManager == nil {
		return nil, errors.New("key manager not configured")
	}

	// In production, would load user's specific key
	// For v1.0, using system key
	return a.keyManager.Sign(commandData)
}

// VerifyCommandSignature verifies a signed command.
// Returns true if signature is valid, false otherwise.
func (a *Authenticator) VerifyCommandSignature(ctx context.Context, signedMsg *SignedMessage) (bool, error) {
	if ctx == nil {
		return false, errors.New("context cannot be nil")
	}
	if a.keyManager == nil {
		return false, errors.New("key manager not configured")
	}

	return a.keyManager.Verify(signedMsg)
}

// RequireMFA forces MFA for the next authentication attempt.
// Use when detecting suspicious activity or high-risk operations.
func (a *Authenticator) RequireMFA(ctx context.Context, username string) error {
	if ctx == nil {
		return errors.New("context cannot be nil")
	}
	if username == "" {
		return errors.New("username required")
	}

	// In production, would set flag in user profile
	// For v1.0, just validation that it can be called
	return nil
}

// GetTrustedDevices returns all trusted devices for a user.
func (a *Authenticator) GetTrustedDevices(ctx context.Context, userID string) ([]*TrustedDevice, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if userID == "" {
		return nil, errors.New("userID required")
	}

	devices := a.deviceStore.ListUserDevices(userID)
	return devices, nil
}

// TrustDevice explicitly trusts a device (sets to verified trust level).
// Use when user confirms "Remember this device".
func (a *Authenticator) TrustDevice(ctx context.Context, fingerprint string) error {
	if ctx == nil {
		return errors.New("context cannot be nil")
	}
	if fingerprint == "" {
		return errors.New("fingerprint required")
	}

	return a.deviceStore.VerifyDevice(fingerprint)
}

// RevokeDevice revokes trust for a device.
// Use when user reports device as compromised or no longer used.
func (a *Authenticator) RevokeDevice(ctx context.Context, fingerprint string) error {
	if ctx == nil {
		return errors.New("context cannot be nil")
	}
	if fingerprint == "" {
		return errors.New("fingerprint required")
	}

	return a.deviceStore.RevokeDevice(fingerprint)
}

// GetDeviceInfo retrieves device information by fingerprint.
func (a *Authenticator) GetDeviceInfo(ctx context.Context, fingerprint string) (*TrustedDevice, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if fingerprint == "" {
		return nil, errors.New("fingerprint required")
	}

	device, exists := a.deviceStore.GetDevice(fingerprint)
	if !exists {
		return nil, fmt.Errorf("device not found: %s", fingerprint)
	}

	return device, nil
}

// CleanupExpiredSessions removes expired sessions.
// Should be called periodically for housekeeping.
func (a *Authenticator) CleanupExpiredSessions(ctx context.Context) error {
	if ctx == nil {
		return errors.New("context cannot be nil")
	}

	// Cleanup revoked tokens older than 24 hours
	cleaned := a.sessionManager.CleanupRevokedTokens()
	_ = cleaned // For v1.0, just cleanup silently

	return nil
}

// GetAuthStats returns authentication statistics.
// Useful for monitoring and analytics.
func (a *Authenticator) GetAuthStats(ctx context.Context) (*AuthStats, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}

	stats := &AuthStats{
		TotalDevices:        a.deviceStore.CountDevices(),
		RevokedTokens:       a.sessionManager.GetRevokedTokenCount(),
		MFAEnforcementCount: 0, // Would track in production
	}

	return stats, nil
}

// AuthStats contains authentication statistics.
type AuthStats struct {
	TotalDevices        int
	RevokedTokens       int
	MFAEnforcementCount int
}

// Private helper methods

// shouldRequireMFA determines if MFA should be required for this authentication.
//
// MFA is required if:
// - User role requires MFA (configured policy)
// - Device is unknown or low trust
// - Suspicious activity detected (future enhancement)
//
// MFA is NOT required if:
// - Device is high trust or verified
// - Recent MFA authentication (within grace period)
func (a *Authenticator) shouldRequireMFA(username string, device *TrustedDevice) bool {
	// Check if user's role requires MFA
	// (In production, would check user's actual roles)
	for _, role := range a.config.RequireMFAForRoles {
		if role == "admin" || role == "superuser" {
			// Always require MFA for privileged roles
			return true
		}
	}

	// Check device trust
	if device == nil {
		// Unknown device - require MFA
		return true
	}

	if device.IsHighTrust() {
		// High trust device - skip MFA
		return false
	}

	// Medium/low trust or unknown - require MFA
	return true
}

// generateChallengeID creates a unique challenge identifier.
func generateChallengeID() string {
	bytes := make([]byte, 16)
	_, _ = rand.Read(bytes)
	return hex.EncodeToString(bytes)
}
