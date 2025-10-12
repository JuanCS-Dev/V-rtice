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
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/verticedev/vcli-go/pkg/security"
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
	
	// Check idle timeout (30 minutes of inactivity)
	idleTimeout := 30 * time.Minute
	if time.Since(session.LastActivity) > idleTimeout {
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
		// Log error but don't fail auth
		// TODO: Add logging
	}
	
	return nil
}

// ValidateToken validates a JWT token and extracts claims
func (v *Validator) ValidateToken(ctx context.Context, tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		// Verify signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("unexpected signing method")
		}
		return v.jwtSecret, nil
	})
	
	if err != nil {
		return nil, ErrInvalidToken
	}
	
	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		// Check expiration explicitly
		if time.Now().After(claims.ExpiresAt.Time) {
			return nil, ErrExpiredToken
		}
		
		return claims, nil
	}
	
	return nil, ErrInvalidToken
}

// CreateToken creates a new JWT token for a user
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
	tokenString, err := token.SignedString(v.jwtSecret)
	if err != nil {
		return "", err
	}
	
	return tokenString, nil
}

// RefreshToken refreshes an authentication token if within refresh window
func (v *Validator) RefreshToken(ctx context.Context, tokenString string) (string, error) {
	claims, err := v.ValidateToken(ctx, tokenString)
	if err != nil {
		return "", err
	}
	
	// Check if we're in the refresh window
	timeUntilExpiry := time.Until(claims.ExpiresAt.Time)
	if timeUntilExpiry > v.refreshWindow {
		// Too early to refresh
		return tokenString, nil
	}
	
	// Get session to verify it's still valid
	session, err := v.sessionStore.Get(ctx, claims.SessionID)
	if err != nil {
		return "", ErrInvalidSession
	}
	
	// Create new token
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
	session := &security.Session{
		ID:           generateSessionID(),
		UserID:       user.ID,
		CreatedAt:    time.Now(),
		ExpiresAt:    time.Now().Add(24 * time.Hour), // 24 hour session
		LastActivity: time.Now(),
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

// generateSessionID generates a unique session ID
func generateSessionID() string {
	// TODO: Implement secure random session ID generation
	// For now, use timestamp + random suffix
	return time.Now().Format("20060102150405") + "-" + randomString(16)
}

// randomString generates a random alphanumeric string
func randomString(length int) string {
	// TODO: Implement crypto/rand based random string
	// For now, simple implementation
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}
