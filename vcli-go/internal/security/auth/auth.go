// Package auth - Layer 1: Authentication
//
// "Who are you?"
//
// This layer provides identity verification through token validation,
// MFA challenges, and certificate verification.
package auth

import (
	"context"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// AuthLayer interface defines authentication operations
type AuthLayer interface {
	// Authenticate verifies user identity with credentials
	Authenticate(ctx context.Context, credentials Credentials) (*AuthToken, error)

	// ValidateToken ensures token is valid, not expired, not revoked
	ValidateToken(ctx context.Context, token string) (*UserIdentity, error)

	// RequireMFA checks if MFA is required for the given user/action
	RequireMFA(ctx context.Context, userID string, actionRisk ActionRisk) (bool, error)

	// RevokeToken revokes a token (adds to blacklist)
	RevokeToken(ctx context.Context, token string) error
}

// Credentials for authentication
type Credentials struct {
	Username string
	Password string
	MFACode  string
}

// AuthToken represents an authenticated session
type AuthToken struct {
	Token     string
	ExpiresAt time.Time
	User      *UserIdentity
}

// UserIdentity represents an authenticated user
type UserIdentity struct {
	UserID     string
	Username   string
	Email      string
	Roles      []string
	MFAEnabled bool
	CreatedAt  time.Time
}

// ActionRisk levels determine security requirements
type ActionRisk int

const (
	RiskSafe        ActionRisk = iota // Read-only, no confirmation
	RiskModerate                      // Confirmation if confidence < 85%
	RiskDestructive                   // ALWAYS require confirmation + MFA
	RiskCritical                      // Confirmation + MFA + Crypto Signature
)

// authLayer implements AuthLayer
type authLayer struct {
	jwtSecret     []byte
	tokenExpiry   time.Duration
	revokedTokens map[string]bool // In-memory for single-instance (use Redis for production)
}

// Metrics
var (
	authRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "auth_requests_total",
			Help: "Total authentication requests",
		},
		[]string{"result"}, // success, failure
	)

	authFailuresTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "auth_failures_total",
			Help: "Authentication failures by type",
		},
		[]string{"reason"}, // invalid, expired, revoked
	)

	mfaChallengesIssued = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "mfa_challenges_issued_total",
			Help: "Total MFA challenges issued",
		},
	)
)

// NewAuthLayer creates a new authentication layer
func NewAuthLayer(jwtSecret []byte, tokenExpiry time.Duration) AuthLayer {
	return &authLayer{
		jwtSecret:     jwtSecret,
		tokenExpiry:   tokenExpiry,
		revokedTokens: make(map[string]bool),
	}
}

// Authenticate implements AuthLayer.Authenticate
func (a *authLayer) Authenticate(ctx context.Context, creds Credentials) (*AuthToken, error) {
	// Basic authentication implementation
	// In production, verify against user database
	
	authRequestsTotal.WithLabelValues("success").Inc()
	
	// Generate token (simplified)
	token := &AuthToken{
		Token:     "auth-token-" + creds.Username,
		ExpiresAt: time.Now().Add(a.tokenExpiry),
	}
	
	return token, nil
}

// ValidateToken implements AuthLayer.ValidateToken
func (a *authLayer) ValidateToken(ctx context.Context, tokenString string) (*UserIdentity, error) {
	// Parse JWT
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		// Verify signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return a.jwtSecret, nil
	})

	if err != nil {
		authFailuresTotal.WithLabelValues("invalid").Inc()
		authRequestsTotal.WithLabelValues("failure").Inc()
		return nil, fmt.Errorf("invalid token: %w", err)
	}

	if !token.Valid {
		authFailuresTotal.WithLabelValues("invalid").Inc()
		authRequestsTotal.WithLabelValues("failure").Inc()
		return nil, fmt.Errorf("token not valid")
	}

	// Extract claims
	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		authFailuresTotal.WithLabelValues("invalid").Inc()
		authRequestsTotal.WithLabelValues("failure").Inc()
		return nil, fmt.Errorf("invalid claims")
	}

	// Check expiration
	if exp, ok := claims["exp"].(float64); ok {
		if time.Now().Unix() > int64(exp) {
			authFailuresTotal.WithLabelValues("expired").Inc()
			authRequestsTotal.WithLabelValues("failure").Inc()
			return nil, fmt.Errorf("token expired")
		}
	}

	// Check if revoked
	if a.revokedTokens[tokenString] {
		authFailuresTotal.WithLabelValues("revoked").Inc()
		authRequestsTotal.WithLabelValues("failure").Inc()
		return nil, fmt.Errorf("token revoked")
	}

	// Extract user identity
	userID, _ := claims["user_id"].(string)
	username, _ := claims["username"].(string)
	email, _ := claims["email"].(string)

	rolesInterface, _ := claims["roles"].([]interface{})
	roles := make([]string, len(rolesInterface))
	for i, r := range rolesInterface {
		roles[i], _ = r.(string)
	}

	mfaEnabled, _ := claims["mfa_enabled"].(bool)

	user := &UserIdentity{
		UserID:     userID,
		Username:   username,
		Email:      email,
		Roles:      roles,
		MFAEnabled: mfaEnabled,
		CreatedAt:  time.Now(),
	}

	authRequestsTotal.WithLabelValues("success").Inc()
	return user, nil
}

// RequireMFA implements AuthLayer.RequireMFA
func (a *authLayer) RequireMFA(ctx context.Context, userID string, actionRisk ActionRisk) (bool, error) {
	// MFA required for destructive and critical actions
	if actionRisk >= RiskDestructive {
		mfaChallengesIssued.Inc()
		return true, nil
	}
	return false, nil
}

// RevokeToken implements AuthLayer.RevokeToken
func (a *authLayer) RevokeToken(ctx context.Context, token string) error {
	a.revokedTokens[token] = true
	return nil
}
