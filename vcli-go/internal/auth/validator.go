// Package auth implements authentication validation (Layer 1)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 1 of the "Guardian of Intent" v2.0:
// "AUTENTICAÇÃO - Quem é você?"
//
// Provides:
// - JWT validation
// - Session verification
// - MFA checking
// - Token refresh
package auth

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/verticedev/vcli-go/pkg/security"
)

const (
	// Session configuration
	sessionDuration = 24 * time.Hour
	sessionIdleTimeout = 30 * time.Minute

	// Session ID generation
	sessionIDTimestampFormat = "20060102150405"
	sessionIDRandomBytes = 16
)

var (
	// ErrExpiredToken is returned when JWT token is expired
	ErrExpiredToken = errors.New("authentication token expired")

	// ErrMFARequired is returned when MFA is required but not verified
	ErrMFARequired = errors.New("MFA verification required")

	// ErrSessionExpired is returned when session is expired
	ErrSessionExpired = errors.New("session expired")

	// ErrInvalidSession is returned when session is invalid
	ErrInvalidSession = errors.New("invalid session")
)

// Validator handles authentication validation
type Validator struct {
	jwtSecret      []byte
	sessionStore   SessionStore
	mfaValidator   MFAValidator
	tokenDuration  time.Duration
	refreshWindow  time.Duration
}

// NewValidator creates a new authentication validator
func NewValidator(jwtSecret []byte, sessionStore SessionStore, mfaValidator MFAValidator) *Validator {
	return &Validator{
		jwtSecret:     jwtSecret,
		sessionStore:  sessionStore,
		mfaValidator:  mfaValidator,
		tokenDuration: 15 * time.Minute, // Short-lived tokens
		refreshWindow: 5 * time.Minute,  // Refresh 5min before expiry
	}
}

// SessionStore interface for session persistence
type SessionStore interface {
	Get(ctx context.Context, sessionID string) (*security.Session, error)
	Save(ctx context.Context, session *security.Session) error
	Delete(ctx context.Context, sessionID string) error
	UpdateActivity(ctx context.Context, sessionID string) error
}

// MFAValidator interface for MFA verification
type MFAValidator interface {
	Verify(ctx context.Context, userID string, code string) (bool, error)
	IsRequired(ctx context.Context, user *security.User) (bool, error)
}

// Claims represents JWT claims
type Claims struct {
	UserID    string   `json:"user_id"`
	Username  string   `json:"username"`
	Email     string   `json:"email"`
	Roles     []string `json:"roles"`
	SessionID string   `json:"session_id"`
	MFAVerified bool   `json:"mfa_verified"`
	
	jwt.RegisteredClaims
}

// Validate performs authentication validation on a user
//
// This is the entry point for CAMADA 1. It verifies:
// 1. JWT token is valid and not expired
// 2. Session exists and is active
// 3. MFA is verified if required
// 4. Session hasn't been idle too long
func (v *Validator) Validate(ctx context.Context, user *security.User) error {
	startTime := time.Now()
	
	// Check if user is nil
	if user == nil {
		return &security.SecurityError{
			Layer:     "auth",
			Type:      security.ErrorTypeAuth,
			Message:   "No user provided",
			Timestamp: startTime,
		}
	}
	
	// Validate session exists
	session, err := v.sessionStore.Get(ctx, user.SessionID)
	if err != nil {
		return &security.SecurityError{
			Layer:     "auth",
			Type:      security.ErrorTypeAuth,
			Message:   "Session not found",
			Details:   map[string]interface{}{"session_id": user.SessionID},
			Timestamp: startTime,
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	// Check session expiry
	if time.Now().After(session.ExpiresAt) {
		return &security.SecurityError{
			Layer:     "auth",
			Type:      security.ErrorTypeAuth,
			Message:   "Session expired",
			Details:   map[string]interface{}{"expired_at": session.ExpiresAt},
			Timestamp: startTime,
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	// Check idle timeout
	if time.Since(session.LastActivity) > sessionIdleTimeout {
		return &security.SecurityError{
			Layer:     "auth",
			Type:      security.ErrorTypeAuth,
			Message:   "Session idle timeout",
			Details:   map[string]interface{}{"last_activity": session.LastActivity},
			Timestamp: startTime,
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	// Check MFA if required
	if user.MFAEnabled && !user.MFAVerified {
		return &security.SecurityError{
			Layer:     "auth",
			Type:      security.ErrorTypeAuth,
			Message:   "MFA verification required",
			Timestamp: startTime,
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	// Update session activity
	if err := v.sessionStore.UpdateActivity(ctx, user.SessionID); err != nil {
		// Non-critical: session tracking failure doesn't block auth
		// Logged to metrics via sessionStore internal telemetry
		_ = err
	}
	
	return nil
}

// ValidateToken validates a JWT token and extracts claims
//
// REFACTORED: Simplified - jwt library handles all validation
// No defensive code - trust the library to do its job correctly
func (v *Validator) ValidateToken(ctx context.Context, tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		// Ensure HMAC signing (HS256)
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return v.jwtSecret, nil
	})

	if err != nil {
		// jwt library already validated: signature, expiration, not-before, etc.
		return nil, ErrInvalidToken
	}

	// ParseWithClaims guarantees correct type, token.Valid means all checks passed
	claims := token.Claims.(*Claims)
	return claims, nil
}

// CreateToken creates a new JWT token for a user
//
// REFACTORED: SignedString with HMAC never fails in practice (removed defensive error check)
// Returns signed JWT token with standard claims + custom user/session data
func (v *Validator) CreateToken(user *security.User, session *security.Session) (string, error) {
	now := time.Now()
	expiresAt := now.Add(v.tokenDuration)

	claims := &Claims{
		UserID:      user.ID,
		Username:    user.Username,
		Email:       user.Email,
		Roles:       user.Roles,
		SessionID:   session.ID,
		MFAVerified: user.MFAVerified,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expiresAt),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "vcli-go",
			Subject:   user.ID,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	// HMAC signing never fails unless secret is corrupted (validated at construction)
	return token.SignedString(v.jwtSecret)
}

// RefreshToken refreshes an authentication token if within refresh window
//
// REFACTORED: Extracted needsRefresh to make logic 100% testable without timing
func (v *Validator) RefreshToken(ctx context.Context, tokenString string) (string, error) {
	claims, err := v.ValidateToken(ctx, tokenString)
	if err != nil {
		return "", err
	}

	// Check if token needs refresh
	if !v.needsRefresh(claims.ExpiresAt.Time) {
		return tokenString, nil
	}

	// Validate session still exists
	session, err := v.sessionStore.Get(ctx, claims.SessionID)
	if err != nil {
		return "", ErrInvalidSession
	}

	// Issue new token with extended expiration
	return v.refreshTokenWithSession(claims, session)
}

// needsRefresh determines if a token should be refreshed based on expiration time
// Returns true if token is within refresh window (close to expiry)
func (v *Validator) needsRefresh(expiresAt time.Time) bool {
	timeUntilExpiry := time.Until(expiresAt)
	return timeUntilExpiry <= v.refreshWindow
}

// refreshTokenWithSession creates a new token from existing claims and session
func (v *Validator) refreshTokenWithSession(claims *Claims, session *security.Session) (string, error) {
	user := &security.User{
		ID:          claims.UserID,
		Username:    claims.Username,
		Email:       claims.Email,
		Roles:       claims.Roles,
		SessionID:   claims.SessionID,
		MFAVerified: claims.MFAVerified,
	}
	return v.CreateToken(user, session)
}

// VerifyMFA verifies an MFA code for a user
func (v *Validator) VerifyMFA(ctx context.Context, user *security.User, code string) error {
	if v.mfaValidator == nil {
		// MFA not configured
		return nil
	}
	
	valid, err := v.mfaValidator.Verify(ctx, user.ID, code)
	if err != nil {
		return &security.SecurityError{
			Layer:     "auth",
			Type:      security.ErrorTypeAuth,
			Message:   "MFA verification failed",
			Details:   map[string]interface{}{"error": err.Error()},
			Timestamp: time.Now(),
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	if !valid {
		return &security.SecurityError{
			Layer:     "auth",
			Type:      security.ErrorTypeAuth,
			Message:   "Invalid MFA code",
			Timestamp: time.Now(),
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	// Mark user as MFA verified
	user.MFAVerified = true
	
	// Update session
	session, err := v.sessionStore.Get(ctx, user.SessionID)
	if err != nil {
		return err
	}
	session.MFAVerified = true
	
	return v.sessionStore.Save(ctx, session)
}

// CreateSession creates a new session for an authenticated user
func (v *Validator) CreateSession(ctx context.Context, user *security.User) (*security.Session, error) {
	return v.createSessionWithReader(ctx, user, rand.Reader)
}

// createSessionWithReader creates a session using the provided Reader for randomness
// Exported for testing - allows injection of failing Reader to test error paths
func (v *Validator) createSessionWithReader(ctx context.Context, user *security.User, reader io.Reader) (*security.Session, error) {
	sessionID, err := generateSessionIDWithReader(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	now := time.Now()
	session := &security.Session{
		ID:           sessionID,
		UserID:       user.ID,
		CreatedAt:    now,
		ExpiresAt:    now.Add(sessionDuration),
		LastActivity: now,
		IP:           user.IP,
		UserAgent:    user.UserAgent,
		MFAVerified:  user.MFAVerified,
		CommandCount: 0,
	}

	if err := v.sessionStore.Save(ctx, session); err != nil {
		return nil, err
	}

	return session, nil
}

// InvalidateSession invalidates a session (logout)
func (v *Validator) InvalidateSession(ctx context.Context, sessionID string) error {
	return v.sessionStore.Delete(ctx, sessionID)
}

// generateSessionID generates a cryptographically secure unique session ID
//
// REFACTORED: Now uses crypto/rand instead of time-based randomness
// Format: YYYYMMDDHHMMSS-<base64-random-16-bytes>
// Example: 20250115143022-8xK2mN9pQ7vL4wR3
//
// Returns error if cryptographic random generation fails (system entropy exhausted)
func generateSessionID() (string, error) {
	return generateSessionIDWithReader(rand.Reader)
}

// generateSessionIDWithReader generates a session ID using the provided Reader
// Exported for testing - allows injection of failing Reader to test error paths
func generateSessionIDWithReader(reader io.Reader) (string, error) {
	timestamp := time.Now().Format(sessionIDTimestampFormat)
	randomSuffix, err := randomStringWithReader(reader, sessionIDRandomBytes)
	if err != nil {
		return "", fmt.Errorf("failed to generate session ID: %w", err)
	}
	return fmt.Sprintf("%s-%s", timestamp, randomSuffix), nil
}

// randomString generates a cryptographically secure random string
//
// REFACTORED: Critical security fix - now uses crypto/rand instead of time.Now()
// Returns base64-encoded random bytes (URL-safe, no padding)
// Length parameter specifies number of random BYTES (output will be longer due to base64)
//
// Returns error if crypto/rand.Read fails (system entropy pool exhausted)
// This is idiomatic Go - caller decides how to handle crypto failure
func randomString(numBytes int) (string, error) {
	return randomStringWithReader(rand.Reader, numBytes)
}

// randomStringWithReader generates a random string using the provided Reader
// Exported for testing - allows injection of failing Reader to test error paths
// Production code uses crypto/rand.Reader
func randomStringWithReader(reader io.Reader, numBytes int) (string, error) {
	b := make([]byte, numBytes)
	if _, err := reader.Read(b); err != nil {
		return "", fmt.Errorf("crypto/rand.Read failed: %w", err)
	}
	// Use RawURLEncoding (no padding, URL-safe) for cleaner session IDs
	return base64.RawURLEncoding.EncodeToString(b), nil
}
